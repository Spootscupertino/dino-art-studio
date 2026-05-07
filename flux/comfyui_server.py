#!/usr/bin/env python3
"""
ComfyUI headless server with Flux-dev backend and branded teal/blue UI.
Runs on M1 Mac, exposes REST API + WebSocket for live generation feedback.

Usage:
    python flux/comfyui_server.py --port 8888
    # Open http://localhost:8888 in browser
"""

import argparse
import asyncio
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from flux.generate_image import FluxGenerator, save_with_sidecar, inject_trex_signature

# ─────────────────────────────────────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(title="Dinosaur Flux Generator", description="Local Flux-dev server")

# CORS: with allow_origins=["*"] the spec forbids credentials, so keep it off.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = REPO_ROOT / "assets" / "gallery" / "flux"
LORA_DIR = REPO_ROOT / "flux" / "loras"

# Serve generated images as static files (absolute path)
ASSETS_DIR = REPO_ROOT / "assets"
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

# The Flux pipeline is a single shared object. Two concurrent .generate() calls
# would corrupt each other (LoRA swaps, RNG, MPS state). Serialize them.
generator = FluxGenerator()
_pipeline_lock = asyncio.Lock()

# ─────────────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────────────

MAX_PROMPT_LEN = 2000
DIM_MIN, DIM_MAX, DIM_STEP = 256, 2048, 8
STEPS_MIN, STEPS_MAX = 1, 150
GUIDANCE_MIN, GUIDANCE_MAX = 0.0, 20.0
LORA_NAME_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")


def _validate(
    prompt: str,
    height: int,
    width: int,
    steps: int,
    guidance: float,
    lora: Optional[str],
) -> None:
    if not prompt or not prompt.strip():
        raise HTTPException(status_code=400, detail="prompt must be non-empty")
    if len(prompt) > MAX_PROMPT_LEN:
        raise HTTPException(status_code=400, detail=f"prompt exceeds {MAX_PROMPT_LEN} chars")
    for name, val in (("height", height), ("width", width)):
        if not (DIM_MIN <= val <= DIM_MAX) or val % DIM_STEP != 0:
            raise HTTPException(
                status_code=400,
                detail=f"{name} must be in [{DIM_MIN},{DIM_MAX}] and a multiple of {DIM_STEP}",
            )
    if not (STEPS_MIN <= steps <= STEPS_MAX):
        raise HTTPException(status_code=400, detail=f"steps must be in [{STEPS_MIN},{STEPS_MAX}]")
    if not (GUIDANCE_MIN <= guidance <= GUIDANCE_MAX):
        raise HTTPException(
            status_code=400, detail=f"guidance must be in [{GUIDANCE_MIN},{GUIDANCE_MAX}]"
        )
    if lora is not None and not LORA_NAME_RE.match(lora):
        raise HTTPException(status_code=400, detail="lora name must match [A-Za-z0-9_-]{1,64}")


async def _run_generation(
    prompt: str,
    height: int,
    width: int,
    steps: int,
    guidance: float,
    seed: Optional[int],
    lora: Optional[str],
):
    """
    Run a generation under the singleton pipeline lock, off the event loop.
    Returns (image, output_path, params).
    """
    async with _pipeline_lock:
        loop = asyncio.get_running_loop()
        image = await loop.run_in_executor(
            None,
            lambda: generator.generate(
                prompt=prompt,
                height=height,
                width=width,
                num_inference_steps=steps,
                guidance_scale=guidance,
                seed=seed,
                lora=lora,
            ),
        )

    if image is None:
        return None, None, None

    output_path = OUTPUT_DIR / f"flux_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    params = {
        "height": height,
        "width": width,
        "steps": steps,
        "guidance": guidance,
        "seed": seed,
        "lora": lora,
    }
    save_with_sidecar(image, output_path, prompt, params)
    return image, output_path, params


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────


@app.get("/")
async def root():
    return HTMLResponse(get_branded_html())


@app.get("/api/generate")
@app.post("/api/generate")
async def generate_image(
    prompt: str,
    height: int = 1024,
    width: int = 1024,
    steps: int = 50,
    guidance: float = 3.5,
    seed: Optional[int] = None,
    lora: Optional[str] = None,
):
    final_prompt = inject_trex_signature(prompt)
    _validate(final_prompt, height, width, steps, guidance, lora)
    try:
        image, output_path, params = await _run_generation(
            final_prompt, height, width, steps, guidance, seed, lora
        )
        if image is None:
            raise HTTPException(status_code=500, detail="Generation failed")
        # Convert absolute path to URL path for browser
        relative_path = output_path.relative_to(REPO_ROOT)
        image_url = "/" + str(relative_path).replace("\\", "/")
        return {
            "success": True,
            "image_path": image_url,
            "prompt": prompt,
            "params": params,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/loras")
async def list_loras():
    if not LORA_DIR.exists():
        return {"loras": []}
    loras = [f.stem for f in LORA_DIR.glob("*.safetensors")]
    return {"loras": sorted(loras)}


@app.get("/api/models/flux")
async def get_flux_status():
    return {
        "model": "SDXL 1.0 (bfloat16, diffusers, M1-optimized)",
        "device": "mps",
        "dtype": "bfloat16",
        "loaded": generator.model_loaded,
    }


@app.websocket("/ws/generate")
async def websocket_generate(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            prompt = data.get("prompt") or ""
            height = int(data.get("height", 1024))
            width = int(data.get("width", 1024))
            steps = int(data.get("steps", 50))
            guidance = float(data.get("guidance", 3.5))
            seed = data.get("seed")
            lora = data.get("lora")

            try:
                _validate(prompt, height, width, steps, guidance, lora)
            except HTTPException as e:
                await websocket.send_json({"error": e.detail})
                continue

            await websocket.send_json({"status": "generating", "prompt": prompt})
            try:
                image, output_path, _ = await _run_generation(
                    prompt, height, width, steps, guidance, seed, lora
                )
            except Exception as e:
                await websocket.send_json({"status": "failed", "error": str(e)})
                continue

            if image is None:
                await websocket.send_json({"status": "failed", "error": "Generation failed"})
                continue

            await websocket.send_json(
                {
                    "status": "complete",
                    "image_path": str(output_path),
                    "prompt": prompt,
                }
            )
    except Exception as e:
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Branded UI
# ─────────────────────────────────────────────────────────────────────────────


def get_branded_html() -> str:
    """Return branded teal/blue ComfyUI-style interface."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dinosaur Flux Generator</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #0a1628 0%, #0f2843 100%);
                color: #e0e6ed;
                min-height: 100vh;
            }

            .container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 2rem;
            }

            header {
                text-align: center;
                margin-bottom: 3rem;
                border-bottom: 2px solid #00d4ff;
                padding-bottom: 2rem;
            }

            h1 {
                font-size: 2.5rem;
                background: linear-gradient(135deg, #00d4ff 0%, #00ffaa 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.5rem;
            }

            .subtitle {
                color: #00d4ff;
                font-size: 0.95rem;
                opacity: 0.8;
            }

            .grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 2rem;
                margin-bottom: 2rem;
            }

            .panel {
                background: rgba(15, 40, 67, 0.8);
                border: 1px solid #00d4ff;
                border-radius: 12px;
                padding: 2rem;
                backdrop-filter: blur(10px);
            }

            .panel h2 {
                color: #00d4ff;
                margin-bottom: 1.5rem;
                font-size: 1.3rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .form-group {
                margin-bottom: 1.5rem;
            }

            label {
                display: block;
                color: #00ffaa;
                font-size: 0.9rem;
                margin-bottom: 0.5rem;
                font-weight: 500;
            }

            input[type="text"],
            input[type="number"],
            select,
            textarea {
                width: 100%;
                padding: 0.75rem;
                background: rgba(0, 30, 60, 0.6);
                border: 1px solid #00d4ff;
                border-radius: 6px;
                color: #e0e6ed;
                font-family: inherit;
                font-size: 0.95rem;
            }

            input[type="text"]:focus,
            input[type="number"]:focus,
            select:focus,
            textarea:focus {
                outline: none;
                border-color: #00ffaa;
                box-shadow: 0 0 10px rgba(0, 255, 170, 0.3);
            }

            textarea {
                resize: vertical;
                min-height: 100px;
            }

            button {
                background: linear-gradient(135deg, #00d4ff 0%, #00ffaa 100%);
                color: #0a1628;
                border: none;
                padding: 0.75rem 2rem;
                border-radius: 6px;
                font-weight: 600;
                font-size: 0.95rem;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }

            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(0, 212, 255, 0.3);
            }

            button:active {
                transform: translateY(0);
            }

            .button-group {
                display: flex;
                gap: 1rem;
                margin-top: 2rem;
            }

            .button-group button {
                flex: 1;
            }

            .status {
                padding: 1rem;
                border-radius: 6px;
                margin-bottom: 1rem;
                display: none;
            }

            .status.active {
                display: block;
            }

            .status.generating {
                background: rgba(0, 212, 255, 0.1);
                border-left: 3px solid #00d4ff;
                color: #00d4ff;
            }

            .status.complete {
                background: rgba(0, 255, 170, 0.1);
                border-left: 3px solid #00ffaa;
                color: #00ffaa;
            }

            .status.error {
                background: rgba(255, 100, 100, 0.1);
                border-left: 3px solid #ff6464;
                color: #ff6464;
            }

            .gallery {
                background: rgba(15, 40, 67, 0.8);
                border: 1px solid #00d4ff;
                border-radius: 12px;
                padding: 2rem;
                backdrop-filter: blur(10px);
            }

            .gallery h2 {
                color: #00d4ff;
                margin-bottom: 1.5rem;
                font-size: 1.3rem;
            }

            .image-preview {
                max-width: 100%;
                border-radius: 8px;
                border: 1px solid #00ffaa;
                margin-bottom: 1rem;
            }

            .specs {
                font-size: 0.85rem;
                color: #00d4ff;
                opacity: 0.7;
                margin-bottom: 1rem;
            }

            .controls {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 1rem;
                margin-bottom: 1.5rem;
            }

            .control-item {
                display: flex;
                flex-direction: column;
            }

            .control-item label {
                font-size: 0.8rem;
                margin-bottom: 0.25rem;
            }

            .control-item input {
                padding: 0.5rem;
            }

            .loading {
                display: inline-block;
                width: 1rem;
                height: 1rem;
                border: 2px solid #00d4ff;
                border-top-color: transparent;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }

            @keyframes spin {
                to { transform: rotate(360deg); }
            }

            @media (max-width: 1024px) {
                .grid {
                    grid-template-columns: 1fr;
                }

                .controls {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🦖 Dinosaur Flux Generator</h1>
                <p class="subtitle">Local SDXL 1.0 on M1 (with LoRA fine-tuning coming Phase C)</p>
            </header>

            <div class="grid">
                <div class="panel">
                    <h2>⚙️ Generation</h2>

                    <div class="form-group">
                        <label>Prompt</label>
                        <textarea id="prompt" placeholder="a Tyrannosaurus rex in a river delta, photorealistic..."></textarea>
                    </div>

                    <div class="controls">
                        <div class="control-item">
                            <label>Height</label>
                            <input type="number" id="height" value="1024" min="512" max="2048" step="128">
                        </div>
                        <div class="control-item">
                            <label>Width</label>
                            <input type="number" id="width" value="1024" min="512" max="2048" step="128">
                        </div>
                        <div class="control-item">
                            <label>Steps</label>
                            <input type="number" id="steps" value="20" min="4" max="100">
                        </div>
                        <div class="control-item">
                            <label>Guidance</label>
                            <input type="number" id="guidance" value="3.5" min="1" max="10" step="0.5">
                        </div>
                    </div>

                    <div class="form-group">
                        <label>LoRA Model</label>
                        <select id="lora">
                            <option value="">None (base model)</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Seed (optional)</label>
                        <input type="number" id="seed" placeholder="Leave empty for random">
                    </div>

                    <div id="status" class="status"></div>

                    <div class="button-group">
                        <button onclick="generateImage()">
                            <span id="btn-text">Generate</span>
                        </button>
                    </div>
                </div>

                <div class="panel">
                    <h2>🎨 Preview</h2>
                    <div id="gallery" class="gallery">
                        <p style="color: #00d4ff; opacity: 0.6;">Generated images will appear here</p>
                    </div>
                </div>
            </div>
        </div>

        <script>
            async function generateImage() {
                const prompt = document.getElementById('prompt').value;
                if (!prompt) {
                    showStatus('Please enter a prompt', 'error');
                    return;
                }

                const params = new URLSearchParams();
                params.append('prompt', prompt);
                params.append('height', document.getElementById('height').value);
                params.append('width', document.getElementById('width').value);
                params.append('steps', document.getElementById('steps').value);
                params.append('guidance', document.getElementById('guidance').value);
                const seed = document.getElementById('seed').value;
                if (seed) params.append('seed', seed);
                const lora = document.getElementById('lora').value;
                if (lora) params.append('lora', lora);

                const btn = document.querySelector('button');
                btn.disabled = true;
                document.getElementById('btn-text').innerHTML = '<span class="loading"></span> Generating...';

                showStatus('Generating... (this may take 30-60 seconds)', 'generating');

                try {
                    const response = await fetch('/api/generate?' + params);
                    const data = await response.json();

                    if (!response.ok) {
                        // FastAPI returns detail as a string for HTTPException
                        // and as an array of {loc,msg,type} for 422 validation.
                        let msg = data.detail;
                        if (Array.isArray(msg)) {
                            msg = msg.map(e => {
                                const field = Array.isArray(e.loc) ? e.loc.slice(1).join('.') : '';
                                return field ? `${field}: ${e.msg}` : e.msg;
                            }).join('; ');
                        } else if (msg && typeof msg === 'object') {
                            msg = JSON.stringify(msg);
                        }
                        throw new Error(msg || `HTTP ${response.status}`);
                    }

                    showStatus('✓ Generation complete!', 'complete');
                    displayImage(data.image_path, data.prompt, data.params);
                } catch (error) {
                    showStatus('✗ ' + error.message, 'error');
                } finally {
                    btn.disabled = false;
                    document.getElementById('btn-text').innerHTML = 'Generate';
                }
            }

            function displayImage(path, prompt, params) {
                const gallery = document.getElementById('gallery');
                const html = `
                    <img src="${path}" class="image-preview" alt="Generated dinosaur">
                    <div class="specs">
                        <strong>${prompt.substring(0, 60)}...</strong><br>
                        ${params.height}×${params.width} | ${params.steps} steps | Guidance ${params.guidance}
                        ${params.lora ? '| LoRA: ' + params.lora : ''}
                    </div>
                `;
                gallery.innerHTML = html;
            }

            function showStatus(message, type) {
                const status = document.getElementById('status');
                status.textContent = message;
                status.className = 'status active ' + type;
            }

            window.addEventListener('DOMContentLoaded', async () => {
                try {
                    const response = await fetch('/api/models/loras');
                    const data = await response.json();
                    const select = document.getElementById('lora');
                    data.loras.forEach(lora => {
                        const option = document.createElement('option');
                        option.value = lora;
                        option.textContent = lora;
                        select.appendChild(option);
                    });
                } catch (e) {
                    console.error('Failed to load LoRAs:', e);
                }
            });

            document.getElementById('prompt').addEventListener('keydown', (e) => {
                if (e.metaKey && e.key === 'Enter') generateImage();
            });
        </script>
    </body>
    </html>
    """


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="ComfyUI-style server for Flux generation")
    parser.add_argument("--port", type=int, default=8888, help="Server port (default: 8888)")
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload on code changes"
    )

    args = parser.parse_args()

    print(f"\n{'═' * 60}")
    print(f"  🦖 Dinosaur Flux Generator Server")
    print(f"{'═' * 60}")
    print(f"  http://localhost:{args.port}")
    print(f"  Press Ctrl+C to stop\n")

    uvicorn.run(
        "flux.comfyui_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()

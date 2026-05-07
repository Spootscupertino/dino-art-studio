#!/usr/bin/env python3
"""
SDXL image generation for photorealistic dinosaur images on Apple Silicon.

Backend: diffusers StableDiffusionXLPipeline with bfloat16 on MPS and model_cpu_offload
for memory management. Runs on M1 / M2 / M3 (~7GB resident, ~2x faster than Flux-dev,
excellent quality for dinosaur anatomy feedback loop).

Usage:
    python flux/generate_image.py --prompt "a Tyrannosaurus in a river delta"
    python flux/generate_image.py --prompt "..." --seed 42
"""

import argparse
import json
import random
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

import PIL.Image
import torch

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
LORA_DIR = Path(__file__).parent / "loras"
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "gallery" / "flux"

MODEL_NAME = "SDXL 1.0 (bfloat16, diffusers, M1-optimized)"
DEVICE = "mps"
DTYPE = "bfloat16"

# ─────────────────────────────────────────────────────────────────────────────
# Color & formatting
# ─────────────────────────────────────────────────────────────────────────────


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    TEAL = "\033[96m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    WHITE = "\033[97m"

    @staticmethod
    def teal(s):
        return f"{C.TEAL}{s}{C.RESET}"

    @staticmethod
    def blue(s):
        return f"{C.BLUE}{s}{C.RESET}"

    @staticmethod
    def bold(s):
        return f"{C.BOLD}{s}{C.RESET}"

    @staticmethod
    def dim(s):
        return f"{C.DIM}{s}{C.RESET}"

    @staticmethod
    def green(s):
        return f"{C.GREEN}{s}{C.RESET}"

    @staticmethod
    def red(s):
        return f"{C.RED}{s}{C.RESET}"

    @staticmethod
    def yellow(s):
        return f"{C.YELLOW}{s}{C.RESET}"


# ─────────────────────────────────────────────────────────────────────────────
# T-rex signature
# ─────────────────────────────────────────────────────────────────────────────

_TREX_KEYWORDS = {"tyrannosaurus rex", "tyrannosaurus", "t-rex", "t rex"}

_TREX_SIGNATURE = (
    "prominent dark curved claws 4-5 inches sharp points rough keratin texture angled 45-60 degrees downward, "
    "massive jaw line with prominent conical honey-gold teeth 60+ visible tongue saliva strands breath mist, "
    "powerful foot impact on ground visible footprints heavy weight depression dominant predatory stance"
)


def inject_trex_signature(prompt: str) -> str:
    """Auto-append the T-rex triple threat (claws/mouth/feet) if prompt is a T-rex image."""
    if any(kw in prompt.lower() for kw in _TREX_KEYWORDS):
        return f"{prompt}, {_TREX_SIGNATURE}"
    return prompt


# ─────────────────────────────────────────────────────────────────────────────
# Sidecar saving
# ─────────────────────────────────────────────────────────────────────────────


def save_with_sidecar(
    image: PIL.Image.Image,
    output_path: Path,
    prompt: str,
    params: dict,
) -> Path:
    """
    Save image and a JSON sidecar with the same stem.

    The sidecar carries everything needed to rate, archive, or feed back into
    LoRA training: prompt, params (dims/steps/guidance/seed/lora), model id,
    timestamp. Without this, generated images are unattributable.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)

    sidecar_path = output_path.with_suffix(".json")
    sidecar = {
        "image": output_path.name,
        "prompt": prompt,
        "params": params,
        "model": MODEL_NAME,
        "device": DEVICE,
        "dtype": DTYPE,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    sidecar_path.write_text(json.dumps(sidecar, indent=2))
    return sidecar_path


# ─────────────────────────────────────────────────────────────────────────────
# Core generation
# ─────────────────────────────────────────────────────────────────────────────


class FluxGenerator:
    """
    Apple Silicon-native SDXL pipeline backed by diffusers.

    Public surface (called by flux/comfyui_server.py):
      - load_model()
      - generate(prompt, height, width, num_inference_steps, guidance_scale, seed, lora)
      - model_loaded (bool)
      - current_lora (Optional[str])
    """

    def __init__(self):
        self.pipe = None
        self.model_loaded = False
        self.current_lora: Optional[str] = None

    def load_model(self):
        """Load SDXL via diffusers with bfloat16 on MPS."""
        if self.model_loaded:
            return

        print(f"\n{C.teal('⏳ Loading SDXL model (bfloat16, diffusers)...')}")
        print(f"  {C.dim('(first load downloads weights; subsequent loads use cache)')}")

        try:
            from diffusers import StableDiffusionXLPipeline
        except ImportError as e:
            raise RuntimeError(
                "diffusers is not installed. Run: pip3 install diffusers torch\n"
                "(See flux/requirements.txt.)"
            ) from e

        try:
            # Load base model
            self.pipe = StableDiffusionXLPipeline.from_pretrained(
                MODEL_ID,
                torch_dtype=torch.bfloat16,
                use_safetensors=True,
                variant="fp16",
            )

            # Move to MPS and enable memory optimization
            self.pipe = self.pipe.to(DEVICE)
            self.pipe.enable_model_cpu_offload()

            self.model_loaded = True
            print(f"  {C.green('✓')} SDXL ready (bfloat16, MPS with cpu_offload)")
        except Exception as e:
            error_msg = str(e)
            print(f"  {C.red('✗')} Failed to load model: {e}")
            if "401" in error_msg or "GatedRepoError" in error_msg or "Access" in error_msg:
                print(f"\n  {C.yellow('⚠')} SDXL requires HuggingFace authentication:")
                print(f"    1. Get token: https://huggingface.co/settings/tokens")
                print(f"    2. Run: hf auth login")
                print(f"    3. Accept model: https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0")
                raise RuntimeError(
                    "SDXL access denied. Run `hf auth login` and accept the "
                    "model license at https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0"
                ) from e
            raise

    def _apply_lora(self, lora_name: Optional[str]) -> bool:
        """
        LoRA support is on the Phase C roadmap. For now: log and continue with the
        base model. Once Phase C ships, we'll call pipe.load_lora_weights() and cache.
        """
        if lora_name is None or lora_name == self.current_lora:
            return True

        lora_path = LORA_DIR / f"{lora_name}.safetensors"
        if not lora_path.exists():
            print(f"  {C.yellow('⚠')} LoRA not found: {lora_path}")
            return False

        print(f"  {C.yellow('⚠')} LoRA hot-swap not yet wired for SDXL backend; "
              f"running base model. (Phase C roadmap.)")
        return False

    def generate(
        self,
        prompt: str,
        height: int = 1024,
        width: int = 1024,
        num_inference_steps: int = 20,
        guidance_scale: float = 3.5,
        seed: Optional[int] = None,
        lora: Optional[str] = None,
    ) -> Optional[PIL.Image.Image]:
        """Generate a single image."""
        if not self.pipe:
            self.load_model()

        self._apply_lora(lora)

        if seed is None:
            seed = random.randint(0, 2**31 - 1)

        print(f"\n{C.blue('═' * 60)}")
        print(f"  {C.bold('GENERATING')} {C.teal(f'{width}×{height}')}")
        print(f"{C.blue('═' * 60)}")
        print(f"  {C.dim('Prompt:')} {prompt[:70]}{'...' if len(prompt) > 70 else ''}")
        print(f"  {C.dim('Steps:')} {num_inference_steps}  "
              f"{C.dim('Guidance:')} {guidance_scale}  "
              f"{C.dim('Seed:')} {seed}")

        try:
            generator = torch.Generator(device=DEVICE).manual_seed(seed)

            result = self.pipe(
                prompt=prompt,
                height=height,
                width=width,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator,
            )

            # diffusers returns an object with .images[0]
            pil_image = result.images[0] if hasattr(result, 'images') else result

            print(f"\n  {C.green('✓')} Generated successfully")
            return pil_image

        except Exception as e:
            print(f"  {C.red('✗')} Generation failed: {e}")
            return None


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Generate photorealistic dinosaur images with SDXL (bfloat16, diffusers)"
    )
    parser.add_argument("--prompt", type=str, required=True)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--guidance", type=float, default=3.5)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--lora", type=str, default=None)
    parser.add_argument("--output", type=Path, default=None)

    args = parser.parse_args()

    gen = FluxGenerator()

    final_prompt = inject_trex_signature(args.prompt)
    if final_prompt != args.prompt:
        print(f"  {C.teal('🦖 T-rex signature injected')}")

    try:
        image = gen.generate(
            prompt=final_prompt,
            height=args.height,
            width=args.width,
            num_inference_steps=args.steps,
            guidance_scale=args.guidance,
            seed=args.seed,
            lora=args.lora,
        )
    except RuntimeError as e:
        print(f"\n  {C.red('✗')} {e}\n")
        sys.exit(1)

    if image is None:
        sys.exit(1)

    output_path = args.output or (
        OUTPUT_DIR / f"flux_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )

    params = {
        "height": args.height,
        "width": args.width,
        "steps": args.steps,
        "guidance": args.guidance,
        "seed": args.seed,
        "lora": args.lora,
    }
    if final_prompt != args.prompt:
        params["base_prompt"] = args.prompt
        params["trex_signature"] = True
    sidecar_path = save_with_sidecar(image, output_path, final_prompt, params)

    print(f"\n  {C.green('✓')} Saved to: {C.teal(str(output_path))}")
    print(f"  {C.green('✓')} Sidecar:  {C.teal(str(sidecar_path))}\n")


if __name__ == "__main__":
    main()

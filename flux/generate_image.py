#!/usr/bin/env python3
"""
Flux-dev image generation for photorealistic dinosaur images on Apple Silicon.

Backend: mflux (https://github.com/filipstrand/mflux). Uses Apple's MLX
framework with 4-bit quantization so Flux-dev fits comfortably on a 24GB
M1 / M2 / M3 (~6GB resident vs ~22GB for the diffusers/MPS path).

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

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

FLUX_ALIAS = "dev"          # "dev" (slower, higher quality) or "schnell" (4 steps)
QUANTIZE_BITS = 4           # 4 or 8. 4-bit is the right default for 24GB unified memory.
LORA_DIR = Path(__file__).parent / "loras"
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "gallery" / "flux"

MODEL_NAME = f"FLUX.1-{FLUX_ALIAS} ({QUANTIZE_BITS}-bit, mflux/MLX)"
DEVICE = "mps"              # mflux uses MLX which targets MPS; surfaced for sidecar metadata.
DTYPE = "bfloat16"          # Same; surfaced for sidecar metadata only.

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
        "quantize_bits": QUANTIZE_BITS,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    sidecar_path.write_text(json.dumps(sidecar, indent=2))
    return sidecar_path


# ─────────────────────────────────────────────────────────────────────────────
# Core generation
# ─────────────────────────────────────────────────────────────────────────────


class FluxGenerator:
    """
    Apple Silicon-native Flux pipeline backed by mflux.

    Public surface (called by flux/comfyui_server.py):
      - load_model()
      - generate(prompt, height, width, num_inference_steps, guidance_scale, seed, lora)
      - model_loaded (bool)
      - current_lora (Optional[str])
    """

    def __init__(self):
        self.flux = None
        self.model_loaded = False
        self.current_lora: Optional[str] = None

    def load_model(self):
        """Load Flux-dev (4-bit) via mflux."""
        if self.model_loaded:
            return

        print(f"\n{C.teal('⏳ Loading Flux-dev model (4-bit, mflux)...')}")
        print(f"  {C.dim('(first load downloads weights; subsequent loads use cache)')}")

        try:
            from mflux import Flux1
        except ImportError as e:
            raise RuntimeError(
                "mflux is not installed. Run: pip3 install mflux\n"
                "(See flux/requirements.txt.)"
            ) from e

        try:
            self.flux = Flux1.from_alias(
                alias=FLUX_ALIAS,
                quantize=QUANTIZE_BITS,
            )
            self.model_loaded = True
            print(f"  {C.green('✓')} Flux-{FLUX_ALIAS} ready ({QUANTIZE_BITS}-bit, MLX)")
        except Exception as e:
            error_msg = str(e)
            print(f"  {C.red('✗')} Failed to load model: {e}")
            if "401" in error_msg or "GatedRepoError" in error_msg or "Access" in error_msg:
                print(f"\n  {C.yellow('⚠')} FLUX.1-dev requires HuggingFace authentication:")
                print(f"    1. Get token: https://huggingface.co/settings/tokens")
                print(f"    2. Run: hf auth login")
                print(f"    3. Accept model: https://huggingface.co/black-forest-labs/FLUX.1-dev")
                raise RuntimeError(
                    "FLUX.1-dev access denied. Run `hf auth login` and accept the "
                    "model license at https://huggingface.co/black-forest-labs/FLUX.1-dev"
                ) from e
            raise

    def _apply_lora(self, lora_name: Optional[str]) -> bool:
        """
        LoRA support is on the Phase C roadmap. mflux exposes LoRAs via a
        different API (constructor arg, not runtime swap), so we cannot
        switch them on a live instance. For now: log and continue with the
        base model. Once Phase C ships, we'll instantiate Flux1 per-LoRA
        and cache by name.
        """
        if lora_name is None or lora_name == self.current_lora:
            return True

        lora_path = LORA_DIR / f"{lora_name}.safetensors"
        if not lora_path.exists():
            print(f"  {C.yellow('⚠')} LoRA not found: {lora_path}")
            return False

        print(f"  {C.yellow('⚠')} LoRA hot-swap not yet wired for mflux backend; "
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
        if not self.flux:
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
            from mflux import Config
            config = Config(
                num_inference_steps=num_inference_steps,
                height=height,
                width=width,
                guidance=guidance_scale,
            )
            result = self.flux.generate_image(
                seed=seed,
                prompt=prompt,
                config=config,
            )

            # mflux returns a GeneratedImage wrapper around a PIL.Image.
            pil_image = getattr(result, "image", result)
            if not isinstance(pil_image, PIL.Image.Image):
                # Some mflux versions expose .pil_image instead.
                pil_image = getattr(result, "pil_image", None) or pil_image

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
        description="Generate photorealistic dinosaur images with Flux-dev (4-bit, mflux)"
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

    try:
        image = gen.generate(
            prompt=args.prompt,
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
    sidecar_path = save_with_sidecar(image, output_path, args.prompt, params)

    print(f"\n  {C.green('✓')} Saved to: {C.teal(str(output_path))}")
    print(f"  {C.green('✓')} Sidecar:  {C.teal(str(sidecar_path))}\n")


if __name__ == "__main__":
    main()

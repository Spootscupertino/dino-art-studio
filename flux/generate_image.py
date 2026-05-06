#!/usr/bin/env python3
"""
Flux-dev image generation for photorealistic dinosaur images.
M1 Mac optimized. Supports LoRA fine-tuning.

Usage:
    python flux/generate_image.py --prompt "a Tyrannosaurus in a river delta"
    python flux/generate_image.py --prompt "..." --lora dino_winners --seed 42
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Flux-dev needs ~22GB; default MPS cap is ~20GB on a 24GB Mac.
# Disable the upper limit so allocations spill to system RAM/swap instead
# of OOMing. Must be set before importing torch.
os.environ.setdefault("PYTORCH_MPS_HIGH_WATERMARK_RATIO", "0.0")

import torch
from diffusers import FluxPipeline
import PIL.Image

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

FLUX_MODEL = "black-forest-labs/FLUX.1-dev"
LORA_DIR = Path(__file__).parent / "loras"
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "gallery" / "flux"

DTYPE = torch.bfloat16
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

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
        "model": FLUX_MODEL,
        "device": DEVICE,
        "dtype": str(DTYPE).replace("torch.", ""),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    sidecar_path.write_text(json.dumps(sidecar, indent=2))
    return sidecar_path


# ─────────────────────────────────────────────────────────────────────────────
# Core generation
# ─────────────────────────────────────────────────────────────────────────────


class FluxGenerator:
    """M1-optimized Flux-dev pipeline with LoRA support."""

    def __init__(self):
        self.pipe = None
        self.model_loaded = False
        self.current_lora: Optional[str] = None

    def load_model(self):
        """Load Flux-dev model with M1 optimizations."""
        if self.model_loaded:
            return

        print(f"\n{C.teal('⏳ Loading Flux-dev model...')}")
        print(f"  {C.dim('(first load may take 1-2 min, then cached)')}")

        try:
            self.pipe = FluxPipeline.from_pretrained(
                FLUX_MODEL,
                torch_dtype=DTYPE,
                local_files_only=False,
            )

            self.pipe = self.pipe.to(DEVICE)

            if hasattr(self.pipe, "enable_attention_slicing"):
                self.pipe.enable_attention_slicing("auto")
            if hasattr(self.pipe, "enable_xformers_memory_efficient_attention"):
                try:
                    self.pipe.enable_xformers_memory_efficient_attention()
                except Exception:
                    pass

            self.model_loaded = True
            print(f"  {C.green('✓')} Flux-dev ready")
            self._print_memory_usage()

        except Exception as e:
            error_msg = str(e)
            print(f"  {C.red('✗')} Failed to load model: {e}")
            if "401" in error_msg or "GatedRepoError" in error_msg or "Access to model" in error_msg:
                print(f"\n  {C.yellow('⚠')} FLUX.1-dev requires HuggingFace authentication:")
                print(f"    1. Get token: https://huggingface.co/settings/tokens")
                print(f"    2. Run: hf auth login")
                print(f"    3. Accept model: https://huggingface.co/black-forest-labs/FLUX.1-dev")
                raise RuntimeError(
                    "FLUX.1-dev access denied. Run `hf auth login` and accept the "
                    "model license at https://huggingface.co/black-forest-labs/FLUX.1-dev"
                ) from e
            if "out of memory" in error_msg.lower() or "MPS" in error_msg:
                raise RuntimeError(
                    f"MPS out of memory loading Flux-dev. Try: "
                    f"export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 before starting the server. "
                    f"Original: {error_msg}"
                ) from e
            raise

    def _apply_lora(self, lora_name: Optional[str]) -> bool:
        """
        Swap the active LoRA. Repeated calls used to fuse_lora() additively,
        compounding weights across requests. We unload everything and then
        load the requested LoRA fresh, tracking the current name so a no-op
        request stays a no-op.
        """
        if lora_name == self.current_lora:
            return True

        # Unload anything currently attached.
        if self.current_lora is not None:
            try:
                self.pipe.unload_lora_weights()
            except Exception as e:
                print(f"  {C.yellow('⚠')} Failed to unload prior LoRA: {e}")
            self.current_lora = None

        if lora_name is None:
            return True

        lora_path = LORA_DIR / f"{lora_name}.safetensors"
        if not lora_path.exists():
            print(f"  {C.yellow('⚠')} LoRA not found: {lora_path}")
            return False

        try:
            print(f"  {C.dim('Loading LoRA')}: {lora_name}")
            self.pipe.load_lora_weights(str(lora_path), adapter_name=lora_name)
            if hasattr(self.pipe, "set_adapters"):
                self.pipe.set_adapters([lora_name], adapter_weights=[1.0])
            self.current_lora = lora_name
            print(f"  {C.green('✓')} LoRA active: {lora_name}")
            return True
        except Exception as e:
            print(f"  {C.yellow('⚠')} Failed to load LoRA: {e}")
            return False

    def generate(
        self,
        prompt: str,
        height: int = 1024,
        width: int = 1024,
        num_inference_steps: int = 50,
        guidance_scale: float = 3.5,
        seed: Optional[int] = None,
        lora: Optional[str] = None,
    ) -> Optional[PIL.Image.Image]:
        """Generate a single image."""
        if not self.pipe:
            self.load_model()

        self._apply_lora(lora)

        if seed is not None:
            generator = torch.Generator(device=DEVICE).manual_seed(seed)
        else:
            generator = None

        print(f"\n{C.blue('═' * 60)}")
        print(f"  {C.bold('GENERATING')} {C.teal(f'{width}×{height}')}")
        print(f"{C.blue('═' * 60)}")
        print(f"  {C.dim('Prompt:')} {prompt[:70]}{'...' if len(prompt) > 70 else ''}")
        if lora:
            print(f"  {C.dim('LoRA:')} {lora}")
        print(f"  {C.dim('Steps:')} {num_inference_steps}  {C.dim('Guidance:')} {guidance_scale}")

        try:
            with torch.no_grad():
                image = self.pipe(
                    prompt=prompt,
                    height=height,
                    width=width,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    generator=generator,
                ).images[0]

            print(f"\n  {C.green('✓')} Generated successfully")
            self._print_memory_usage()
            return image

        except Exception as e:
            print(f"  {C.red('✗')} Generation failed: {e}")
            return None

    def _print_memory_usage(self):
        if torch.backends.mps.is_available():
            allocated = torch.mps.current_allocated_memory() / 1e9
            reserved = torch.mps.driver_allocated_memory() / 1e9
            print(f"  {C.dim(f'Memory: {allocated:.1f}GB allocated, {reserved:.1f}GB reserved')}")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Generate photorealistic dinosaur images with Flux-dev + LoRA"
    )
    parser.add_argument("--prompt", type=str, required=True)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--steps", type=int, default=50)
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

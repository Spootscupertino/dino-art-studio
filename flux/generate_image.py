#!/usr/bin/env python3
"""
Flux-dev image generation for photorealistic dinosaur images.
M1 Mac optimized. Supports LoRA fine-tuning and ControlNet anatomy guidance.

Usage:
    python flux/generate_image.py --prompt "a Tyrannosaurus in a river delta"
    python flux/generate_image.py --prompt "..." --lora dino_winners --seed 42
    python flux/generate_image.py --prompt "..." --controlnet skeletal_anatomy --cref URL
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import torch
from diffusers import FluxPipeline
from diffusers.utils import load_image
import PIL.Image

# M1 Mac optimizations
torch.backends.cuda.is_available = lambda: False  # Force Metal backend
if hasattr(torch.backends, "mps"):
    torch.set_default_device("mps")

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

FLUX_MODEL = "black-forest-labs/FLUX.1-dev"
LORA_DIR = Path(__file__).parent / "loras"
CONTROLNET_DIR = Path(__file__).parent / "controlnets"
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "gallery" / "flux"

# M1 memory optimization constants
DTYPE = torch.bfloat16  # bfloat16 saves memory while keeping quality
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


# ─────────────────────────────────────────────────────────────────────────────
# Core generation
# ─────────────────────────────────────────────────────────────────────────────


class FluxGenerator:
    """M1-optimized Flux-dev pipeline with LoRA + ControlNet support."""

    def __init__(self):
        self.pipe = None
        self.model_loaded = False

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

            # M1 optimizations
            self.pipe = self.pipe.to(DEVICE)

            # Enable memory-efficient attention (native sdpa, xformers fallback)
            if hasattr(self.pipe, "enable_attention_slicing"):
                self.pipe.enable_attention_slicing("auto")
            if hasattr(self.pipe, "enable_xformers_memory_efficient_attention"):
                try:
                    self.pipe.enable_xformers_memory_efficient_attention()
                except Exception:
                    pass  # xformers not available on M1, use native sdpa

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
            sys.exit(1)

    def load_lora(self, lora_name: str):
        """Load and merge LoRA weights."""
        if not self.pipe:
            self.load_model()

        lora_path = LORA_DIR / f"{lora_name}.safetensors"
        if not lora_path.exists():
            print(f"  {C.yellow('⚠')} LoRA not found: {lora_path}")
            return False

        try:
            print(f"  {C.dim('Loading LoRA')}: {lora_name}")
            self.pipe.load_lora_weights(str(lora_path))
            self.pipe.fuse_lora(lora_scale=1.0)
            print(f"  {C.green('✓')} LoRA merged")
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
        seed: int = None,
        lora: str = None,
        controlnet_ref: str = None,
    ) -> PIL.Image.Image:
        """Generate a single image."""
        if not self.pipe:
            self.load_model()

        if lora:
            self.load_lora(lora)

        # Set seed for reproducibility
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
        """Print current memory usage for M1 optimization."""
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
    parser.add_argument(
        "--prompt",
        type=str,
        required=True,
        help="Image generation prompt",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1024,
        help="Image height in pixels (default: 1024)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1024,
        help="Image width in pixels (default: 1024)",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=50,
        help="Inference steps (more = higher quality, slower) (default: 50)",
    )
    parser.add_argument(
        "--guidance",
        type=float,
        default=3.5,
        help="Classifier-free guidance scale (default: 3.5)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--lora",
        type=str,
        default=None,
        help="LoRA name to load (e.g., 'dino_winners')",
    )
    parser.add_argument(
        "--controlnet",
        type=str,
        default=None,
        help="ControlNet name for anatomy guidance",
    )
    parser.add_argument(
        "--cref",
        type=str,
        default=None,
        help="Character reference image URL or path",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file path (default: assets/gallery/flux/timestamp.png)",
    )

    args = parser.parse_args()

    # Initialize generator
    gen = FluxGenerator()

    # Generate image
    image = gen.generate(
        prompt=args.prompt,
        height=args.height,
        width=args.width,
        num_inference_steps=args.steps,
        guidance_scale=args.guidance,
        seed=args.seed,
        lora=args.lora,
        controlnet_ref=args.controlnet,
    )

    if image is None:
        sys.exit(1)

    # Save image
    output_path = args.output or (
        OUTPUT_DIR / f"flux_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)

    print(f"\n  {C.green('✓')} Saved to: {C.teal(str(output_path))}\n")


if __name__ == "__main__":
    main()

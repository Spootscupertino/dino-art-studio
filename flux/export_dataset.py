#!/usr/bin/env python3
"""
export_dataset.py — prepare a LoRA training dataset from reference images.

This script reads all images + captions from assets/gallery/flux/training_refs/
and exports them in a format that ai-toolkit expects. It filters for reference
images (source_type="reference" in winners.json) and generates dataset metadata.

Usage:
    python3 flux/export_dataset.py
    python3 flux/export_dataset.py --output flux/datasets/dino_refs

Output:
    flux/datasets/dino_refs/
      ├── dataset.json          (metadata: image paths, captions, species)
      ├── images/               (symlinks to actual training_refs)
      │   ├── trex_20260505_...png
      │   ├── trex_20260505_...txt
      │   └── ...
      └── summary.txt           (human-readable counts and species breakdown)

The images/ folder uses symlinks so you don't duplicate storage. You can point
ai-toolkit directly at flux/datasets/dino_refs/images/ for training.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
TRAINING_DIR = REPO_ROOT / "assets" / "gallery" / "flux" / "training_refs"
WINNERS_FILE = REPO_ROOT / "winners.json"


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    TEAL = "\033[96m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"

    @staticmethod
    def teal(s: str) -> str:
        return f"{C.TEAL}{s}{C.RESET}"

    @staticmethod
    def blue(s: str) -> str:
        return f"{C.BLUE}{s}{C.RESET}"

    @staticmethod
    def dim(s: str) -> str:
        return f"{C.DIM}{s}{C.RESET}"

    @staticmethod
    def bold(s: str) -> str:
        return f"{C.BOLD}{s}{C.RESET}"

    @staticmethod
    def green(s: str) -> str:
        return f"{C.GREEN}{s}{C.RESET}"

    @staticmethod
    def yellow(s: str) -> str:
        return f"{C.YELLOW}{s}{C.RESET}"

    @staticmethod
    def red(s: str) -> str:
        return f"{C.RED}{s}{C.RESET}"


def banner(title: str) -> None:
    bar = "═" * 62
    print(f"\n{C.teal(bar)}")
    print(f"  {C.bold(C.teal(title))}")
    print(f"{C.teal(bar)}\n")


def get_reference_images() -> dict[str, dict]:
    """
    Read all training_refs images with their captions and metadata from winners.json.
    Returns: {image_stem: {image_path, caption_path, caption_text, species, ...}}
    """
    images = {}

    if not TRAINING_DIR.exists():
        print(f"  {C.yellow('⚠')} {TRAINING_DIR} does not exist yet")
        return images

    # Load winners.json to get metadata
    reference_entries = {}
    if WINNERS_FILE.exists():
        with open(WINNERS_FILE) as f:
            winners = json.load(f)
        for species, entries in winners.items():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                if entry.get("source_type") == "reference":
                    img_path = entry.get("image_path")
                    if img_path:
                        reference_entries[img_path] = {
                            "species": species,
                            "entry": entry,
                        }

    # Scan training_refs recursively for image files (subdirs are species/source_type/)
    for image_file in TRAINING_DIR.rglob("*"):
        if image_file.is_file() and image_file.suffix.lower() in (
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
        ):
            caption_file = image_file.with_suffix(".txt")
            if not caption_file.exists():
                print(
                    f"  {C.yellow('⚠')} Missing caption for {image_file.name} "
                    f"(expected {caption_file.name})"
                )
                continue

            with open(caption_file) as f:
                caption_text = f.read().strip()

            # Look up metadata from winners.json
            rel_path = str(image_file.relative_to(REPO_ROOT))
            metadata = reference_entries.get(rel_path, {})
            # Prefer the path-derived species (training_refs/<species>/<source_type>/image)
            # over winners.json so newly-ingested files don't get "Unknown".
            try:
                parts = image_file.relative_to(TRAINING_DIR).parts
                species = parts[0] if len(parts) >= 2 else metadata.get("species", "Unknown")
            except ValueError:
                species = metadata.get("species", "Unknown")

            # Skip refs whose sidecar is quarantined.
            sidecar_json = image_file.with_suffix(".json")
            if sidecar_json.exists():
                try:
                    meta = json.loads(sidecar_json.read_text())
                    if meta.get("quarantined"):
                        print(f"  {C.yellow('⊘')} {image_file.name} quarantined, skipping")
                        continue
                except Exception:
                    pass

            stem = image_file.stem
            images[stem] = {
                "image_path": image_file,
                "caption_path": caption_file,
                "caption_text": caption_text,
                "species": species,
                "metadata": metadata.get("entry", {}),
            }
            print(f"  {C.green('✓')} {image_file.name}")

    return images


def export_dataset(images: dict[str, dict], output_dir: Path) -> bool:
    """Export images and captions to output_dir in ai-toolkit format."""
    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Create symlinks in images/ directory (don't duplicate storage)
    dataset_entries = []
    for stem, img_meta in images.items():
        image_path = img_meta["image_path"]
        caption_path = img_meta["caption_path"]
        species = img_meta["species"]
        caption_text = img_meta["caption_text"]

        # Symlink the image and caption into images/
        link_image = images_dir / image_path.name
        link_caption = images_dir / caption_path.name

        # Remove old links if they exist
        if link_image.is_symlink() or link_image.exists():
            link_image.unlink()
        if link_caption.is_symlink() or link_caption.exists():
            link_caption.unlink()

        # Create symlinks with relative path from symlink to target
        # Compute relative path from the images/ folder back to the original location
        rel_image_path = Path("../..") / image_path.relative_to(REPO_ROOT)
        rel_caption_path = Path("../..") / caption_path.relative_to(REPO_ROOT)
        link_image.symlink_to(rel_image_path)
        link_caption.symlink_to(rel_caption_path)

        dataset_entries.append(
            {
                "filename": image_path.name,
                "caption": caption_text,
                "species": species,
            }
        )

    # Write dataset.json
    dataset_json = {
        "images": dataset_entries,
        "metadata": {
            "created": datetime.now().isoformat(),
            "total_images": len(dataset_entries),
            "species_count": len(set(e["species"] for e in dataset_entries)),
            "purpose": "LoRA fine-tuning for Flux-dev dinosaur generation",
        },
    }
    with open(output_dir / "dataset.json", "w") as f:
        json.dump(dataset_json, f, indent=2)

    # Write summary.txt
    species_counts = {}
    for entry in dataset_entries:
        species = entry["species"]
        species_counts[species] = species_counts.get(species, 0) + 1

    summary_lines = [
        "LORA Training Dataset Summary",
        "=" * 50,
        f"\nTotal images: {len(dataset_entries)}",
        f"Unique species: {len(species_counts)}",
        "\nBreakdown by species:",
    ]
    for species in sorted(species_counts.keys()):
        count = species_counts[species]
        summary_lines.append(f"  {species}: {count} image(s)")

    summary_lines.extend(
        [
            "\nDataset ready for ai-toolkit training:",
            f"  → Images (with captions): {images_dir.relative_to(REPO_ROOT)}",
            f"  → Metadata: {(output_dir / 'dataset.json').relative_to(REPO_ROOT)}",
            "\nNext steps:",
            "  1. Install ai-toolkit (https://github.com/ostris/ai-toolkit)",
            "  2. Point ai-toolkit at the images/ folder for training",
            "  3. Save output LoRA to flux/loras/",
        ]
    )

    with open(output_dir / "summary.txt", "w") as f:
        f.write("\n".join(summary_lines))

    # Also produce a zip of (image, caption) pairs for Replicate's trainer.
    # The trainer expects a flat zip with files side-by-side, no subdirs.
    zip_path = output_dir.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for stem, img_meta in images.items():
            image_path = img_meta["image_path"]
            caption_path = img_meta["caption_path"]
            zf.write(image_path, arcname=image_path.name)
            zf.write(caption_path, arcname=caption_path.name)
    print(f"  {C.green('✓')} wrote zip: {zip_path.relative_to(REPO_ROOT)}")

    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=str,
        default="flux/datasets/dino_refs",
        help="Output directory for dataset (default: flux/datasets/dino_refs)",
    )
    args = parser.parse_args()

    output_dir = REPO_ROOT / args.output

    banner("LORA DATASET EXPORT")

    print(f"  {C.dim('Reading training_refs...')}\n")
    images = get_reference_images()

    if not images:
        print(f"\n  {C.red('✗')} No reference images found in {TRAINING_DIR}")
        print(f"  Run {C.teal('python3 reference.py')} to add images first.\n")
        sys.exit(1)

    print(f"\n  {C.dim('Exporting to ' + C.teal(str(output_dir.relative_to(REPO_ROOT))) + '...')}\n")
    if export_dataset(images, output_dir):
        print(f"\n  {C.green('✓')} Dataset exported successfully\n")

        # Print summary
        summary_path = output_dir / "summary.txt"
        if summary_path.exists():
            with open(summary_path) as f:
                summary = f.read()
            print("  " + "\n  ".join(summary.split("\n")))
            print()
    else:
        print(f"\n  {C.red('✗')} Export failed\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

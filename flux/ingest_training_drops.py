#!/usr/bin/env python3
"""Ingest LoRA training reference images from Desktop drop folders.

Walks ~/Desktop/Jurassinkart/Training Drops/<species>/<source_type>/ and for
each image:
  1. Moves it into assets/gallery/flux/training_refs/<species>/<source_type>/
  2. Writes a .json sidecar (species, source_type, ingested_at, source_url stub)
  3. Writes a .txt caption stub for manual editing

Manual-run only by design — auto-watching this folder is the same trap the
.approved publish gate was added to prevent. Drop a batch, eyeball, run.

Usage:
    python3 flux/ingest_training_drops.py
    python3 flux/ingest_training_drops.py --add-species velociraptor
    python3 flux/ingest_training_drops.py --dry-run

Source types (folder names) are fixed:
    skeletal       Museum mounts, technical diagrams
    paleoart       Scientifically-grounded illustrations
    living_analog  Modern bird/reptile photos for soft-tissue cues
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DROP_ROOT = Path.home() / "Desktop" / "Jurassinkart" / "Training Drops"
DEST_ROOT = REPO_ROOT / "assets" / "gallery" / "flux" / "training_refs"

SOURCE_TYPES = ("skeletal", "paleoart", "living_analog")
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

# Licenses allowed for commercial LoRA training.
# NC (Non-Commercial) and ND (No Derivatives) are banned.
ALLOWED_LICENSES = {
    "CC0",
    "CC BY",      "CC BY 2.0",  "CC BY 3.0",  "CC BY 4.0",
    "CC BY-SA",   "CC BY-SA 2.0", "CC BY-SA 3.0", "CC BY-SA 4.0",
    "Public Domain",
}
BANNED_LICENSE_KEYWORDS = ("NC", "ND")

LICENSE_URLS = {
    "CC0":          "https://creativecommons.org/publicdomain/zero/1.0/",
    "CC BY 4.0":    "https://creativecommons.org/licenses/by/4.0/",
    "CC BY 3.0":    "https://creativecommons.org/licenses/by/3.0/",
    "CC BY 2.0":    "https://creativecommons.org/licenses/by/2.0/",
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/",
    "CC BY-SA 2.0": "https://creativecommons.org/licenses/by-sa/2.0/",
}


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    TEAL = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"

    @classmethod
    def teal(cls, s): return f"{cls.TEAL}{s}{cls.RESET}"
    @classmethod
    def green(cls, s): return f"{cls.GREEN}{s}{cls.RESET}"
    @classmethod
    def yellow(cls, s): return f"{cls.YELLOW}{s}{cls.RESET}"
    @classmethod
    def red(cls, s): return f"{cls.RED}{s}{cls.RESET}"
    @classmethod
    def dim(cls, s): return f"{cls.DIM}{s}{cls.RESET}"
    @classmethod
    def bold(cls, s): return f"{cls.BOLD}{s}{cls.RESET}"


def add_species(name: str) -> int:
    name = name.lower().strip()
    if not name:
        print(C.red("species name required"))
        return 1
    base = DROP_ROOT / name
    for st in SOURCE_TYPES:
        (base / st).mkdir(parents=True, exist_ok=True)
    print(f"{C.green('✓')} created {C.bold(name)}/ with {len(SOURCE_TYPES)} source-type folders")
    print(f"  {C.dim(str(base))}")
    return 0


def caption_stub(species: str, source_type: str) -> str:
    species_human = species.replace("_", " ").title()
    if source_type == "skeletal":
        return f"a {species_human} skeletal mount, museum specimen, lateral view, neutral pose"
    if source_type == "paleoart":
        return f"a {species_human}, scientifically accurate paleoart, anatomically correct, natural pose"
    if source_type == "living_analog":
        return f"a living animal reference for {species_human} anatomy, photographic"
    return f"a {species_human}"


def ingest_one(image: Path, species: str, source_type: str, dry_run: bool) -> bool:
    dest_dir = DEST_ROOT / species / source_type
    dest = dest_dir / image.name
    if dest.exists():
        print(f"  {C.yellow('skip')} {image.name} — already at {dest.relative_to(REPO_ROOT)}")
        return False

    sidecar_json = dest.with_suffix(".json")
    sidecar_txt = dest.with_suffix(".txt")

    rel = dest.relative_to(REPO_ROOT)
    if dry_run:
        print(f"  {C.dim('would move')} {image.name} → {rel}")
        return True

    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(image), str(dest))

    meta = {
        "species": species,
        "source_type": source_type,
        "ingested_at": datetime.now().isoformat(timespec="seconds"),
        "source_url": "",
        "image_url": "",
        "creator": "",
        "license": "",
        "license_url": "",
        "verified": False,
        "source_checked_date": "",
        "quarantined": False,
        "quarantine_reason": "",
        "thesis_score": {},
        "notes": "",
    }
    sidecar_json.write_text(json.dumps(meta, indent=2) + "\n")
    sidecar_txt.write_text(caption_stub(species, source_type) + "\n")

    print(f"  {C.green('✓')} {image.name} → {rel}")
    print(f"  {C.yellow('!')} fill source_url, creator, license in {sidecar_json.name} before training")
    return True


def walk_and_ingest(dry_run: bool) -> int:
    if not DROP_ROOT.exists():
        print(C.red(f"drop root not found: {DROP_ROOT}"))
        return 2

    total = 0
    moved = 0
    for species_dir in sorted(DROP_ROOT.iterdir()):
        if not species_dir.is_dir() or species_dir.name.startswith((".", "_")):
            continue
        species = species_dir.name.lower()

        printed_header = False
        for st in SOURCE_TYPES:
            st_dir = species_dir / st
            if not st_dir.is_dir():
                continue
            images = [p for p in st_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
            if not images:
                continue
            if not printed_header:
                print(f"\n{C.teal(species)}")
                printed_header = True
            print(f"  {C.dim(st + '/')}")
            for img in sorted(images):
                total += 1
                if ingest_one(img, species, st, dry_run):
                    moved += 1

        # Warn about loose files dropped at the species-root level.
        loose = [p for p in species_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
        if loose:
            print(f"  {C.yellow('warn')} {len(loose)} loose image(s) in {species}/ — "
                  f"move into a source-type subfolder ({', '.join(SOURCE_TYPES)})")

    if total == 0:
        print(C.dim("nothing to ingest"))
    else:
        verb = "would move" if dry_run else "moved"
        print(f"\n{C.bold(f'{verb} {moved}/{total}')} image(s)")
        if not dry_run and moved:
            print(C.dim("→ edit .txt caption stubs and fill source_url/license in .json before training"))
    return 0


def validate_training_refs(species_filter: str | None = None) -> int:
    """Audit all sidecar JSONs in training_refs/ for missing or banned license fields.
    Returns number of problems found.
    """
    problems = 0
    for sidecar in sorted(DEST_ROOT.rglob("*.json")):
        try:
            meta = json.loads(sidecar.read_text())
        except Exception:
            continue

        species = meta.get("species", "")
        if species_filter and species_filter.lower() not in species.lower():
            continue

        flags = []
        if not meta.get("source_url"):
            flags.append("missing source_url")
        if not meta.get("creator"):
            flags.append("missing creator")
        if not meta.get("license"):
            flags.append("missing license")
        elif any(kw in meta["license"].upper() for kw in BANNED_LICENSE_KEYWORDS):
            flags.append(f"BANNED license: {meta['license']}")
        elif meta["license"] not in ALLOWED_LICENSES:
            flags.append(f"unrecognized license: {meta['license']} (verify it's not NC/ND)")
        if meta.get("quarantined"):
            flags.append(f"QUARANTINED: {meta.get('quarantine_reason', 'no reason given')}")

        if flags:
            rel = sidecar.relative_to(REPO_ROOT)
            print(f"  {C.red('✗')} {C.bold(str(rel))}")
            for f in flags:
                print(f"       {C.yellow('·')} {f}")
            problems += 1

    if problems == 0:
        print(C.green("  ✓ all sidecars look clean"))
    else:
        print(f"\n  {C.bold(C.red(str(problems)))} sidecar(s) need attention before training")
    return problems


def main():
    ap = argparse.ArgumentParser(description="Ingest training drop folders into training_refs/")
    ap.add_argument("--add-species", metavar="NAME", help="Create empty drop folders for a new species")
    ap.add_argument("--dry-run", action="store_true", help="Show what would move without touching files")
    ap.add_argument("--validate", action="store_true", help="Audit all training_refs/ sidecars for license issues")
    ap.add_argument("--species", metavar="NAME", help="Filter --validate to one species")
    args = ap.parse_args()

    if args.add_species:
        sys.exit(add_species(args.add_species))
    if args.validate:
        print(f"\n{C.bold(C.teal('Training refs license audit'))}\n")
        problems = validate_training_refs(args.species)
        sys.exit(0 if problems == 0 else 1)
    sys.exit(walk_and_ingest(args.dry_run))


if __name__ == "__main__":
    main()

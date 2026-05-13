#!/usr/bin/env python3
"""
reference.py — drop a scientifically accurate dinosaur reference image into
a short interview, get it logged into winners.json so generate_prompt.py
can pull its anatomy notes into future prompts (and Phase C LoRA training
can use it as a positive example).

Usage:
    python3 reference.py [image_path]

If no path is given, you'll be prompted to drag-drop the image into the
terminal. The interview captures:
    - species (auto-detected from filename when possible)
    - source URL / attribution
    - source subtype (paleoart, museum, living analog, wildlife, other)
    - what's anatomically accurate (free-form notes)
    - what's wrong or caveats (optional)
    - LLaVA anatomy analysis (automatic if Ollama + llava available)

Reference entries are written to winners.json with source_type="reference"
so they're distinguishable from generated winners but still flow through
get_winner_anatomy_hints() to reinforce future prompts.

The image is copied (not moved) into assets/gallery/flux/training_refs/
with a slugified filename.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

REPO_ROOT     = Path(__file__).resolve().parent
WINNERS_FILE  = REPO_ROOT / "winners.json"
TRAINING_DIR  = REPO_ROOT / "assets" / "gallery" / "flux" / "training_refs"

# Try to reuse unified_feedback's vision call so we keep one LLaVA prompt.
try:
    from unified_feedback import analyze_winner_anatomy  # type: ignore
except Exception:
    analyze_winner_anatomy = None


# ─── Color palette (teal + blue per user preference) ────────────────────────
class C:
    RESET = "\033[0m"
    BOLD  = "\033[1m"
    DIM   = "\033[2m"
    TEAL  = "\033[96m"
    BLUE  = "\033[94m"
    WHITE = "\033[97m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED   = "\033[91m"


def teal(s: str) -> str:  return f"{C.TEAL}{s}{C.RESET}"
def blue(s: str) -> str:  return f"{C.BLUE}{s}{C.RESET}"
def dim(s: str) -> str:   return f"{C.DIM}{s}{C.RESET}"
def bold(s: str) -> str:  return f"{C.BOLD}{s}{C.RESET}"


def banner(title: str) -> None:
    bar = "═" * 62
    print(f"\n{teal(bar)}")
    print(f"  {bold(teal(title))}")
    print(f"{teal(bar)}\n")


def section(title: str) -> None:
    print(f"\n  {bold(blue('▸ ' + title))}\n")


# ─── Image path resolution ──────────────────────────────────────────────────

def resolve_image_path(arg: Optional[str]) -> Path:
    """Get a valid image path, prompting drag-drop if not provided."""
    if arg:
        candidate = arg.strip().strip("'\"")
        path = Path(candidate).expanduser()
        if path.exists() and path.is_file():
            return path.resolve()
        print(f"  {C.RED}✗  {path} not found{C.RESET}")
        sys.exit(1)

    print(f"  {teal('Drag a reference image into this terminal and press Enter')}")
    print(f"  {dim('(or type/paste a path)')}")
    raw = input(f"  {blue('image: ')}").strip().strip("'\"")
    if not raw:
        print(f"  {C.RED}No path given.{C.RESET}")
        sys.exit(1)
    path = Path(raw).expanduser()
    if not path.exists() or not path.is_file():
        print(f"  {C.RED}✗  {path} not found{C.RESET}")
        sys.exit(1)
    return path.resolve()


# ─── Slugifier for the destination filename ─────────────────────────────────

_SLUG_RE = re.compile(r"[^a-z0-9]+")

def slugify(text: str) -> str:
    s = _SLUG_RE.sub("-", text.lower()).strip("-")
    return s or "ref"


def copy_into_training_refs(src: Path, species: str) -> Path:
    TRAINING_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    species_slug = slugify(species)
    src_stem = slugify(src.stem)
    dest = TRAINING_DIR / f"{species_slug}_{stamp}_{src_stem}{src.suffix.lower()}"
    shutil.copy2(src, dest)
    return dest


# ─── Species detection ──────────────────────────────────────────────────────

KNOWN_SPECIES = [
    "Tyrannosaurus rex", "Triceratops", "Velociraptor", "Stegosaurus",
    "Brachiosaurus", "Allosaurus", "Spinosaurus", "Ankylosaurus",
    "Diplodocus", "Carnotaurus", "Parasaurolophus", "Pteranodon",
    "Mosasaurus", "Plesiosaurus", "Therizinosaurus", "Deinonychus",
    "Iguanodon", "Pachycephalosaurus", "Dilophosaurus", "Yutyrannus",
]

def guess_species(image_path: Path) -> Optional[str]:
    name = image_path.stem.lower().replace("_", " ").replace("-", " ")
    for sp in KNOWN_SPECIES:
        first = sp.split()[0].lower()
        if first in name or sp.lower() in name:
            return sp
    if "rex" in name or "trex" in name or "t rex" in name:
        return "Tyrannosaurus rex"
    return None


# ─── Interview helpers ──────────────────────────────────────────────────────

def ask(question: str, *, default: Optional[str] = None, allow_blank: bool = False) -> str:
    suffix = f" {dim(f'[{default}]')}" if default else ""
    while True:
        raw = input(f"  {blue(question)}{suffix} {dim('>')} ").strip()
        if raw:
            return raw
        if default is not None:
            return default
        if allow_blank:
            return ""
        print(f"  {C.YELLOW}(required){C.RESET}")


def ask_multiline(question: str, *, allow_blank: bool = True) -> str:
    print(f"  {blue(question)}")
    print(f"  {dim('(end with a blank line)')}")
    lines = []
    while True:
        try:
            line = input(f"  {dim('|')} ")
        except EOFError:
            break
        if not line.strip():
            if lines:
                break
            if allow_blank:
                return ""
            continue
        lines.append(line.rstrip())
    return "\n".join(lines)


SOURCE_SUBTYPES = [
    ("paleoart",       "Paleoart illustration (Witton, Csotonyi, Henderson, etc.)"),
    ("museum",         "Museum specimen photo / mounted skeleton"),
    ("living_analog",  "Living animal analog (Komodo, croc, cassowary, etc.)"),
    ("wildlife",       "Wildlife / nature photograph"),
    ("other",          "Other (specify in source URL)"),
]

# Only licenses cleared for commercial LoRA training. NC/ND are banned.
_ALLOWED_LICENSES = [
    ("CC0",          "CC0 — Public Domain (no attribution needed, gold standard)"),
    ("CC BY 4.0",    "CC BY 4.0 — Attribution required"),
    ("CC BY 3.0",    "CC BY 3.0 — Attribution required"),
    ("CC BY 2.0",    "CC BY 2.0 — Attribution required"),
    ("CC BY-SA 4.0", "CC BY-SA 4.0 — Attribution + ShareAlike (use with caution)"),
    ("CC BY-SA 3.0", "CC BY-SA 3.0 — Attribution + ShareAlike (use with caution)"),
    ("CC BY-SA 2.0", "CC BY-SA 2.0 — Attribution + ShareAlike (use with caution)"),
    ("Public Domain","Public Domain — pre-1927 or government work"),
]

_LICENSE_URLS = {
    "CC0":          "https://creativecommons.org/publicdomain/zero/1.0/",
    "CC BY 4.0":    "https://creativecommons.org/licenses/by/4.0/",
    "CC BY 3.0":    "https://creativecommons.org/licenses/by/3.0/",
    "CC BY 2.0":    "https://creativecommons.org/licenses/by/2.0/",
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/",
    "CC BY-SA 2.0": "https://creativecommons.org/licenses/by-sa/2.0/",
    "Public Domain": "",
}


def pick_license() -> str:
    print(f"  {bold(blue('License'))} {dim('(NC and ND are banned — do not ingest those images)')}")
    for i, (key, desc) in enumerate(_ALLOWED_LICENSES, start=1):
        print(f"    {teal(str(i))}) {desc}")
    while True:
        raw = input(f"  {dim('>')} ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(_ALLOWED_LICENSES):
            return _ALLOWED_LICENSES[int(raw) - 1][0]
        for key, _ in _ALLOWED_LICENSES:
            if raw.upper() == key.upper():
                return key
        print(f"  {C.YELLOW}(pick 1-{len(_ALLOWED_LICENSES)}, or if NC/ND → abort and discard this image){C.RESET}")


def pick_source_subtype() -> str:
    print(f"  {blue('Source type:')}")
    for i, (key, desc) in enumerate(SOURCE_SUBTYPES, start=1):
        print(f"    {teal(str(i))}) {desc}")
    while True:
        raw = input(f"  {dim('>')} ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(SOURCE_SUBTYPES):
            return SOURCE_SUBTYPES[int(raw) - 1][0]
        for key, _ in SOURCE_SUBTYPES:
            if raw.lower() == key:
                return key
        print(f"  {C.YELLOW}(pick 1-{len(SOURCE_SUBTYPES)}){C.RESET}")


# ─── winners.json writer ────────────────────────────────────────────────────

def append_reference_entry(species: str, entry: dict) -> int:
    """Append a reference entry to winners.json. Returns total entries for species."""
    if WINNERS_FILE.exists():
        with open(WINNERS_FILE) as f:
            winners = json.load(f)
    else:
        winners = {}

    winners.pop("_description", None)
    winners.pop("_format", None)

    winners.setdefault(species, []).append(entry)
    # Keep refs without truncating — generated winners still capped elsewhere.
    # Sort so highest-scoring (refs default to 10) appear first.
    winners[species] = sorted(winners[species], key=lambda x: x.get("score", 0), reverse=True)

    with open(WINNERS_FILE, "w") as f:
        json.dump(winners, f, indent=2)
    return len(winners[species])


# ─── Main interview flow ────────────────────────────────────────────────────

def write_caption_file(image_dest: Path, species: str, anatomy_notes: str) -> Path:
    """Write a .txt caption file for the image (for ai-toolkit LoRA training)."""
    caption_path = image_dest.with_suffix(".txt")
    caption = f"a photo of {species}, {anatomy_notes}"
    with open(caption_path, "w") as f:
        f.write(caption)
    return caption_path


def run_single(image_path: Path) -> dict:
    """Run interview for a single image. Returns entry dict and dest path."""
    print(f"  {dim('image:')} {image_path}")

    section("Step 1 — Species")
    guessed = guess_species(image_path)
    species = ask(
        "Which species is this?",
        default=guessed,
        allow_blank=False,
    )

    section("Step 2 — Source & License")
    source_url = ask("Source URL (Wikimedia page, museum link, etc.)", allow_blank=False)
    creator = ask("Creator / artist name", allow_blank=False)
    license_str = pick_license()
    license_url = _LICENSE_URLS.get(license_str, "")
    subtype = pick_source_subtype()

    section("Step 3 — What's anatomically accurate?")
    print(f"  {dim('Focus on tooth shape, claw morphology, foot structure, jaw line,')}")
    print(f"  {dim('posture, proportions, integument — the parts you want reinforced.')}\n")
    accurate = ask_multiline("Accurate features:", allow_blank=False)

    section("Step 4 — Anything wrong or worth flagging?")
    caveats = ask_multiline("Caveats (optional):", allow_blank=True)

    section("Step 5 — LLaVA anatomy analysis")
    if analyze_winner_anatomy is None:
        print(f"  {C.YELLOW}unified_feedback.analyze_winner_anatomy unavailable — skipping{C.RESET}")
        llava = ""
    else:
        print(f"  {dim('running llava...')}")
        try:
            llava = analyze_winner_anatomy(str(image_path)) or ""
        except Exception as e:
            print(f"  {C.YELLOW}LLaVA failed: {e}{C.RESET}")
            llava = ""
        if llava:
            print(f"  {C.GREEN}✓{C.RESET} {dim(llava[:200] + ('…' if len(llava) > 200 else ''))}")
        else:
            print(f"  {dim('(no analysis returned)')}")

    section("Step 6 — Copy into training_refs/")
    dest = copy_into_training_refs(image_path, species)
    print(f"  {C.GREEN}✓{C.RESET} {dim(str(dest.relative_to(REPO_ROOT)))}")

    # Compose the anatomy_analysis field by combining user notes + LLaVA so
    # generate_prompt.py picks up both via get_winner_anatomy_hints().
    composed_parts = []
    if accurate:
        composed_parts.append("User-verified accurate features:\n" + accurate)
    if caveats:
        composed_parts.append("Caveats:\n" + caveats)
    if llava:
        composed_parts.append("LLaVA analysis:\n" + llava)
    composed_anatomy = "\n\n".join(composed_parts)

    # For .txt caption: use just the accurate features (cleaner for training)
    caption_notes = accurate.strip() if accurate else "reference image"

    section("Step 7 — Write caption file")
    caption_dest = write_caption_file(dest, species, caption_notes)
    print(f"  {C.GREEN}✓{C.RESET} {dim(str(caption_dest.relative_to(REPO_ROOT)))}")

    entry = {
        "prompt": f"REFERENCE: {species} ({subtype})",
        "mj_flags": {},
        "score": 10.0,
        "session_id": -1,
        "timestamp": datetime.now().isoformat(),
        "image_path": str(dest.relative_to(REPO_ROOT)),
        "anatomy_analysis": composed_anatomy,
        "source_type": "reference",
        "source_subtype": subtype,
        "source_url": source_url,
        "creator": creator,
        "license": license_str,
        "license_url": license_url,
        "verified": True,
        "source_checked_date": datetime.now().strftime("%Y-%m-%d"),
        "user_accurate_notes": accurate,
        "user_caveats": caveats,
    }

    return {"entry": entry, "species": species, "dest": dest}


def run(image_path: Path) -> None:
    banner("REFERENCE IMAGE INTERVIEW — BATCH MODE")

    results = []
    total = 0

    while True:
        print()
        result = run_single(image_path)
        species = result["species"]
        entry = result["entry"]

        section("Step 8 — Save to winners.json")
        total = append_reference_entry(species, entry)
        print(f"  {C.GREEN}✓{C.RESET} written to {dim(str(WINNERS_FILE.relative_to(REPO_ROOT)))}")
        print(f"  {dim(f'{species} now has {total} winner entries (refs + generated).')}")

        results.append(result)

        print()
        more = ask(
            "Add another image?",
            default="n",
            allow_blank=True,
        ).lower()
        if more not in ("y", "yes"):
            break

        print()
        image_path = resolve_image_path(None)

    print()
    banner("SESSION SUMMARY")
    print(f"  {C.GREEN}✓{C.RESET} {len(results)} image(s) processed")
    for r in results:
        print(f"    • {r['species']}: {r['dest'].name}")
    print()
    print(f"  {bold(teal('Done.'))} generate_prompt.py will pull anatomy into future prompts.")
    print(f"  {bold(teal('Next:'))} run {teal('python3 flux/export_dataset.py')} to prepare for LoRA training.\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", nargs="?", help="Path to reference image (or omit to drag-drop)")
    args = parser.parse_args()
    image_path = resolve_image_path(args.image)
    run(image_path)


if __name__ == "__main__":
    main()

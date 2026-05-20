#!/usr/bin/env python3
"""
print_locked_prompt.py — emit a ready-to-paste Midjourney prompt for a species
whose --sref set is locked in refs/locked_refs.json.

Usage:
    python3 tools/print_locked_prompt.py                       # defaults to Tyrannosaurus rex
    python3 tools/print_locked_prompt.py "Tyrannosaurus rex"
    python3 tools/print_locked_prompt.py "Tyrannosaurus rex" | pbcopy

Reads:
  refs/locked_refs.json   — canonical per-species ref list (label + purpose)
  sref_urls.json          — flat pool with fresh Discord CDN URLs
  refs/locked_prompts.json (optional) — per-species base prompt text;
                                        falls back to a built-in T. rex default

Exits non-zero with a clear message if any locked label is missing from the
pool (cue to re-run upload_gallery_refs.py).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_PROMPTS = {
    "Tyrannosaurus rex": (
        "solitary Tyrannosaurus rex, massive deep skull forward binocular eyes "
        "rugose brow ridges, conical honey-gold serrated teeth visible along jaw, "
        "tight pebbly scaly hide olive-brown dorsal tawny underbelly, vestigial "
        "forearms two curved dark keratin claws, pillar-like hindlimbs digitigrade "
        "three-toed feet dark curved claws, thick muscular tail held rigidly "
        "horizontal, 12 meters long 8-tonne apex predator "
        "--no three-fingered, extra fingers, fused digits, dragging tail, skeleton, "
        "fossilized, feathered, pair of animals "
        "--style raw --stylize 75 --sw 50 --q 1"
    ),
}


def main() -> int:
    species = sys.argv[1] if len(sys.argv) > 1 else "Tyrannosaurus rex"

    locked_path = ROOT / "refs" / "locked_refs.json"
    pool_path   = ROOT / "sref_urls.json"
    prompts_path = ROOT / "refs" / "locked_prompts.json"

    locked_all = json.loads(locked_path.read_text())
    if species not in locked_all:
        print(f"!! no locked ref set for {species!r} in {locked_path}", file=sys.stderr)
        return 2

    locked = locked_all[species]["refs"]
    pool = json.loads(pool_path.read_text()).get(species, [])
    by_label = {e["label"]: e["url"] for e in pool}

    urls, missing = [], []
    for r in locked:
        u = by_label.get(r["label"])
        (urls if u else missing).append(u or r["label"])

    if missing:
        print("!! MISSING refs (re-run upload_gallery_refs.py):", file=sys.stderr)
        for m in missing:
            print(f"   - {m}", file=sys.stderr)
        return 1

    base = DEFAULT_PROMPTS.get(species)
    if prompts_path.exists():
        base = json.loads(prompts_path.read_text()).get(species, base)
    if not base:
        print(f"!! no base prompt for {species!r} (add it to {prompts_path} "
              f"or DEFAULT_PROMPTS in {Path(__file__).name})", file=sys.stderr)
        return 3

    print(f"{base} --sref " + " ".join(urls))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

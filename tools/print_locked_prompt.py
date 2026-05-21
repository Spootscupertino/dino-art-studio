#!/usr/bin/env python3
"""
print_locked_prompt.py — emit a ready-to-paste Midjourney prompt for a species
whose ref set is locked in refs/locked_refs.json.

Each ref carries a `slot` that routes it into the prompt:
  - image: URL prepended before prose (subject/composition influence)
  - sref:  appended under --sref (style/texture influence)
  - oref:  appended under --oref (subject preservation, v7+, ONE url max)

`params` in locked_refs.json sets --iw / --sw / --ow. The base prose lives in
refs/locked_prompts.json and must already include --style / --stylize / --q etc.

Usage:
    python3 tools/print_locked_prompt.py                       # defaults to Tyrannosaurus rex
    python3 tools/print_locked_prompt.py "Tyrannosaurus rex"
    python3 tools/print_locked_prompt.py "Tyrannosaurus rex" | pbcopy

Exits non-zero with a clear message if any locked label is missing from the
sref_urls.json pool (cue to re-run upload_gallery_refs.py).
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
        "--style raw --stylize 75 --q 1"
    ),
}


def main() -> int:
    species = sys.argv[1] if len(sys.argv) > 1 else "Tyrannosaurus rex"

    locked_path  = ROOT / "refs" / "locked_refs.json"
    pool_path    = ROOT / "sref_urls.json"
    prompts_path = ROOT / "refs" / "locked_prompts.json"

    locked_all = json.loads(locked_path.read_text())
    if species not in locked_all:
        print(f"!! no locked ref set for {species!r} in {locked_path}", file=sys.stderr)
        return 2

    entry  = locked_all[species]
    locked = entry["refs"]
    params = entry.get("params", {})

    pool = json.loads(pool_path.read_text()).get(species, [])
    by_label = {e["label"]: e["url"] for e in pool}

    image_urls, sref_urls, oref_urls = [], [], []
    missing = []
    for r in locked:
        slot = r.get("slot", "image")
        url  = by_label.get(r["label"])
        if not url:
            missing.append(r["label"])
            continue
        if slot == "image":
            image_urls.append(url)
        elif slot == "sref":
            sref_urls.append(url)
        elif slot == "oref":
            oref_urls.append(url)
        else:
            print(f"!! unknown slot {slot!r} on ref {r['label']!r}", file=sys.stderr)
            return 4

    if missing:
        print("!! MISSING refs (re-run upload_gallery_refs.py):", file=sys.stderr)
        for m in missing:
            print(f"   - {m}", file=sys.stderr)
        return 1

    if len(oref_urls) > 1:
        print(f"!! --oref takes ONE url max; got {len(oref_urls)}. Demote extras to image/sref.",
              file=sys.stderr)
        return 5

    base = DEFAULT_PROMPTS.get(species)
    if prompts_path.exists():
        base = json.loads(prompts_path.read_text()).get(species, base)
    if not base:
        print(f"!! no base prompt for {species!r} (add it to {prompts_path} "
              f"or DEFAULT_PROMPTS in {Path(__file__).name})", file=sys.stderr)
        return 3

    parts = []
    if image_urls:
        parts.append(" ".join(image_urls))
    parts.append(base)
    if sref_urls:
        parts.append("--sref " + " ".join(sref_urls))
        if "sw" in params:
            parts.append(f"--sw {params['sw']}")
    if oref_urls:
        parts.append(f"--oref {oref_urls[0]}")
        if "ow" in params:
            parts.append(f"--ow {params['ow']}")
    if "iw" in params and image_urls:
        parts.append(f"--iw {params['iw']}")

    print(" ".join(parts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

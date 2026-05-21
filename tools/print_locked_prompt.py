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

Default behavior emits TEXT ONLY (no leading image URLs) for MJ web, where
image prompts must be drag-dropped from the saved panel into the prompt bar.
Pass --with-images for the Discord workflow where pasted URLs auto-attach.

Pass --cam <angle> to inject a camera/perspective phrase AND auto-suppress
composition-locking refs (image prompts + --oref), so the camera text actually
gets room to work. Style refs (--sref) stay on for texture/color continuity.

Usage:
    python3 tools/print_locked_prompt.py                                 # text only (MJ web)
    python3 tools/print_locked_prompt.py "Tyrannosaurus rex"
    python3 tools/print_locked_prompt.py --with-images                   # include image-prompt URLs (Discord)
    python3 tools/print_locked_prompt.py --cam wormseye                  # low-angle hero, refs relaxed
    python3 tools/print_locked_prompt.py --cam list                      # show all camera presets
    python3 tools/print_locked_prompt.py "Tyrannosaurus rex" | pbcopy

Exits non-zero with a clear message if any locked label is missing from the
sref_urls.json pool (cue to re-run upload_gallery_refs.py).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Camera presets. Each phrase is injected at the front of the base prompt and
# triggers suppression of composition-locking refs (image-prompt + oref).
CAMERAS = {
    "wormseye":  "extreme low angle worm's-eye view from ground level, dinosaur towering massive overhead, sky visible behind silhouette, dramatic upward perspective, 24mm lens",
    "hero":      "low hero shot, camera at knee height tilted up, dinosaur looming over viewer, 35mm lens, cinematic",
    "drone":     "aerial drone overhead top-down shot, dinosaur small in vast landscape, 24mm lens, scale dominates",
    "dutch":     "dutch tilt angle, off-kilter horizon, kinetic unease, 50mm lens",
    "tele":      "tight telephoto compression, 600mm lens, flattened perspective, subject isolated against compressed bokeh background",
    "wide":      "ultra-wide establishing shot, 14mm lens, dinosaur small in frame, vast landscape dominates, cinematic scale",
    "pov":       "first-person POV from prey eye-level, dinosaur charging head-on toward camera, motion blur at edges",
    "tracking":  "panning tracking shot, sharp dinosaur mid-stride, motion-blurred background streaks, 200mm pan",
    "back":      "rear view from directly behind dinosaur, tail and back of head visible, looking out at environment beyond",
    "macro":     "extreme macro close-up, single anatomical surface fills frame, texture dominant, 100mm macro lens, razor-thin depth of field",
    "profile":   "classic broadside side profile, full body lateral view, magazine cover composition",
}

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


def parse_args(argv):
    """Tiny manual parser. Supports positional species, --with-images, --cam <name>."""
    positional, with_images, cam = [], False, None
    it = iter(argv)
    for tok in it:
        if tok == "--with-images":
            with_images = True
        elif tok == "--cam":
            cam = next(it, None)
        elif tok.startswith("--cam="):
            cam = tok.split("=", 1)[1]
        elif tok.startswith("--"):
            print(f"!! unknown flag {tok!r}", file=sys.stderr)
            sys.exit(2)
        else:
            positional.append(tok)
    return positional, with_images, cam


def main() -> int:
    positional, with_images, cam = parse_args(sys.argv[1:])
    species = positional[0] if positional else "Tyrannosaurus rex"

    if cam == "list":
        print("Available --cam presets:", file=sys.stderr)
        for name, phrase in CAMERAS.items():
            print(f"  {name:10s}  {phrase}", file=sys.stderr)
        return 0

    if cam is not None and cam not in CAMERAS:
        print(f"!! unknown --cam {cam!r}. Use --cam list to see options.", file=sys.stderr)
        return 6

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

    # When --cam is set (and isn't "profile"), suppress composition-locking refs
    # so the camera phrase actually has room to influence framing.
    suppress_composition = cam is not None and cam != "profile"

    image_urls, sref_urls, oref_urls = [], [], []
    missing, suppressed = [], []
    for r in locked:
        slot = r.get("slot", "image")
        url  = by_label.get(r["label"])
        if not url:
            missing.append(r["label"])
            continue
        if suppress_composition and slot in ("image", "oref"):
            suppressed.append(r)
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

    # Inject camera phrase at the very front of the base prose.
    if cam:
        base = CAMERAS[cam] + ", " + base

    parts = []
    if with_images and image_urls:
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
    if with_images and image_urls and "iw" in params:
        parts.append(f"--iw {params['iw']}")

    print(" ".join(parts))

    # Stderr help: drag-drop reminder + suppression notice.
    notes = []
    if not with_images and image_urls:
        notes.append(f"# {len(image_urls)} image prompt(s) NOT included — drag from MJ saved panel:")
        for r in locked:
            if r.get("slot", "image") == "image" and by_label.get(r["label"]) in image_urls:
                notes.append(f"#   - {r['purpose']}: {Path(r['label']).name}")
        notes.append("# (use --with-images to include URLs inline for Discord workflow)")
    if suppressed:
        notes.append(f"# --cam {cam}: suppressed {len(suppressed)} composition-locking ref(s):")
        for r in suppressed:
            notes.append(f"#   - [{r.get('slot')}] {r['purpose']}")
        notes.append("# (style --sref refs kept for texture/color continuity)")
    if notes:
        print(file=sys.stderr)
        for line in notes:
            print(line, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

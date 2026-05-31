#!/usr/bin/env python3
"""web_promote.py — Promote horizontal/vertical winners onto the public website.

Called automatically by printify_sync.sh after a 9+ image lands in horizontal/
or vertical/. For each image:
  1. Detects species from slug → maps to website category folder
  2. Copies to site/src/assets/gallery/<category>/ if not already there
  3. Writes a .txt sidecar sentence (SEO caption visible on product page)
  4. Returns changed paths so the caller can commit + deploy

Usage:
  python3 tools/web_promote.py site/src/assets/gallery/horizontal \
                                site/src/assets/gallery/vertical
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GALLERY = ROOT / "site" / "src" / "assets" / "gallery"

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

# ── Species → website category ────────────────────────────────────────────────
# Carnivores / apex predators → predators
# Herbivores / filter-feeders → herbivores
# Marine reptiles / fish      → marine
# Pterosaurs / fliers         → aerial
# Plants / arthropods         → flora_arthropods

SPECIES_CATEGORY = {
    # Predators
    "tyrannosaurus rex":    "predators",
    "tyrannosaurus":        "predators",
    "t-rex":                "predators",
    "t rex":                "predators",
    "trex":                 "predators",
    "velociraptor":         "predators",
    "deinonychus":          "predators",
    "utahraptor":           "predators",
    "allosaurus":           "predators",
    "carnotaurus":          "predators",
    "spinosaurus":          "predators",
    "dilophosaurus":        "predators",
    "ceratosaurus":         "predators",
    "giganotosaurus":       "predators",
    "carcharodontosaurus":  "predators",
    "acrocanthosaurus":     "predators",
    "megaraptor":           "predators",
    "baryonyx":             "predators",
    "suchomimus":           "predators",
    "oviraptor":            "predators",
    "gallimimus":           "predators",
    "therizinosaurus":      "predators",
    "dromaeosaurus":        "predators",
    "troodon":              "predators",
    "compsognathus":        "predators",
    # Herbivores
    "triceratops":          "herbivores",
    "stegosaurus":          "herbivores",
    "brachiosaurus":        "herbivores",
    "apatosaurus":          "herbivores",
    "diplodocus":           "herbivores",
    "ankylosaurus":         "herbivores",
    "pachycephalosaurus":   "herbivores",
    "parasaurolophus":      "herbivores",
    "iguanodon":            "herbivores",
    "edmontosaurus":        "herbivores",
    "hadrosaur":            "herbivores",
    "protoceratops":        "herbivores",
    "styracosaurus":        "herbivores",
    "torosaurus":           "herbivores",
    "maiasaura":            "herbivores",
    "corythosaurus":        "herbivores",
    "lambeosaurus":         "herbivores",
    "kentrosaurus":         "herbivores",
    "sauropod":             "herbivores",
    "ceratopsian":          "herbivores",
    "mammoth":              "herbivores",
    "smilodon":             "predators",
    # Marine
    "mosasaurus":           "marine",
    "elasmosaurus":         "marine",
    "plesiosaurus":         "marine",
    "pliosaurus":           "marine",
    "liopleurodon":         "marine",
    "kronosaurus":          "marine",
    "ichthyosaurus":        "marine",
    "megalodon":            "marine",
    "dunkleosteus":         "marine",
    "xiphactinus":          "marine",
    "cretoxyrhina":         "marine",
    "helicoprion":          "marine",
    "archelon":             "marine",
    "leedsichthys":         "marine",
    "ammonite":             "marine",
    # Aerial
    "pteranodon":           "aerial",
    "quetzalcoatlus":       "aerial",
    "pterodactyl":          "aerial",
    "pterodactylus":        "aerial",
    "pterosaur":            "aerial",
    "rhamphorhynchus":      "aerial",
    "dimorphodon":          "aerial",
    "archaeopteryx":        "aerial",
    # Flora / arthropods
    "lepidodendron":        "flora_arthropods",
    "trilobite":            "flora_arthropods",
    "anomalocaris":         "flora_arthropods",
    "meganeura":            "flora_arthropods",
    "arthropleura":         "flora_arthropods",
    "pulmonoscorpius":      "flora_arthropods",
}

_SPECIES_KEYS = sorted(SPECIES_CATEGORY.keys(), key=len, reverse=True)

# ── Slug-word → readable phrase ───────────────────────────────────────────────
WEATHER_DISPLAY = {
    "monsoon":      "a driving monsoon",
    "rain":         "heavy rain",
    "storm":        "a violent storm",
    "stormy":       "a violent storm",
    "lightning":    "a lightning storm",
    "fog":          "dense fog",
    "mist":         "morning mist",
    "snow":         "snowfall",
    "frost":        "frost",
    "ash":          "volcanic ash",
    "volcanic":     "volcanic ash",
    "wildfire":     "wildfire smoke",
    "dust":         "a dust storm",
    "haze":         "golden haze",
    "golden":       "golden light",
    "crystal":      "crystal-clear morning air",
    "rainbow":      "a clearing storm",
    "twilight":     "twilight",
    "blue":         "blue-hour twilight",
    "crepuscular":  "crepuscular rays",
    "rays":         "crepuscular rays",
    "dawn":         "dawn light",
    "dusk":         "dusk",
    "overcast":     "overcast skies",
    "drizzle":      "light drizzle",
}

ACTION_DISPLAY = {
    "charge":       "charging",
    "charging":     "charging",
    "hunt":         "hunting",
    "hunting":      "hunting",
    "menacing":     "poised and menacing",
    "serene":       "in a serene moment",
    "alert":        "on high alert",
    "scent":        "tracking by scent",
    "drinking":     "drinking",
    "wading":       "wading through shallow water",
    "roar":         "mid-roar",
    "territorial":  "holding territory",
    "dawn":         "at dawn",
    "dusk":         "at dusk",
    "mid":          "mid-stride",
    "stride":       "mid-stride",
    "grazing":      "grazing",
    "resting":      "resting",
    "eye":          "making eye contact",
}

ERA_DISPLAY = {
    "tyrannosaurus rex": "Late Cretaceous",
    "triceratops":       "Late Cretaceous",
    "velociraptor":      "Late Cretaceous",
    "stegosaurus":       "Late Jurassic",
    "brachiosaurus":     "Late Jurassic",
    "allosaurus":        "Late Jurassic",
    "spinosaurus":       "Cretaceous",
    "mosasaurus":        "Late Cretaceous",
    "pteranodon":        "Late Cretaceous",
    "megalodon":         "Miocene",
}
_ERA_FALLBACK = "Mesozoic"


def _detect_species(slug: str) -> tuple[str | None, str]:
    """Return (species_key, category) from slug words."""
    haystack = slug.replace("-", " ").replace("_", " ").lower()
    for key in _SPECIES_KEYS:
        if key in haystack:
            return key, SPECIES_CATEGORY[key]
    return None, "predators"


def _make_caption(slug: str, species_key: str | None) -> str:
    """Build one SEO sentence from slug words + species context."""
    words = re.split(r"[-_\s]+", slug.lower())
    word_set = set(words)

    # Species display name
    if species_key:
        display = species_key.title().replace("T Rex", "T. rex").replace("T-Rex", "T. rex")
        display = re.sub(r"\bRex\b", "rex", display)
        era = ERA_DISPLAY.get(species_key, _ERA_FALLBACK)
    else:
        display = "prehistoric creature"
        era = _ERA_FALLBACK

    # Pick best weather phrase
    weather = None
    for w, phrase in WEATHER_DISPLAY.items():
        if w in word_set:
            weather = phrase
            break

    # Pick best action phrase
    action = None
    for w, phrase in ACTION_DISPLAY.items():
        if w in word_set:
            action = phrase
            break

    # Assemble a short, human scene sentence — no marketing filler.
    if weather and action:
        return f"A {display} {action} through {weather}, {era}."
    elif weather:
        return f"A {display} in {weather}, {era}."
    elif action:
        return f"A {display} {action}, {era}."
    else:
        return f"A {display} in its natural {era} habitat."


def promote(src_dir: Path) -> list[Path]:
    """Promote winners from src_dir into the appropriate website category folder.
    Returns list of image Paths that were newly added (for git staging).
    """
    added: list[Path] = []
    images = [f for f in src_dir.iterdir() if f.suffix.lower() in IMAGE_EXTS]
    if not images:
        return added

    for img in sorted(images):
        species_key, category = _detect_species(img.stem)
        dest_dir = GALLERY / category
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / img.name

        # Copy image
        if not dest.exists():
            shutil.copy2(img, dest)
            print(f"  [web_promote] {img.name} → {category}/")
            added.append(dest)
        else:
            print(f"  [web_promote] {img.name} already in {category}/ — skipping")

        # Carry the curated .meta.json sidecar (durable SEO → site + Printify).
        src_meta = img.with_suffix(img.suffix + ".meta.json")
        dest_meta = dest.with_suffix(dest.suffix + ".meta.json")
        has_meta = src_meta.exists()
        if has_meta and not dest_meta.exists():
            shutil.copy2(src_meta, dest_meta)
            print(f"  [web_promote] carried {src_meta.name} → {category}/")
            if dest in added:
                added.append(dest_meta)

        # Write a derived .txt caption only when no curated meta caption exists.
        txt = dest.with_suffix(".txt")
        if not txt.exists() and not has_meta:
            caption = _make_caption(img.stem, species_key)
            txt.write_text(caption, encoding="utf-8")
            print(f"  [web_promote] wrote caption: {caption}")
            if dest in added:
                added.append(txt)

    return added


if __name__ == "__main__":
    dirs = [Path(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else [
        GALLERY / "horizontal",
        GALLERY / "vertical",
    ]
    new_images: list[str] = []
    for d in dirs:
        if d.exists():
            for p in promote(d):
                if p.suffix.lower() in IMAGE_EXTS:
                    new_images.append(str(p.relative_to(GALLERY)))
    print(f"  [web_promote] {len(new_images)} new image(s) promoted to website gallery.")
    # Machine-readable lines for printify_sync.sh to scope the publish to just
    # these new winners (one gallery-relative path per line).
    for rel in new_images:
        print(f"NEW_IMAGE\t{rel}")

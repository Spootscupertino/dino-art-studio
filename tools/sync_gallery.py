#!/usr/bin/env python3
# Sync site/src/data/products.json with files in site/public/assets/website_dino_images/.
# - Adds entries for new images and videos
# - Removes entries for files that no longer exist
# - Idempotent (safe to run repeatedly)
# - No external Python deps; uses `file` for image dimensions and `ffprobe` (if present) for video.

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "site" / "public" / "assets" / "website_dino_images"
PRODUCTS_JSON = ROOT / "site" / "src" / "data" / "products.json"
PUBLIC_PREFIX = "/assets/website_dino_images/"

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
VIDEO_EXTS = {".mp4", ".webm", ".mov"}

# Species → category map. Categories mirror the prompt generator's habitats,
# but arthropods + plants share one tab on the site.
# Categories: terrestrial | aerial | marine | flora_arthropods
SPECIES_CATEGORY = {
    # Terrestrial — land dinosaurs and large land vertebrates
    "tyrannosaurus rex":   "terrestrial",
    "tyrannosaurus":       "terrestrial",
    "t-rex":               "terrestrial",
    "t rex":               "terrestrial",
    "trex":                "terrestrial",
    "triceratops":         "terrestrial",
    "stegosaurus":         "terrestrial",
    "velociraptor":        "terrestrial",
    "carnotaurus":         "terrestrial",
    "dilophosaurus":       "terrestrial",
    "brachiosaurus":       "terrestrial",
    "allosaurus":          "terrestrial",
    "spinosaurus":         "terrestrial",
    "apatosaurus":         "terrestrial",
    "iguanodon":           "terrestrial",
    "parasaurolophus":     "terrestrial",
    "ankylosaurus":        "terrestrial",
    "pachycephalosaurus":  "terrestrial",
    "deinonychus":         "terrestrial",
    "utahraptor":          "terrestrial",
    "diplodocus":          "terrestrial",
    "gallimimus":          "terrestrial",
    "oviraptor":           "terrestrial",
    "therizinosaurus":     "terrestrial",
    "compsognathus":       "terrestrial",
    "dimetrodon":          "terrestrial",
    "smilodon":            "terrestrial",
    "mammoth":             "terrestrial",
    "dinosaur":            "terrestrial",
    "dino":                "terrestrial",

    # Aerial — pterosaurs and flying species
    "pteranodon":          "aerial",
    "quetzalcoatlus":      "aerial",
    "archaeopteryx":       "aerial",
    "rhamphorhynchus":     "aerial",
    "pterodactyl":         "aerial",
    "pterodactylus":       "aerial",
    "pterosaur":           "aerial",
    "dimorphodon":         "aerial",

    # Marine — ocean, water-dwelling
    "liopleurodon":        "marine",
    "ammonite":            "marine",
    "plesiosaurus":        "marine",
    "mosasaurus":          "marine",
    "ichthyosaurus":       "marine",
    "megalodon":           "marine",
    "elasmosaurus":        "marine",
    "kronosaurus":         "marine",
    "pliosaurus":          "marine",
    "dunkleosteus":        "marine",
    "nautilus":            "marine",
    "shark":               "marine",
    "whale":               "marine",

    # Flora & Arthropods — plants, insects, giant invertebrates
    "lepidodendron":       "flora_arthropods",
    "trilobite":           "flora_arthropods",
    "anomalocaris":        "flora_arthropods",
    "meganeura":           "flora_arthropods",
    "arthropleura":        "flora_arthropods",
    "pulmonoscorpius":     "flora_arthropods",
    "dragonfly":           "flora_arthropods",
    "scorpion":            "flora_arthropods",
    "millipede":           "flora_arthropods",
    "centipede":           "flora_arthropods",
    "fern":                "flora_arthropods",
    "cycad":               "flora_arthropods",
    "mushroom":            "flora_arthropods",
    "bloom":               "flora_arthropods",
    "flower":              "flora_arthropods",
    "tree":                "flora_arthropods",
    "forest":              "flora_arthropods",
    "lycopsid":            "flora_arthropods",
    "conifer":             "flora_arthropods",
}

SPECIES = list(SPECIES_CATEGORY.keys())


def derive_category(filename: str, title: str = "") -> str:
    stem = Path(filename).stem.lower()
    stem = UUID_PATTERN.sub("", stem)
    haystack = f"{stem} {title.lower()}"
    for sp in sorted(SPECIES_CATEGORY.keys(), key=len, reverse=True):
        if sp in haystack:
            return SPECIES_CATEGORY[sp]
    return "terrestrial"

UUID_PATTERN = re.compile(r"_[a-f0-9]{8,}(-[a-f0-9-]+)?$")
FILLER = {
    "spootscupertino", "the", "of", "with", "and", "a", "an", "in", "on",
    "at", "to", "from", "macro", "extreme", "massive", "large", "small",
    "huge", "feathered", "scientifically", "accurate", "image", "generated",
    "gemini", "close", "up", "deta", "details", "photo", "render",
}


def derive_title(filename: str) -> str:
    stem = Path(filename).stem.lower()
    stem = UUID_PATTERN.sub("", stem)

    for sp in sorted(SPECIES, key=len, reverse=True):
        if sp in stem:
            t = sp.title()
            return t.replace("T-Rex", "T. rex").replace("T Rex", "T. rex")

    words = re.split(r"[_\-\s]+", stem)
    words = [w for w in words if w and w not in FILLER and not re.fullmatch(r"\d+", w)]
    if not words:
        return Path(filename).stem
    return " ".join(words[:3]).title()


def get_image_dims(path: Path):
    try:
        out = subprocess.check_output(["file", str(path)], text=True)
        m = re.search(r"(\d+)\s*x\s*(\d+)", out)
        if m:
            return int(m.group(1)), int(m.group(2))
    except subprocess.CalledProcessError:
        pass
    return None


def get_video_dims(path: Path):
    try:
        out = subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        w, h = out.split(",")
        return int(w), int(h)
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError):
        return 1920, 1080


def title_with_dedupe(title: str, taken: set) -> str:
    if title not in taken:
        return title
    n = 2
    while f"{title} {n}" in taken:
        n += 1
    return f"{title} {n}"


def main() -> int:
    if not ASSETS_DIR.is_dir():
        print(f"ERROR: {ASSETS_DIR} not found", file=sys.stderr)
        return 2

    existing = []
    if PRODUCTS_JSON.exists():
        try:
            existing = json.loads(PRODUCTS_JSON.read_text())
        except json.JSONDecodeError:
            print("WARNING: products.json was malformed; starting fresh.", file=sys.stderr)

    by_filename = {}
    for entry in existing:
        fname = entry.get("filename")
        if not fname:
            img = entry.get("image", "")
            if img.startswith(PUBLIC_PREFIX):
                fname = img[len(PUBLIC_PREFIX):]
        if not fname:
            continue
        ext = Path(fname).suffix.lower()
        if ext not in (IMAGE_EXTS | VIDEO_EXTS):
            continue
        by_filename[fname] = {
            "filename": fname,
            "title": entry.get("title") or derive_title(fname),
            "image": PUBLIC_PREFIX + fname,
            "width": entry.get("width") or 1024,
            "height": entry.get("height") or 1024,
            "type": "video" if ext in VIDEO_EXTS else "image",
            "category": entry.get("category") or derive_category(fname, entry.get("title", "")),
        }

    actual_files = {
        p.name for p in ASSETS_DIR.iterdir()
        if p.is_file() and not p.name.startswith(".")
        and p.suffix.lower() in (IMAGE_EXTS | VIDEO_EXTS)
    }

    by_filename = {k: v for k, v in by_filename.items() if k in actual_files}

    new_count = 0
    for fname in sorted(actual_files):
        if fname in by_filename:
            continue
        path = ASSETS_DIR / fname
        ext = path.suffix.lower()
        if ext in IMAGE_EXTS:
            dims = get_image_dims(path) or (1024, 1024)
            entry_type = "image"
        else:
            dims = get_video_dims(path)
            entry_type = "video"
        taken = {e["title"] for e in by_filename.values()}
        title = title_with_dedupe(derive_title(fname), taken)
        by_filename[fname] = {
            "filename": fname,
            "title": title,
            "image": PUBLIC_PREFIX + fname,
            "width": dims[0],
            "height": dims[1],
            "type": entry_type,
            "category": derive_category(fname, title),
        }
        new_count += 1

    products = sorted(
        by_filename.values(),
        key=lambda e: (ASSETS_DIR / e["filename"]).stat().st_mtime,
        reverse=True,
    )

    new_json = json.dumps(products, indent=2, ensure_ascii=False) + "\n"
    if PRODUCTS_JSON.exists() and PRODUCTS_JSON.read_text() == new_json:
        print(f"sync_gallery: no changes ({len(products)} pieces).")
        return 0

    PRODUCTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    PRODUCTS_JSON.write_text(new_json)
    print(f"sync_gallery: wrote {len(products)} pieces ({new_count} new).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

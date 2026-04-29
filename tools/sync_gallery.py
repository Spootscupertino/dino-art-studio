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

SPECIES = [
    "tyrannosaurus rex", "t-rex", "t rex",
    "tyrannosaurus", "pteranodon", "triceratops", "stegosaurus",
    "velociraptor", "liopleurodon", "ammonite", "carnotaurus",
    "dilophosaurus", "lepidodendron", "brachiosaurus", "allosaurus",
    "spinosaurus", "apatosaurus", "iguanodon", "parasaurolophus",
    "ankylosaurus", "pachycephalosaurus", "plesiosaurus", "mosasaurus",
    "archaeopteryx", "compsognathus", "ichthyosaurus", "megalodon",
    "deinonychus", "utahraptor", "diplodocus", "gallimimus",
    "oviraptor", "therizinosaurus", "elasmosaurus", "kronosaurus",
    "pliosaurus", "quetzalcoatlus", "dimetrodon", "trilobite",
    "anomalocaris", "dunkleosteus", "smilodon", "mammoth",
]

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

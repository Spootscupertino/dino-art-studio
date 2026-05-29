#!/usr/bin/env python3
"""slug_rename.py — Rename non-SEO-friendly image filenames to clean slugs.

Shared utility used by both the website and Printify pipelines.

Usage:
  python3 tools/slug_rename.py [dir1 dir2 ...]
  With no args: renames in all gallery category folders.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GALLERY_DIR = ROOT / "site" / "src" / "assets" / "gallery"
PRODUCTS_JSON = ROOT / "site" / "src" / "data" / "products.json"

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

UUID_PATTERN = re.compile(r"_[a-f0-9]{8,}(-[a-f0-9-]+)?$")
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,59}$")

# Midjourney CDN drops land as "httpss.mj.run<hash>-..." — opaque hashes with no
# species token, so the descriptive-word path below produces a junk slug (or, when
# the derived slug equals the original stem, silently no-ops). For these we derive
# the slug from the curated products.json title instead.
MJ_CDN_RE = re.compile(r"\bmj\.run|httpss?\.mj\.", re.IGNORECASE)

FILLER = {
    "spootscupertino", "the", "of", "with", "and", "a", "an", "in", "on",
    "at", "to", "from", "macro", "extreme", "massive", "large", "small",
    "huge", "feathered", "scientifically", "accurate", "image", "generated",
    "gemini", "close", "up", "deta", "details", "photo", "render",
}

# Species keys ordered longest-first so more specific names match before shorter ones.
_SPECIES_KEYS = sorted([
    "tyrannosaurus rex", "tyrannosaurus", "t-rex", "t rex", "trex",
    "triceratops", "stegosaurus", "velociraptor", "carnotaurus", "dilophosaurus",
    "brachiosaurus", "allosaurus", "spinosaurus", "apatosaurus", "iguanodon",
    "parasaurolophus", "ankylosaurus", "pachycephalosaurus", "deinonychus",
    "utahraptor", "diplodocus", "gallimimus", "oviraptor", "therizinosaurus",
    "compsognathus", "dimetrodon", "smilodon", "mammoth", "pteranodon",
    "quetzalcoatlus", "archaeopteryx", "rhamphorhynchus", "pterodactyl",
    "pterodactylus", "pterosaur", "dimorphodon", "liopleurodon", "ammonite",
    "plesiosaurus", "mosasaurus", "ichthyosaurus", "megalodon", "elasmosaurus",
    "kronosaurus", "pliosaurus", "dunkleosteus", "nautilus", "shark", "whale",
    "lepidodendron", "trilobite", "anomalocaris", "meganeura", "arthropleura",
    "pulmonoscorpius",
], key=len, reverse=True)


def _slugify(text: str) -> str:
    """Turn arbitrary text (e.g. a products.json title) into a clean SEO slug."""
    words = re.split(r"[^a-z0-9]+", text.lower())
    words = [w for w in words if w and w not in FILLER and not re.fullmatch(r"\d+", w)]
    slug = "-".join(words[:6])
    return re.sub(r"-+", "-", slug).strip("-")


def _load_titles() -> dict:
    """Map basename -> title from products.json (curated titles for MJ-CDN drops)."""
    titles = {}
    if PRODUCTS_JSON.exists():
        try:
            for entry in json.loads(PRODUCTS_JSON.read_text("utf-8")):
                fname, title = entry.get("filename"), entry.get("title")
                if fname and title:
                    titles[Path(fname).name] = title
        except (json.JSONDecodeError, OSError):
            pass
    return titles


def _make_seo_slug(path: Path, titles: dict | None = None) -> str:
    titles = titles or {}
    # Split on dots too — MJ CDN names like "httpss.mj.run" would otherwise stay a
    # single opaque token and yield a slug identical to the raw stem (a silent no-op).
    stem = UUID_PATTERN.sub("", path.stem)
    words = re.split(r"[_\-\s.]+", stem.lower())
    descriptive = [w for w in words if w and w not in FILLER and not re.fullmatch(r"\d+", w)]

    haystack = " ".join(descriptive)
    sp = next((k for k in _SPECIES_KEYS if k in haystack), None)

    # MJ-CDN drops carry no species token; derive from the curated title instead.
    if not sp and (MJ_CDN_RE.search(path.name) or path.name in titles):
        title_slug = _slugify(titles.get(path.name, ""))
        if _SLUG_RE.match(title_slug):
            return title_slug

    if sp:
        sp_words = sp.split()
        extra = [w for w in descriptive if w not in sp_words]
        slug_words = sp_words + extra[:3]
    else:
        slug_words = descriptive[:6]

    slug = "-".join(slug_words[:6])
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "prehistoric-art"


def rename_slugs(folder: Path, titles: dict | None = None) -> int:
    """Rename non-slug image files in folder. Returns count renamed."""
    renamed = 0
    for p in sorted(folder.iterdir()):
        if not p.is_file() or p.name.startswith("."):
            continue
        if p.suffix.lower() not in IMAGE_EXTS:
            continue
        if _SLUG_RE.match(p.stem):
            continue
        slug = _make_seo_slug(p, titles)
        new_name = slug + p.suffix.lower()
        new_path = folder / new_name
        counter = 1
        while new_path.exists() and new_path != p:
            new_name = f"{slug}-{counter}{p.suffix.lower()}"
            new_path = folder / new_name
            counter += 1
        if new_path != p:
            p.rename(new_path)
            print(f"  {p.name}  →  {new_name}")
            renamed += 1
    return renamed


def main():
    if len(sys.argv) > 1:
        dirs = [Path(d) for d in sys.argv[1:]]
    else:
        dirs = sorted(d for d in GALLERY_DIR.iterdir() if d.is_dir() and not d.name.startswith("."))

    titles = _load_titles()
    total = 0
    for d in dirs:
        if d.is_dir():
            n = rename_slugs(d, titles)
            total += n
    if total:
        print(f"slug_rename: {total} file(s) renamed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

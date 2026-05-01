#!/usr/bin/env python3
# Sync site/src/data/products.json with files in site/src/assets/gallery/.
# - Adds entries for new images and videos
# - Removes entries for files that no longer exist
# - Idempotent (safe to run repeatedly)
# - Emits SEO-rich metadata: alt, description, keywords, scientific_name, era

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "site" / "src" / "assets" / "gallery"
PRODUCTS_JSON = ROOT / "site" / "src" / "data" / "products.json"
REFS_BEST_DIR = ROOT / "refs" / "gallery_best"

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
VIDEO_EXTS = {".mp4", ".webm", ".mov"}

# Categories are derived from the subfolder under site/src/assets/gallery/.
# horizontal/ and vertical/ are "best-of" website display folders — images dropped
# there are also mirrored into refs/gallery_best/ to seed future MJ --sref pools.
CATEGORIES = {"predators", "herbivores", "marine", "aerial", "flora_arthropods",
               "horizontal", "vertical"}

# Categories whose images feed back into refs/gallery_best/ for --sref reuse.
REFS_MIRROR_CATEGORIES = {"horizontal", "vertical"}

# Species metadata supplies scientific_name / era / traits per species.
# Category is no longer set here — it comes from the file's subfolder.
SPECIES_META = {
    "tyrannosaurus rex":   {"scientific_name": "Tyrannosaurus rex",     "era": "Late Cretaceous",   "traits": "apex theropod predator with massive jaws and binocular vision"},
    "tyrannosaurus":       {"scientific_name": "Tyrannosaurus rex",     "era": "Late Cretaceous",   "traits": "apex theropod predator with massive jaws and binocular vision"},
    "t-rex":               {"scientific_name": "Tyrannosaurus rex",     "era": "Late Cretaceous",   "traits": "apex theropod predator with massive jaws and binocular vision"},
    "t rex":               {"scientific_name": "Tyrannosaurus rex",     "era": "Late Cretaceous",   "traits": "apex theropod predator with massive jaws and binocular vision"},
    "trex":                {"scientific_name": "Tyrannosaurus rex",     "era": "Late Cretaceous",   "traits": "apex theropod predator with massive jaws and binocular vision"},
    "triceratops":         {"scientific_name": "Triceratops horridus",  "era": "Late Cretaceous",   "traits": "three-horned ceratopsian herbivore with a bony neck frill"},
    "stegosaurus":         {"scientific_name": "Stegosaurus stenops",   "era": "Late Jurassic",     "traits": "plated herbivore with dorsal plates and a thagomizer tail"},
    "velociraptor":        {"scientific_name": "Velociraptor mongoliensis", "era": "Late Cretaceous", "traits": "feathered dromaeosaurid raptor with a sickle claw"},
    "carnotaurus":         {"scientific_name": "Carnotaurus sastrei",   "era": "Late Cretaceous",   "traits": "horned abelisaurid theropod with a powerful tail"},
    "dilophosaurus":       {"scientific_name": "Dilophosaurus wetherilli", "era": "Early Jurassic", "traits": "double-crested early theropod predator"},
    "brachiosaurus":       {"scientific_name": "Brachiosaurus altithorax", "era": "Late Jurassic",  "traits": "long-necked sauropod with elevated forelimbs"},
    "allosaurus":          {"scientific_name": "Allosaurus fragilis",   "era": "Late Jurassic",     "traits": "large carnosaurian apex predator"},
    "spinosaurus":         {"scientific_name": "Spinosaurus aegyptiacus", "era": "Cretaceous",       "traits": "semi-aquatic theropod with a sail-backed spine"},
    "apatosaurus":         {"scientific_name": "Apatosaurus louisae",   "era": "Late Jurassic",     "traits": "massive sauropod with a whip-like tail"},
    "iguanodon":           {"scientific_name": "Iguanodon bernissartensis", "era": "Early Cretaceous", "traits": "thumb-spiked ornithopod herbivore"},
    "parasaurolophus":     {"scientific_name": "Parasaurolophus walkeri", "era": "Late Cretaceous",  "traits": "tube-crested hadrosaur"},
    "ankylosaurus":        {"scientific_name": "Ankylosaurus magniventris", "era": "Late Cretaceous", "traits": "armored thyreophoran with a clubbed tail"},
    "pachycephalosaurus":  {"scientific_name": "Pachycephalosaurus wyomingensis", "era": "Late Cretaceous", "traits": "dome-skulled bipedal herbivore"},
    "deinonychus":         {"scientific_name": "Deinonychus antirrhopus", "era": "Early Cretaceous", "traits": "feathered dromaeosaurid raptor"},
    "utahraptor":          {"scientific_name": "Utahraptor ostrommaysorum", "era": "Early Cretaceous", "traits": "giant feathered raptor with a sickle claw"},
    "diplodocus":          {"scientific_name": "Diplodocus carnegii",   "era": "Late Jurassic",     "traits": "extreme long-necked sauropod"},
    "gallimimus":          {"scientific_name": "Gallimimus bullatus",   "era": "Late Cretaceous",   "traits": "ostrich-like ornithomimid"},
    "oviraptor":           {"scientific_name": "Oviraptor philoceratops", "era": "Late Cretaceous", "traits": "crested feathered theropod"},
    "therizinosaurus":     {"scientific_name": "Therizinosaurus cheloniformis", "era": "Late Cretaceous", "traits": "scythe-clawed feathered theropod"},
    "compsognathus":       {"scientific_name": "Compsognathus longipes", "era": "Late Jurassic",    "traits": "diminutive coelurosaurid theropod"},
    "dimetrodon":          {"scientific_name": "Dimetrodon limbatus",   "era": "Early Permian",     "traits": "sail-backed synapsid predator"},
    "smilodon":            {"scientific_name": "Smilodon fatalis",      "era": "Pleistocene",       "traits": "saber-toothed cat predator"},
    "mammoth":             {"scientific_name": "Mammuthus primigenius", "era": "Pleistocene",       "traits": "wooly tusked proboscidean"},
    "herbivorous":         {"scientific_name": "Dinosauria",            "era": "Mesozoic",           "traits": "plant-eating ornithischian"},
    "dinosaur":            {"scientific_name": "Dinosauria",            "era": "Mesozoic",           "traits": "prehistoric reptilian fauna"},
    "dino":                {"scientific_name": "Dinosauria",            "era": "Mesozoic",           "traits": "prehistoric reptilian fauna"},

    "pteranodon":          {"scientific_name": "Pteranodon longiceps",   "era": "Late Cretaceous",   "traits": "toothless crested pterosaur"},
    "quetzalcoatlus":      {"scientific_name": "Quetzalcoatlus northropi", "era": "Late Cretaceous", "traits": "azhdarchid pterosaur with a 10-meter wingspan"},
    "archaeopteryx":       {"scientific_name": "Archaeopteryx lithographica", "era": "Late Jurassic", "traits": "transitional feathered avialan"},
    "rhamphorhynchus":     {"scientific_name": "Rhamphorhynchus muensteri", "era": "Late Jurassic",  "traits": "long-tailed pterosaur with needle teeth"},
    "pterodactyl":         {"scientific_name": "Pterodactylus antiquus", "era": "Late Jurassic",     "traits": "short-tailed pterodactyloid pterosaur"},
    "pterodactylus":       {"scientific_name": "Pterodactylus antiquus", "era": "Late Jurassic",     "traits": "short-tailed pterodactyloid pterosaur"},
    "pterosaur":           {"scientific_name": "Pterosauria",            "era": "Mesozoic",           "traits": "flying archosaur with membranous wings"},
    "dimorphodon":         {"scientific_name": "Dimorphodon macronyx",   "era": "Early Jurassic",    "traits": "puffin-faced early pterosaur"},

    "liopleurodon":        {"scientific_name": "Liopleurodon ferox",     "era": "Middle to Late Jurassic", "traits": "short-necked apex pliosaur"},
    "ammonite":            {"scientific_name": "Ammonoidea",             "era": "Devonian to Cretaceous",   "traits": "spiral-shelled cephalopod mollusk"},
    "plesiosaurus":        {"scientific_name": "Plesiosaurus dolichodeirus", "era": "Early Jurassic",      "traits": "long-necked plesiosaur marine reptile"},
    "mosasaurus":          {"scientific_name": "Mosasaurus hoffmannii",  "era": "Late Cretaceous",   "traits": "apex marine lizard predator"},
    "ichthyosaurus":       {"scientific_name": "Ichthyosaurus communis", "era": "Early Jurassic",    "traits": "dolphin-shaped marine reptile"},
    "megalodon":           {"scientific_name": "Otodus megalodon",       "era": "Miocene to Pliocene", "traits": "massive macropredatory shark"},
    "elasmosaurus":        {"scientific_name": "Elasmosaurus platyurus", "era": "Late Cretaceous",   "traits": "extreme long-necked plesiosaur"},
    "kronosaurus":         {"scientific_name": "Kronosaurus queenslandicus", "era": "Early Cretaceous", "traits": "giant short-necked pliosaur"},
    "pliosaurus":          {"scientific_name": "Pliosaurus brachydeirus", "era": "Late Jurassic",    "traits": "short-necked apex pliosaur"},
    "dunkleosteus":        {"scientific_name": "Dunkleosteus terrelli",  "era": "Late Devonian",     "traits": "armored placoderm apex predator"},
    "nautilus":            {"scientific_name": "Nautilidae",             "era": "Cambrian to Recent", "traits": "chambered cephalopod mollusk"},
    "shark":               {"scientific_name": "Selachimorpha",          "era": "Devonian to Recent", "traits": "cartilaginous marine predator"},
    "whale":               {"scientific_name": "Cetacea",                "era": "Eocene to Recent",  "traits": "marine mammal cetacean"},

    "lepidodendron":       {"scientific_name": "Lepidodendron",  "era": "Carboniferous",   "traits": "towering scale tree lycopsid"},
    "trilobite":           {"scientific_name": "Trilobita",      "era": "Cambrian to Permian", "traits": "segmented marine arthropod"},
    "anomalocaris":        {"scientific_name": "Anomalocaris canadensis", "era": "Cambrian", "traits": "early apex predatory arthropod"},
    "meganeura":           {"scientific_name": "Meganeura monyi", "era": "Late Carboniferous", "traits": "giant griffinfly with 65 cm wingspan"},
    "arthropleura":        {"scientific_name": "Arthropleura armata", "era": "Late Carboniferous", "traits": "two-meter-long giant millipede"},
    "pulmonoscorpius":     {"scientific_name": "Pulmonoscorpius kirktonensis", "era": "Carboniferous", "traits": "giant terrestrial scorpion"},
    "dragonfly":           {"scientific_name": "Odonata",        "era": "Carboniferous to Recent", "traits": "predatory winged insect"},
    "scorpion":            {"scientific_name": "Scorpiones",     "era": "Silurian to Recent", "traits": "venomous arachnid arthropod"},
    "millipede":           {"scientific_name": "Diplopoda",      "era": "Silurian to Recent", "traits": "many-legged detritivore arthropod"},
    "centipede":           {"scientific_name": "Chilopoda",      "era": "Silurian to Recent", "traits": "venomous predatory myriapod"},
    "fern":                {"scientific_name": "Polypodiopsida", "era": "Devonian to Recent", "traits": "non-flowering vascular plant"},
    "cycad":               {"scientific_name": "Cycadophyta",    "era": "Permian to Recent", "traits": "seed-bearing gymnosperm"},
    "mushroom":            {"scientific_name": "Fungi",          "era": "Devonian to Recent", "traits": "fruiting body of fungi"},
    "magnolia":            {"scientific_name": "Magnoliaceae",   "era": "Cretaceous to Recent", "traits": "early flowering angiosperm"},
    "bloom":               {"scientific_name": "Angiospermae",   "era": "Cretaceous to Recent", "traits": "flowering plant"},
    "flower":              {"scientific_name": "Angiospermae",   "era": "Cretaceous to Recent", "traits": "flowering plant"},
    "tree":                {"scientific_name": "Tracheophyta",   "era": "Devonian to Recent", "traits": "vascular plant"},
    "forest":              {"scientific_name": "Tracheophyta",   "era": "Devonian to Recent", "traits": "prehistoric forest scene"},
    "lycopsid":            {"scientific_name": "Lycopodiopsida", "era": "Silurian to Recent", "traits": "ancient lycophyte plant"},
    "conifer":             {"scientific_name": "Pinophyta",      "era": "Carboniferous to Recent", "traits": "cone-bearing gymnosperm"},
}

UUID_PATTERN = re.compile(r"_[a-f0-9]{8,}(-[a-f0-9-]+)?$")
FILLER = {
    "spootscupertino", "the", "of", "with", "and", "a", "an", "in", "on",
    "at", "to", "from", "macro", "extreme", "massive", "large", "small",
    "huge", "feathered", "scientifically", "accurate", "image", "generated",
    "gemini", "close", "up", "deta", "details", "photo", "render",
}

DEFAULT_META = {"scientific_name": "Dinosauria", "era": "Mesozoic", "traits": "prehistoric creature"}

CATEGORY_LABELS = {
    "predators": "Predators",
    "herbivores": "Herbivores",
    "aerial": "Aerial Paleoart",
    "marine": "Marine Paleoart",
    "flora_arthropods": "Prehistoric Flora and Arthropods",
    "horizontal": "Best Of — Landscape",
    "vertical": "Best Of — Portrait",
}


def species_for(filename: str, title: str = ""):
    # filename may be a relative path like "predators/foo.png" — only the basename matters.
    stem = UUID_PATTERN.sub("", Path(filename).name.rsplit(".", 1)[0].lower()).replace("-", " ").replace("_", " ")
    haystack = f"{stem} {title.lower()}"
    for sp in sorted(SPECIES_META.keys(), key=len, reverse=True):
        if sp in haystack:
            return sp, SPECIES_META[sp]
    return None, DEFAULT_META


def derive_title(filename: str) -> str:
    stem = UUID_PATTERN.sub("", Path(filename).stem.lower())
    sp, meta = species_for(filename)
    if sp:
        common = sp.title().replace("T-Rex", "T. rex").replace("T Rex", "T. rex")
        common = re.sub(r"\bRex\b", "rex", common)
        return common
    words = re.split(r"[_\-\s]+", stem)
    words = [w for w in words if w and w not in FILLER and not re.fullmatch(r"\d+", w)]
    if not words:
        return Path(filename).stem
    return " ".join(words[:3]).title()


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def derive_alt(title: str, meta: dict) -> str:
    art = _article(meta["traits"])
    return (
        f"Scientifically accurate paleoart of {meta['scientific_name']}, "
        f"{art} {meta['traits']} from the {meta['era']}, "
        f"rendered in cinematic prehistoric detail."
    )


def derive_description(title: str, meta: dict) -> str:
    return (
        f"{title} — fine-art paleoart print depicting {meta['scientific_name']}, "
        f"{meta['traits']}, native to the {meta['era']}. "
        f"Museum-quality dinosaur wall art for collectors and natural-history enthusiasts."
    )


def derive_keywords(title: str, meta: dict) -> list:
    base = [
        "paleoart",
        "dinosaur art",
        "prehistoric art",
        "natural history illustration",
        "wall art print",
        meta["scientific_name"],
        meta["era"],
        meta["traits"].split(",")[0],
        title,
    ]
    seen, out = set(), []
    for k in base:
        kl = k.lower()
        if kl and kl not in seen:
            seen.add(kl)
            out.append(k)
    return out


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


def build_entry(rel_path: str, category: str, dims: tuple, entry_type: str, existing=None) -> dict:
    sp, meta = species_for(rel_path, (existing or {}).get("title", ""))
    title = (existing or {}).get("title") or derive_title(rel_path)
    return {
        "filename": rel_path,
        "title": title,
        "width": dims[0],
        "height": dims[1],
        "type": entry_type,
        "category": category,
        "scientific_name": meta["scientific_name"],
        "era": meta["era"],
        "alt": derive_alt(title, meta),
        "description": derive_description(title, meta),
        "keywords": derive_keywords(title, meta),
    }


def main() -> int:
    if not ASSETS_DIR.is_dir():
        print(f"ERROR: {ASSETS_DIR} not found", file=sys.stderr)
        return 2

    existing_by_fname = {}
    if PRODUCTS_JSON.exists():
        try:
            for entry in json.loads(PRODUCTS_JSON.read_text()):
                fname = entry.get("filename")
                if fname:
                    existing_by_fname[fname] = entry
        except json.JSONDecodeError:
            print("WARNING: products.json was malformed; starting fresh.", file=sys.stderr)

    # Walk one level deep — files must live inside a category subfolder.
    found = []
    for category_dir in sorted(ASSETS_DIR.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith("."):
            continue
        if category_dir.name not in CATEGORIES:
            print(f"WARNING: skipping unknown category folder '{category_dir.name}/' "
                  f"(allowed: {sorted(CATEGORIES)})", file=sys.stderr)
            continue
        for p in category_dir.iterdir():
            if not p.is_file() or p.name.startswith("."):
                continue
            if p.suffix.lower() not in (IMAGE_EXTS | VIDEO_EXTS):
                continue
            found.append((category_dir.name, p))

    # Warn about loose files at the gallery root (won't be synced).
    for p in ASSETS_DIR.iterdir():
        if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in (IMAGE_EXTS | VIDEO_EXTS):
            print(f"WARNING: '{p.name}' is at gallery root; move it into a category subfolder.",
                  file=sys.stderr)

    by_fname = {}
    for category, path in found:
        rel_path = f"{category}/{path.name}"
        ext = path.suffix.lower()
        if ext in IMAGE_EXTS:
            dims = get_image_dims(path) or (1024, 1024)
            entry_type = "image"
        else:
            dims = get_video_dims(path)
            entry_type = "video"
        existing = existing_by_fname.get(rel_path) or existing_by_fname.get(path.name)
        # Re-derive SEO fields each run; preserve manual title overrides.
        # Category is always taken from the subfolder, not from existing.
        by_fname[rel_path] = build_entry(rel_path, category, dims, entry_type, existing)

    products = sorted(
        by_fname.values(),
        key=lambda e: (ASSETS_DIR / e["filename"]).stat().st_mtime,
        reverse=True,
    )

    new_json = json.dumps(products, indent=2, ensure_ascii=False) + "\n"
    if PRODUCTS_JSON.exists() and PRODUCTS_JSON.read_text() == new_json:
        print(f"sync_gallery: no changes ({len(products)} pieces).")
        return 0

    PRODUCTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    PRODUCTS_JSON.write_text(new_json)
    added = len(set(by_fname) - set(existing_by_fname))
    removed = len(set(existing_by_fname) - set(by_fname))
    print(f"sync_gallery: wrote {len(products)} pieces (+{added} new, -{removed} removed).")

    # Mirror horizontal/ and vertical/ images into refs/gallery_best/ so they
    # become available as --sref candidates for future Midjourney generations.
    refs_mirrored = 0
    for category, path in found:
        if category not in REFS_MIRROR_CATEGORIES:
            continue
        dest_dir = REFS_BEST_DIR / category
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / path.name
        if not dest.exists() or dest.stat().st_mtime < path.stat().st_mtime:
            shutil.copy2(str(path), str(dest))
            refs_mirrored += 1
    if refs_mirrored:
        print(f"sync_gallery: mirrored {refs_mirrored} image(s) → refs/gallery_best/")

    return 0


if __name__ == "__main__":
    sys.exit(main())

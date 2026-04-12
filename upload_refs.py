#!/usr/bin/env python3
"""Download reference images from source catalog and upload to Discord for MJ --sref.

Workflow:
    1. sref_sources.json  -- Wikimedia Commons URLs (source catalog)
    2. reference_images/   -- downloaded images (local cache)
    3. Discord webhook     -- upload images -> get CDN URLs
    4. sref_urls.json      -- Discord CDN URLs (used by generate_prompt.py --sref)

Usage:
    # Download all source images into reference_images/:
    python3 upload_refs.py download

    # Upload all downloaded images to Discord and wire CDN URLs:
    python3 upload_refs.py all

    # Download + upload in one step:
    python3 upload_refs.py sync

    # Upload a single image with a category tag:
    python3 upload_refs.py upload --file photo.jpg --category waterhole

    # List what's already uploaded:
    python3 upload_refs.py list
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR / ".env"
SREF_PATH = SCRIPT_DIR / "sref_urls.json"
SOURCES_PATH = SCRIPT_DIR / "sref_sources.json"
REF_DIR = SCRIPT_DIR / "reference_images"

# Category -> which species benefit from this reference
CATEGORY_SPECIES_MAP = {
    "waterhole": [
        "Stegosaurus", "Triceratops", "Ankylosaurus", "Brachiosaurus",
        "Parasaurolophus", "Tyrannosaurus rex",
    ],
    "migration": [
        "Parasaurolophus", "Brachiosaurus", "Triceratops", "Stegosaurus",
        "Ankylosaurus",
    ],
    "family": [
        "Tyrannosaurus rex", "Triceratops", "Stegosaurus", "Brachiosaurus",
        "Parasaurolophus", "Ankylosaurus", "Velociraptor",
    ],
    "crocodile": [
        "Tyrannosaurus rex", "Spinosaurus", "Mosasaurus", "Kronosaurus",
        "Liopleurodon", "Dilophosaurus",
    ],
    "feathered_biped": [
        "Tyrannosaurus rex", "Velociraptor", "Dilophosaurus",
    ],
    "tall_predator": [
        "Velociraptor", "Dilophosaurus", "Tyrannosaurus rex",
    ],
    "komodo": [
        "Tyrannosaurus rex", "Velociraptor", "Dilophosaurus",
        "Spinosaurus",
    ],
    "arthropod_group": [
        "Meganeura", "Arthropleura", "Jaekelopterus", "Pulmonoscorpius",
        "Megarachne", "Anomalocaris", "Eurypterus", "Megalograptus",
    ],
    "tortoise_group": [
        "Ankylosaurus", "Archelon", "Stegosaurus", "Triceratops",
    ],
    "raptor_flight": [
        "Pteranodon", "Quetzalcoatlus", "Rhamphorhynchus", "Dimorphodon",
    ],
    "marine": [
        "Mosasaurus", "Kronosaurus", "Liopleurodon", "Elasmosaurus",
        "Ichthyosaurus", "Megalodon", "Cretoxyrhina", "Helicoprion",
        "Dunkleosteus", "Xiphactinus", "Leedsichthys", "Archelon",
    ],
    "sea_scorpion": [
        "Eurypterus", "Jaekelopterus", "Megalograptus", "Anomalocaris",
    ],
    "paleo_plant": [
        "Araucaria", "Calamites", "Lepidodendron", "Sigillaria",
        "Archaefructus", "Glossopteris", "Wattieza", "Williamsonia",
    ],
    "ammonite": [
        "Ammonite",
    ],
}


def load_webhook_url():
    """Read DISCORD_WEBHOOK_URL from .env file."""
    if not ENV_PATH.exists():
        sys.exit("No .env file found. Add DISCORD_WEBHOOK_URL to .env")
    for line in ENV_PATH.read_text().splitlines():
        if line.startswith("DISCORD_WEBHOOK_URL="):
            return line.split("=", 1)[1].strip()
    sys.exit("DISCORD_WEBHOOK_URL not found in .env")


def load_sources():
    """Load sref_sources.json (Wikimedia source URLs keyed by species)."""
    if not SOURCES_PATH.exists():
        return {}
    with open(SOURCES_PATH) as f:
        return json.load(f)


def build_source_download_list():
    """Build flat list of {label, url, category, filename} from sref_sources.json.

    Deduplicates by URL.  Assigns each image to the first matching category
    from the species that references it.
    """
    sources = load_sources()
    if not sources:
        print("No sref_sources.json found. Nothing to download.")
        return []

    # Reverse map: species -> categories
    species_to_cats = {}
    for cat, sp_list in CATEGORY_SPECIES_MAP.items():
        for sp in sp_list:
            species_to_cats.setdefault(sp, []).append(cat)

    # Collect unique URLs with their best category assignment
    seen_urls = {}
    for species, entries in sources.items():
        cats = species_to_cats.get(species, [])
        for entry in entries:
            url = entry["url"] if isinstance(entry, dict) else entry
            label = entry.get("label", "ref") if isinstance(entry, dict) else "ref"
            if url not in seen_urls:
                best_cat = cats[0] if cats else "uncategorized"
                # Derive filename from URL
                fname = url.rsplit("/", 1)[-1]
                try:
                    fname = urllib.request.url2pathname(fname)
                except Exception:
                    pass
                fname = fname.replace("/", "_").replace("\\", "_")
                if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                    fname += ".jpg"
                seen_urls[url] = {
                    "label": label,
                    "url": url,
                    "category": best_cat,
                    "filename": fname,
                }

    return list(seen_urls.values())


def upload_to_discord(webhook_url, filepath, category):
    """Upload an image to Discord via webhook, return the CDN URL."""
    boundary = "----DinoArtRefBoundary"
    filename = filepath.name
    ct = "image/jpeg" if filepath.suffix.lower() in (".jpg", ".jpeg") else "image/png"

    payload_json = json.dumps({
        "content": "[dino_art ref] category: %s | file: %s" % (category, filename)
    })

    body = []
    body.append(("--%s" % boundary).encode())
    body.append(b'Content-Disposition: form-data; name="payload_json"')
    body.append(b"Content-Type: application/json")
    body.append(b"")
    body.append(payload_json.encode())
    body.append(("--%s" % boundary).encode())
    body.append(('Content-Disposition: form-data; name="file"; filename="%s"' % filename).encode())
    body.append(("Content-Type: %s" % ct).encode())
    body.append(b"")
    body.append(filepath.read_bytes())
    body.append(("--%s--" % boundary).encode())

    body_bytes = b"\r\n".join(body)

    req = urllib.request.Request(
        webhook_url + "?wait=true",
        data=body_bytes,
        method="POST",
        headers={
            "Content-Type": "multipart/form-data; boundary=%s" % boundary,
            "User-Agent": "DinoArtRefUploader/1.0",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            if data.get("attachments"):
                return data["attachments"][0]["url"]
            else:
                print("  WARNING: No attachment in response for %s" % filename)
                return ""
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print("  ERROR uploading %s: %s -- %s" % (filename, e.code, error_body))
        return ""


def load_sref():
    if SREF_PATH.exists():
        return json.loads(SREF_PATH.read_text())
    return {}


def save_sref(data):
    SREF_PATH.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def add_url_to_sref(sref, category, url, label):
    """Add a URL to all species that benefit from this category."""
    species_list = CATEGORY_SPECIES_MAP.get(category, [])
    entry = {"label": label, "url": url}

    for sp in species_list:
        if sp not in sref:
            sref[sp] = []
        existing_urls = set()
        for e in sref[sp]:
            if isinstance(e, dict):
                existing_urls.add(e.get("url", ""))
            elif isinstance(e, str):
                existing_urls.add(e)
        if url not in existing_urls:
            sref[sp].append(entry)


def get_uploaded_urls(sref):
    """Get all URLs already in sref_urls.json."""
    urls = set()
    for entries in sref.values():
        if isinstance(entries, list):
            for e in entries:
                if isinstance(e, dict):
                    urls.add(e.get("url", ""))
                elif isinstance(e, str):
                    urls.add(e)
    return urls


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_download(args):
    """Download source images from sref_sources.json into reference_images/."""
    items = build_source_download_list()
    if not items:
        return

    total = 0
    skipped = 0
    failed = 0

    for item in items:
        cat_dir = REF_DIR / item["category"]
        cat_dir.mkdir(parents=True, exist_ok=True)
        dest = cat_dir / item["filename"]

        if dest.exists():
            skipped += 1
            continue

        print("  Downloading: %s" % item["label"])
        print("    -> %s" % dest.relative_to(SCRIPT_DIR))

        try:
            req = urllib.request.Request(
                item["url"],
                headers={"User-Agent": "DinoArtStudio/1.0 (reference download)"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                dest.write_bytes(resp.read())
            total += 1
            time.sleep(1.0)  # Rate limit courtesy
        except Exception as ex:
            print("    FAILED: %s" % str(ex)[:80])
            failed += 1
            time.sleep(2.0)

    print("\nDownload complete: %d new, %d skipped, %d failed" % (total, skipped, failed))


def cmd_upload_single(args):
    filepath = Path(args.file).resolve()
    if not filepath.exists():
        sys.exit("File not found: %s" % filepath)

    webhook_url = load_webhook_url()
    sref = load_sref()

    print("Uploading %s [%s]..." % (filepath.name, args.category))
    url = upload_to_discord(webhook_url, filepath, args.category)
    if url:
        print("  CDN URL: %s" % url)
        add_url_to_sref(sref, args.category, url, "%s/%s" % (args.category, filepath.name))
        save_sref(sref)
        print("  Saved to sref_urls.json")
    else:
        print("  Upload failed.")


def cmd_upload_all(args):
    if not REF_DIR.exists():
        sys.exit("No reference_images/ directory found at %s" % REF_DIR)

    webhook_url = load_webhook_url()
    sref = load_sref()

    total = 0
    skipped = 0

    for category_dir in sorted(REF_DIR.iterdir()):
        if not category_dir.is_dir():
            continue
        category = category_dir.name
        if category not in CATEGORY_SPECIES_MAP:
            print("Skipping unknown category: %s" % category)
            continue

        images = sorted([
            f for f in category_dir.iterdir()
            if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
        ])

        if not images:
            continue

        print("\n[%s] -- %d image(s)" % (category, len(images)))
        for img in images:
            existing_labels = set()
            for sp in CATEGORY_SPECIES_MAP.get(category, []):
                for e in sref.get(sp, []):
                    if isinstance(e, dict):
                        existing_labels.add(e.get("label", ""))

            label = "%s/%s" % (category, img.name)
            if label in existing_labels:
                print("  SKIP (already uploaded): %s" % img.name)
                skipped += 1
                continue

            print("  Uploading %s..." % img.name)
            url = upload_to_discord(webhook_url, img, category)
            if url:
                add_url_to_sref(sref, category, url, label)
                total += 1
            else:
                print("  FAILED: %s" % img.name)

            time.sleep(1.0)  # Discord rate limit courtesy

    save_sref(sref)
    print("\nDone. Uploaded %d images, skipped %d." % (total, skipped))


def cmd_sync(args):
    """Download from sources, then upload to Discord -- full pipeline."""
    print("=== STEP 1: Download from sref_sources.json ===\n")
    cmd_download(args)
    print("\n=== STEP 2: Upload to Discord ===\n")
    cmd_upload_all(args)
    print("\n=== SYNC COMPLETE ===")
    sref = load_sref()
    covered = sum(1 for v in sref.values() if v)
    total_urls = sum(len(v) for v in sref.values())
    print("Species with refs: %d/42" % covered)
    print("Total CDN URLs: %d" % total_urls)


def cmd_list(args):
    sref = load_sref()
    total = 0
    for sp, entries in sorted(sref.items()):
        if sp.startswith("_"):
            continue
        if not entries:
            continue
        print("\n%s:" % sp)
        for e in entries:
            if isinstance(e, dict):
                print("  [%s] %s" % (e.get("label", "?"), e.get("url", "?")))
            else:
                print("  %s" % e)
            total += 1
    if total == 0:
        print("No URLs in sref_urls.json yet.")
        print("Run: python3 upload_refs.py sync")
    else:
        print("\nTotal: %d entries" % total)


def main():
    parser = argparse.ArgumentParser(
        description="Download reference images and upload to Discord for MJ --sref"
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("download", help="Download source images from sref_sources.json")

    p_file = sub.add_parser("upload", help="Upload a single image")
    p_file.add_argument("--file", required=True, help="Path to image file")
    p_file.add_argument("--category", required=True,
                        choices=list(CATEGORY_SPECIES_MAP.keys()),
                        help="Reference category")

    sub.add_parser("all", help="Upload all new images from reference_images/")
    sub.add_parser("sync", help="Download sources + upload to Discord (full pipeline)")
    sub.add_parser("list", help="List all uploaded reference URLs")

    args = parser.parse_args()

    if args.command == "download":
        cmd_download(args)
    elif args.command == "upload":
        cmd_upload_single(args)
    elif args.command == "all":
        cmd_upload_all(args)
    elif args.command == "sync":
        cmd_sync(args)
    elif args.command == "list":
        cmd_list(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

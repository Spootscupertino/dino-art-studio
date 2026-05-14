#!/usr/bin/env python3
"""
Batch-ingest reference images from a JSON list of {url, filename, caption, source_type}.

Gemini (or any sourcing step) produces the JSON; this script handles:
  - Download from URL
  - Rename to the suggested filename
  - Drop into Training Drops/<species>/<source_type>/
  - Write matching .txt caption sidecar

Input JSON format (save as e.g. flux/ingest_batch.json):
  [
    {
      "url": "https://upload.wikimedia.org/...",
      "filename": "nile_crocodile_mouth_gumline.jpg",
      "caption": "Nile crocodile open mouth showing recurved conical teeth anchored in exposed gumline, fleshy soft tissue visible along jaw margin, tongue and palate detail, high resolution",
      "source_type": "living_analog",
      "species": "tyrannosaurus",
      "license": "CC BY-SA 4.0"
    },
    ...
  ]

source_type options (determines subfolder):
  living_analog     — extant animal anatomy references
  skeletal          — fossil skeletal mounts
  paleoart          — scientific reconstructions
  integument        — skin/scale/texture refs
  corrected_mj      — MJ self-generations with specific anatomy corrections

Usage:
  python3 flux/ingest_from_links.py flux/ingest_batch.json
  python3 flux/ingest_from_links.py flux/ingest_batch.json --dry-run
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

DROPS_ROOT = Path("/Users/ericeldridge/Desktop/Training Drops")
REPO_ROOT = Path(__file__).resolve().parent.parent

VALID_SOURCE_TYPES = {"living_analog", "skeletal", "paleoart", "integument", "corrected_mj"}


def download(url: str, dest: Path, dry_run: bool = False) -> bool:
    if dry_run:
        print(f"    [dry-run] would download {url} → {dest}")
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            dest.write_bytes(r.read())
        return True
    except Exception as e:
        print(f"    ERROR downloading {url}: {e}")
        return False


def ingest_batch(batch_path: Path, dry_run: bool):
    entries = json.loads(batch_path.read_text())
    print(f"Ingesting {len(entries)} images from {batch_path.name}")
    if dry_run:
        print("(dry-run mode — no files written)\n")

    ok = skipped = failed = 0
    for entry in entries:
        url = entry.get("url", "").strip()
        filename = entry.get("filename", "").strip()
        caption = entry.get("caption", "").strip()
        source_type = entry.get("source_type", "living_analog").strip()
        species = entry.get("species", "tyrannosaurus").strip()
        license_note = entry.get("license", "unknown")

        if not url or not filename:
            print(f"  SKIP — missing url or filename: {entry}")
            skipped += 1
            continue
        if source_type not in VALID_SOURCE_TYPES:
            print(f"  SKIP — unknown source_type '{source_type}' for {filename}")
            skipped += 1
            continue
        if not caption:
            print(f"  WARN — no caption for {filename}, will write empty sidecar")

        dest_img = DROPS_ROOT / species / source_type / filename
        dest_txt = dest_img.with_suffix(".txt")

        if dest_img.exists():
            print(f"  SKIP — already exists: {dest_img.relative_to(DROPS_ROOT.parent)}")
            skipped += 1
            continue

        print(f"  {filename}  [{source_type}]  license={license_note}")
        if download(url, dest_img, dry_run):
            if not dry_run:
                caption_with_license = f"{caption}\n\n[source: {url}]\n[license: {license_note}]"
                dest_txt.write_text(caption_with_license)
                print(f"    ✓ saved + caption written")
            ok += 1
        else:
            failed += 1

    print(f"\nDone: {ok} ingested, {skipped} skipped, {failed} failed")
    if not dry_run and ok > 0:
        print(f"\nImages dropped to: {DROPS_ROOT}")
        print("Run flux/ingest_training_drops.py to move them into the training pool.")


def main():
    parser = argparse.ArgumentParser(description="Batch-ingest refs from JSON link list")
    parser.add_argument("batch_json", help="Path to JSON file with {url, filename, caption, source_type}")
    parser.add_argument("--dry-run", action="store_true", help="Preview without downloading")
    args = parser.parse_args()

    batch_path = Path(args.batch_json)
    if not batch_path.exists():
        sys.exit(f"File not found: {batch_path}")
    ingest_batch(batch_path, args.dry_run)


if __name__ == "__main__":
    main()

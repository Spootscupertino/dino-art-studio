#!/usr/bin/env python3
"""Sync paleoart_refs.json entries for one species into sref_urls.json.

Bridge between the paleoart catalog and the Discord-CDN cache that
generate_prompt.py actually consumes. upload_refs.py handles wildlife
refs (sref_sources.json) and broadcasts by category — that's wrong for
paleoart, which is species-specific.

Usage:
    python3 sync_paleoart.py "Tyrannosaurus rex"
    python3 sync_paleoart.py "Tyrannosaurus rex" --dry-run

Flow per species:
    1. Read its entries from paleoart_refs.json (Wikimedia URLs).
    2. Download each into reference_images/paleoart/.
    3. Upload each to Discord via webhook → CDN URL.
    4. Replace that species' "paleoart/*" entries in sref_urls.json.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import upload_refs

SCRIPT_DIR = Path(__file__).resolve().parent
PALEOART_REFS = SCRIPT_DIR / "paleoart_refs.json"
SREF_URLS = SCRIPT_DIR / "sref_urls.json"
PALEOART_DIR = SCRIPT_DIR / "reference_images" / "paleoart"


def load_paleoart_refs():
    return json.loads(PALEOART_REFS.read_text())


def download_one(url, dest):
    """Download via upload_refs._download_via_api (handles Wikimedia rate limits)."""
    if dest.exists() and dest.stat().st_size > 1000:
        return True
    PALEOART_DIR.mkdir(parents=True, exist_ok=True)
    return upload_refs._download_via_api(url, dest, width=1024)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("species", help='e.g. "Tyrannosaurus rex"')
    ap.add_argument("--dry-run", action="store_true", help="show plan, no Discord uploads, no file writes")
    args = ap.parse_args()

    species = args.species
    refs = load_paleoart_refs()
    if species not in refs:
        sys.exit(f"No entries for {species!r} in paleoart_refs.json")

    entries = refs[species]
    print(f"\n=== {species} ===")
    print(f"  {len(entries)} paleoart entries in catalog\n")

    # --- step 1: download ---
    files_to_upload = []
    for e in entries:
        label = e["label"]  # e.g. "paleoart/T_rex_witton_2013.png"
        url = e["url"]
        filename = label.split("/", 1)[-1]
        dest = PALEOART_DIR / filename
        print(f"  [download] {filename}")
        if args.dry_run:
            print(f"             (dry-run; skip)")
            files_to_upload.append((label, dest))
            continue
        ok = download_one(url, dest)
        if not ok:
            print(f"             FAILED to download {url}")
            continue
        files_to_upload.append((label, dest))

    if not files_to_upload:
        sys.exit("No files to upload.")

    if args.dry_run:
        print(f"\n  [dry-run] would upload {len(files_to_upload)} files to Discord")
        print(f"  [dry-run] would replace paleoart/* entries for {species!r} in sref_urls.json")
        return

    # --- step 2: upload to discord ---
    webhook = upload_refs.load_webhook_url()
    new_paleoart_entries = []
    for label, dest in files_to_upload:
        if not dest.exists():
            print(f"  [skip upload] {dest.name} missing on disk")
            continue
        print(f"  [upload] {dest.name}")
        cdn_url = upload_refs.upload_to_discord(webhook, dest, "paleoart")
        if not cdn_url:
            print(f"           FAILED")
            continue
        new_paleoart_entries.append({"label": label, "url": cdn_url})
        time.sleep(1.0)  # polite pacing for the webhook

    if not new_paleoart_entries:
        sys.exit("All Discord uploads failed.")

    # --- step 3: rewrite sref_urls.json for this species ---
    sref = json.loads(SREF_URLS.read_text())
    old_entries = sref.get(species, [])
    kept = [
        e for e in old_entries
        if not (isinstance(e, dict) and e.get("label", "").startswith("paleoart/"))
    ]
    sref[species] = kept + new_paleoart_entries
    SREF_URLS.write_text(json.dumps(sref, indent=2, sort_keys=True) + "\n")

    dropped = len(old_entries) - len(kept)
    print(f"\n  [sref] dropped {dropped} old paleoart entries")
    print(f"  [sref] added {len(new_paleoart_entries)} new paleoart entries")
    print(f"\nDone. Re-run the prompt generator for {species!r} to see the new --cref refs in action.\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
source_paleoart.py — find CC-licensed reference images for a species/category.

This is deterministic work: hits public APIs, filters by license, downloads to
a staging folder. No AI required. Called by the `source-hunter` subagent or
directly from the command line.

Usage:
    python3 tools/source_paleoart.py --species tyrannosaurus --category v5_forelimb_hand --limit 10
    python3 tools/source_paleoart.py --species triceratops --category v5_mouth_macro --source wikimedia,inaturalist

Sources (all CC-clean):
    - Wikimedia Commons API     https://commons.wikimedia.org/w/api.php
    - iNaturalist API           https://api.inaturalist.org/v1/observations
    - Smithsonian Open Access   https://api.si.edu/openaccess/api/v1.0/search
    - PLOS journals             scrape per article (CC BY 4.0)
    - PeerJ                     scrape per article (CC BY 4.0)
    - Flickr CC                 https://www.flickr.com/services/api/

Output:
    assets/staging/<species>/<category>/
        <filename>.{png,jpg}            (downloaded image)
        <filename>.json                  (sidecar with license, source_url, creator)
    assets/staging/<species>/<category>/_candidates.json   (manifest of this run)

The staging folder is git-ignored — review happens here before promotion to
`assets/gallery/flux/training_refs/<species>/<category>/`.
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STAGING_DIR = REPO_ROOT / "assets" / "staging"

# TODO(v6): implement Wikimedia search via Action=query with srnamespace=6 (File)
# TODO(v6): implement iNaturalist observation search with license filter
# TODO(v6): implement Smithsonian Open Access search via api.si.edu
# TODO(v6): implement PLOS/PeerJ figure scraping
# TODO(v6): implement pHash dedup against existing training_refs to avoid re-fetching

SOURCE_MODULES = {
    "wikimedia": "search_wikimedia",   # not yet implemented
    "inaturalist": "search_inaturalist",
    "smithsonian": "search_smithsonian",
    "plos": "search_plos",
    "peerj": "search_peerj",
    "flickr": "search_flickr_cc",
}

LICENSE_WHITELIST = {
    "CC0", "Public domain", "Public Domain",
    "CC BY 4.0", "CC BY 3.0", "CC BY 2.0",
    "CC BY-SA 4.0", "CC BY-SA 3.0",
    "CC BY-NC 4.0", "CC BY-NC-SA 4.0",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--species", required=True, help="e.g. tyrannosaurus")
    parser.add_argument("--category", required=True, help="e.g. v5_forelimb_hand")
    parser.add_argument("--limit", type=int, default=10, help="max candidates per source")
    parser.add_argument("--source", default="wikimedia,inaturalist,smithsonian",
                        help="comma-separated source names")
    args = parser.parse_args()

    sources = [s.strip() for s in args.source.split(",")]
    unknown = [s for s in sources if s not in SOURCE_MODULES]
    if unknown:
        sys.exit(f"Unknown source(s): {unknown}. Valid: {list(SOURCE_MODULES.keys())}")

    out_dir = STAGING_DIR / args.species / args.category
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[stub] Would search {sources} for {args.species}/{args.category}")
    print(f"[stub] Would write candidates to {out_dir.relative_to(REPO_ROOT)}")
    print(f"[stub] License whitelist: {sorted(LICENSE_WHITELIST)}")
    print()
    print("Not yet implemented. v6 work item.")
    print("Interface contract for downstream agents:")
    print("  - Writes <stem>.{png,jpg} and <stem>.json sidecars to staging/")
    print("  - Sidecar JSON includes: source_url, license, license_url, creator, ingested_at")
    print("  - Writes _candidates.json manifest with one entry per downloaded image")


if __name__ == "__main__":
    main()

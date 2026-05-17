#!/usr/bin/env python3
"""
dedup_refs.py — perceptual-hash deduplication for training reference images.

Catches near-duplicate refs that would otherwise inflate the training signal for
a single piece of source content (e.g., the same paleoart resized + reposted on
multiple sites).

Usage:
    python3 tools/dedup_refs.py --species tyrannosaurus               # report dupes only
    python3 tools/dedup_refs.py --species tyrannosaurus --quarantine  # auto-quarantine dupes (keeps highest-res)
    python3 tools/dedup_refs.py --against staging                     # check staging vs training_refs

Algorithm: pHash (perceptual hash via imagehash library), Hamming distance < 5 = near-dup.

Deliberate exception: horizontal mirrors (e.g. Steveoc Profile + mirror) are NOT
flagged as dupes — they're legitimate data augmentation. We detect mirrors by
also pHashing the horizontally-flipped version and treating that as a separate
signature.
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TRAINING_DIR = REPO_ROOT / "assets" / "gallery" / "flux" / "training_refs"
STAGING_DIR = REPO_ROOT / "assets" / "staging"

# TODO(v6): implement pHash via `imagehash` library (pip install imagehash Pillow)
# TODO(v6): handle horizontal mirror detection so it doesn't false-positive on Steveoc-style pairs
# TODO(v6): when --quarantine, keep the highest-resolution copy and mark the rest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--species", help="species folder to scan")
    parser.add_argument("--against", choices=["staging", "training"], default=None,
                        help="if 'staging': compare staging refs against existing training_refs to avoid re-fetching")
    parser.add_argument("--quarantine", action="store_true", help="auto-quarantine near-duplicates")
    parser.add_argument("--threshold", type=int, default=5, help="Hamming distance threshold")
    args = parser.parse_args()

    print(f"[stub] Would scan {args.species or 'all species'} for near-duplicates")
    print(f"[stub] Threshold: Hamming < {args.threshold}")
    print(f"[stub] Action: {'quarantine dupes' if args.quarantine else 'report only'}")
    print()
    print("Not yet implemented. v6 work item.")
    print("Interface contract:")
    print("  - Computes pHash + mirrored-pHash for every image")
    print("  - Groups by Hamming distance < threshold")
    print("  - Reports each group, retains highest-resolution copy")
    print("  - With --quarantine: writes quarantined: true to other copies' sidecar JSONs")


if __name__ == "__main__":
    main()

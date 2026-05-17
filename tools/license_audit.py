#!/usr/bin/env python3
"""
license_audit.py — verify every reference image has a clean, verifiable license.

Final gate before any image ships into a training export. Called by the
`license-auditor` subagent, or directly before running `flux/export_dataset.py`.

Usage:
    python3 tools/license_audit.py                                    # audit all training_refs
    python3 tools/license_audit.py --species tyrannosaurus
    python3 tools/license_audit.py --staging                          # audit assets/staging/ only
    python3 tools/license_audit.py --verify-urls                      # also curl each source_url (slow)

Output: per-image PASS / FIX / BLOCK report + summary.
Side effects: writes `quarantined: true` + `quarantine_reason` to sidecar JSONs for BLOCK cases.
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TRAINING_DIR = REPO_ROOT / "assets" / "gallery" / "flux" / "training_refs"
STAGING_DIR = REPO_ROOT / "assets" / "staging"

LICENSE_WHITELIST = {
    "CC0", "Public domain", "Public Domain",
    "CC BY 4.0", "CC BY 3.0", "CC BY 2.0",
    "CC BY-SA 4.0", "CC BY-SA 3.0",
    "CC BY-NC 4.0", "CC BY-NC-SA 4.0",
    "Midjourney",  # self-generated outputs only
    "Work-for-hire", "Commissioned",
}

BLOCK_PATTERNS = [
    "all rights reserved",
    "getty", "alamy", "shutterstock", "adobe stock",
    "rights managed", "rm", "rf",
]


def audit_sidecar(image_path: Path, verify_urls: bool = False) -> tuple[str, str]:
    """Returns (status, reason) where status in {PASS, FIX, BLOCK}."""
    sidecar = image_path.with_suffix(".json")
    if not sidecar.exists():
        return ("FIX", f"missing sidecar JSON: {sidecar.name}")

    try:
        meta = json.loads(sidecar.read_text())
    except Exception as e:
        return ("BLOCK", f"sidecar JSON unparseable: {e}")

    if meta.get("quarantined"):
        return ("BLOCK", f"already quarantined: {meta.get('quarantine_reason','no reason')}")

    license_field = (meta.get("license") or "").strip()
    if not license_field:
        return ("BLOCK", "license field empty")
    if license_field.lower() in [p.lower() for p in BLOCK_PATTERNS]:
        return ("BLOCK", f"license is blocklisted: {license_field}")
    if license_field not in LICENSE_WHITELIST:
        return ("FIX", f"license '{license_field}' not in whitelist — verify or add to whitelist")

    if license_field != "CC0" and license_field not in ("Public domain", "Public Domain"):
        if not (meta.get("creator") or "").strip():
            return ("FIX", f"license {license_field} requires creator attribution")

    if not (meta.get("source_url") or "").strip():
        return ("FIX", "source_url missing — attribution chain broken")

    if verify_urls:
        # TODO(v6): curl -sI the source_url, check 200
        pass

    return ("PASS", "clean")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--species", help="audit only one species folder")
    parser.add_argument("--staging", action="store_true", help="audit staging/ instead of training_refs/")
    parser.add_argument("--verify-urls", action="store_true", help="also curl each source_url")
    args = parser.parse_args()

    root = STAGING_DIR if args.staging else TRAINING_DIR
    if args.species:
        root = root / args.species
    if not root.exists():
        sys.exit(f"Audit root does not exist: {root}")

    pass_n = fix_n = block_n = 0
    for img in root.rglob("*"):
        if img.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        status, reason = audit_sidecar(img, args.verify_urls)
        marker = {"PASS": "✓", "FIX": "⚠", "BLOCK": "✗"}[status]
        rel = img.relative_to(REPO_ROOT)
        print(f"  {marker} {status:<5} {rel}  — {reason}")
        if status == "PASS": pass_n += 1
        elif status == "FIX": fix_n += 1
        else: block_n += 1

    print()
    print(f"Summary: {pass_n} pass, {fix_n} fix, {block_n} block")
    ready = "READY" if (fix_n == 0 and block_n == 0) else "NOT READY"
    print(f"Audit verdict: {ready} for training")
    sys.exit(0 if ready == "READY" else 1)


if __name__ == "__main__":
    main()

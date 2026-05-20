"""Reference image management: load Discord-CDN-hosted refs for MJ --sref / --cref.

Reads `sref_urls.json` at the project root (one level above the `refs/` dir).
That file is populated by `python3 upload_refs.py sync`, which downloads from
the Wikimedia source catalog in `sref_sources.json` and uploads to a Discord
webhook channel to get MJ-compatible CDN URLs.

Why not read the Wikimedia URLs directly: MJ errors on `upload.wikimedia.org`
URLs as `--sref` / `--cref` arguments (confirmed 2026-05-20, T. rex round 1).
Discord-hosted URLs are MJ's most reliable source.
"""

import json
from pathlib import Path
from typing import Any, Optional


def load_refs(refs_dir: Path) -> dict:
    """Load Discord-CDN-hosted reference URLs from sref_urls.json.

    Args:
        refs_dir: Path to refs/ directory. sref_urls.json is read from
            refs_dir.parent (project root) for backward compatibility with
            the existing CLI --refs-dir flag.

    Returns:
        dict mapping species_name → list of {label, url}. Labels are
        prefixed with a category, e.g. "paleoart/foo.png", "skeletal/bar.jpg",
        "komodo/baz.jpg", "crocodile/qux.jpg".

    Raises:
        FileNotFoundError: if sref_urls.json is missing — typically because
            `upload_refs.py sync` hasn't been run yet.
    """
    refs_dir = Path(refs_dir)
    sref_urls_path = refs_dir.parent / "sref_urls.json"

    if not sref_urls_path.exists():
        raise FileNotFoundError(
            f"sref_urls.json not found at {sref_urls_path}. "
            "Run `python3 upload_refs.py sync` from the project root to populate it."
        )

    try:
        with open(sref_urls_path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in sref_urls.json: {e}")


def get_refs_for_species(species_name: str, refs: dict) -> dict:
    """Pick a --sref (paleoart) and --cref (skeletal) URL for a species.

    sref_urls.json bundles all reference categories together per species.
    We prefer:
        --sref ← first entry labelled "paleoart/..."
        --cref ← first entry labelled "skeletal/..."
    If no paleoart entry exists, sref falls back to the first entry of any
    category (still better than text-only for anchoring the visual prior).

    Args:
        species_name: Species name (e.g. "Tyrannosaurus rex")
        refs: Loaded refs dict from load_refs() — keys are species names,
            values are lists of {label, url} dicts.

    Returns:
        dict with keys 'sref' and 'cref'. Values are URL strings or None
        if no matching entry exists.
    """
    result: dict[str, Optional[str]] = {"sref": None, "cref": None}

    entries = refs.get(species_name, [])
    if not isinstance(entries, list) or not entries:
        return result

    def _label(e: Any) -> str:
        return e.get("label", "") if isinstance(e, dict) else ""

    def _url(e: Any) -> Optional[str]:
        return e.get("url") if isinstance(e, dict) else None

    # gallery_best/ = our own vetted MJ outputs — better anchors than Wikimedia paleoart
    gallery = next((e for e in entries if _label(e).startswith("gallery_best/")), None)
    paleoart = next((e for e in entries if _label(e).startswith("paleoart/")), None)
    skeletal = next((e for e in entries if _label(e).startswith("skeletal/")), None)

    if gallery:
        result["sref"] = _url(gallery)
    elif paleoart:
        result["sref"] = _url(paleoart)
    elif entries:
        result["sref"] = _url(entries[0])

    if skeletal:
        result["cref"] = _url(skeletal)

    return result

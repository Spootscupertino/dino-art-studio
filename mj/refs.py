"""Reference image management: Load & validate paleoart / skeletal refs."""

import json
from pathlib import Path
from typing import Any, Optional, Union


def load_refs(refs_dir: Path) -> dict:
    """Load paleoart and skeletal reference JSONs.

    Args:
        refs_dir: Path to refs/ directory (contains paleoart_refs.json, skeletal_refs.json)

    Returns:
        dict with keys 'paleoart' and 'skeletal', each mapping species name → list of {label, url}

    Raises:
        FileNotFoundError: If required ref files are missing or malformed
    """
    refs_dir = Path(refs_dir)

    paleoart_path = refs_dir / "paleoart_refs.json"
    skeletal_path = refs_dir / "skeletal_refs.json"

    if not paleoart_path.exists():
        raise FileNotFoundError(f"paleoart_refs.json not found at {paleoart_path}")
    if not skeletal_path.exists():
        raise FileNotFoundError(f"skeletal_refs.json not found at {skeletal_path}")

    try:
        with open(paleoart_path) as f:
            paleoart = json.load(f)
        with open(skeletal_path) as f:
            skeletal = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in refs files: {e}")

    return {
        "paleoart": paleoart,
        "skeletal": skeletal,
    }


def get_refs_for_species(species_name: str, refs: dict) -> dict:
    """Get --sref and --cref URLs for a species.

    Args:
        species_name: Species name (e.g., "Triceratops")
        refs: Loaded refs dict from load_refs()

    Returns:
        dict with keys 'sref' (paleoart) and 'cref' (skeletal), values are URLs or None
    """
    result = {
        "sref": None,
        "cref": None,
    }

    # Get first available paleoart ref
    paleoart_list = refs.get("paleoart", {}).get(species_name, [])
    if paleoart_list and len(paleoart_list) > 0:
        result["sref"] = paleoart_list[0].get("url")

    # Get first available skeletal ref
    skeletal_list = refs.get("skeletal", {}).get(species_name, [])
    if skeletal_list and len(skeletal_list) > 0:
        result["cref"] = skeletal_list[0].get("url")

    return result

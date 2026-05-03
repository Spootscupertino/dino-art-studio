#!/usr/bin/env python3
"""Non-interactive CLI for prompt-crafter agent."""

import argparse
import json
import sys
from pathlib import Path

from mj.prompt_engine import assemble_prompt
from mj.refs import load_refs, get_refs_for_species
from species import get_anatomy


def main():
    parser = argparse.ArgumentParser(
        description="Generate Midjourney prompts (agent mode).",
        epilog="Output is valid Midjourney prompt text (copy to Discord)."
    )

    # Required
    parser.add_argument("species", help="Species name (e.g., 'Triceratops')")
    parser.add_argument("output_mode", help="Mode (e.g., 'portrait', 'environmental', 'aerial')")

    # Parameters
    parser.add_argument("--mood", default="neutral", help="Mood (e.g., 'aggressive', 'curious')")
    parser.add_argument("--lighting", default="natural", help="Lighting (e.g., 'golden_hour', 'overcast')")
    parser.add_argument("--behavior", default="neutral", help="Behavior (e.g., 'hunting', 'feeding')")
    parser.add_argument("--condition", default="healthy", help="Condition (e.g., 'scarred', 'muddy')")
    parser.add_argument("--weather", default="clear", help="Weather (e.g., 'stormy', 'misty')")
    parser.add_argument("--camera", default="eye-level", help="Camera angle (e.g., 'overhead', 'ground_level')")
    parser.add_argument("--perspective", default="default", help="Perspective override")
    parser.add_argument("--style", default="raw", help="MJ style (raw or default)")

    # Flags
    parser.add_argument("--stylize", type=int, default=None, help="--stylize 0-1000 (auto if not set)")
    parser.add_argument("--chaos", type=int, default=0, help="--chaos 0-100")
    parser.add_argument("--quality", type=float, default=1.0, choices=[0.25, 0.5, 1.0])
    parser.add_argument("--sref", type=str, default=None, help="Style ref URL override")
    parser.add_argument("--cref", type=str, default=None, help="Character ref URL override")

    # Output format
    parser.add_argument("--json", action="store_true", help="Output as JSON (all variants + metadata)")
    parser.add_argument("--variants", action="store_true", help="Include feet/environment/mouth fixes")

    # Config
    parser.add_argument("--db", type=Path, default=Path("dino_art.db"), help="Database path")
    parser.add_argument("--refs-dir", type=Path, default=Path("refs"), help="Refs directory")

    args = parser.parse_args()

    # Load anatomy
    anatomy = get_anatomy(args.species)
    if not anatomy:
        print(f"Error: Unknown species '{args.species}'", file=sys.stderr)
        sys.exit(1)

    # Load refs
    try:
        refs = load_refs(args.refs_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get auto refs if not overridden
    auto_refs = get_refs_for_species(args.species, refs)
    sref = args.sref or auto_refs.get("sref")
    cref = args.cref or auto_refs.get("cref")

    # Build parameters dict
    parameters = {
        "mood": args.mood,
        "lighting": args.lighting,
        "behavior": args.behavior,
        "condition": args.condition,
        "weather": args.weather,
        "camera": args.camera,
        "output_mode": args.output_mode,
        "perspective": args.perspective,
        "style": args.style,
    }

    # Build flags dict
    flags = {
        "stylize": args.stylize,
        "chaos": args.chaos,
        "quality": args.quality,
        "sref": sref,
        "cref": cref,
    }

    # Generate prompt
    try:
        result = assemble_prompt(
            species_data={"name": args.species},
            anatomy=anatomy,
            parameters=parameters,
            flags=flags,
            db_path=args.db,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Output
    if args.json:
        output = {
            "main": result.main_prompt,
            "variants": {
                "feet": result.feet_fix,
                "environment": result.environment_fix,
            } if args.variants else None,
            "tags": result.tags,
            "clip_estimate": result.clip_estimate,
        }
        print(json.dumps(output, indent=2))
    else:
        print(result.main_prompt)
        if args.variants:
            if result.feet_fix:
                print(f"\n--- FEET FIX ---\n{result.feet_fix}")
            if result.environment_fix:
                print(f"\n--- ENVIRONMENT FIX ---\n{result.environment_fix}")


if __name__ == "__main__":
    main()

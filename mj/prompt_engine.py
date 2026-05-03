"""Core prompt assembly engine.

Wraps the existing generate_prompt.py logic with a simplified, testable interface.
Input: species name + parameters dict + flags dict
Output: PromptResult with main prompt + variants + metadata
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union
import sqlite3

from species import get_anatomy


@dataclass
class PromptResult:
    """Output from prompt assembly."""
    main_prompt: str          # Full Midjourney-ready prompt
    feet_fix: Optional[str]   # Optional feet-fix variant
    environment_fix: Optional[str]  # Optional environment-fix variant
    tags: list[str]           # Metadata tags (period, mood, lighting, camera, output_mode)
    clip_estimate: int        # Approximate CLIP token count


def assemble_prompt(
    species_data: dict[str, Any],
    anatomy,  # SpeciesAnatomy from species.get_anatomy()
    parameters: dict[str, str],  # mood, lighting, behavior, condition, weather, camera, output_mode, perspective
    flags: dict[str, Any],  # stylize, chaos, quality, sref, cref
    secondary_species: Optional[dict] = None,
    interaction_type: Optional[str] = None,
    db_path: Path = Path("dino_art.db"),
) -> PromptResult:
    """Generate a Midjourney prompt from species + parameters.

    Args:
        species_data: Dict with 'name', 'id', 'habitat', etc. (typically from DB)
        anatomy: SpeciesAnatomy object from species.get_anatomy() — can be None
        parameters: Dict with mood, lighting, behavior, condition, weather, camera, output_mode, perspective
        flags: Dict with stylize, chaos, quality, sref, cref
        secondary_species: Optional secondary species for multi-subject scenes
        interaction_type: Optional interaction type for multi-subject (predator_prey, coexisting, etc.)
        db_path: Path to dino_art.db (for parameter lookups)

    Returns:
        PromptResult with main_prompt, variants, tags, clip_estimate
    """
    # Import here to avoid circular dependencies
    from generate_prompt import (
        assemble_prompt as _assemble_prompt,
        make_title,
        make_tags,
        make_feet_fix_prompt,
        make_environment_fix_prompt,
    )

    # Load species data from DB if not fully provided
    species = _load_species(species_data, db_path)
    if not species:
        raise ValueError(f"Species '{species_data.get('name')}' not found in database")

    # Science data is now part of the species table, so science = species for our purposes
    science = species

    # Map parameter names to DB parameter dicts
    style_param = _get_parameter(parameters.get("style", "raw"), "style", species["habitat"], db_path) or {
        "name": "raw",
        "value": "raw",
        "id": 0,
    }
    lighting_param = _get_parameter(
        parameters.get("lighting", "natural"), "lighting", species["habitat"], db_path
    ) or {"name": "natural", "value": "natural", "id": 0}
    camera_param = _get_parameter(
        parameters.get("camera", "eye-level"), "camera", species["habitat"], db_path
    ) or {"name": "eye-level", "value": "eye-level", "id": 0}
    mood_param = _get_parameter(
        parameters.get("mood", "neutral"), "mood", species["habitat"], db_path
    ) or {"name": "neutral", "value": "neutral", "id": 0}
    condition_param = _get_parameter(
        parameters.get("condition", "healthy"), "condition", species["habitat"], db_path
    ) or {"name": "healthy", "value": "healthy", "id": 0}
    behavior_param = _get_parameter(
        parameters.get("behavior", "neutral"), "behavior", species["habitat"], db_path
    ) or {"name": "neutral", "value": "neutral", "id": 0}
    weather_param = _get_parameter(
        parameters.get("weather", "clear"), "weather", species["habitat"], db_path
    ) or {"name": "clear", "value": "clear", "id": 0}

    # Load required parameters for this species
    required_params = _load_required_params(species["id"], db_path)

    # Load global blockers
    global_rules = _load_global_rules(db_path)

    # Extract flags
    stylize = flags.get("stylize") or _get_species_recommended_stylize(anatomy)
    chaos = flags.get("chaos", 0)
    quality = flags.get("quality", 1.0)
    sref = flags.get("sref")
    cref = flags.get("cref")

    # Determine output mode
    output_mode = parameters.get("output_mode", "portrait")
    perspective = parameters.get("perspective", "default")

    # Call the existing assemble_prompt function
    prompt = _assemble_prompt(
        species=species,
        science=science,
        style_param=style_param,
        lighting_param=lighting_param,
        camera_param=camera_param,
        mood_param=mood_param,
        condition_param=condition_param,
        behavior_param=behavior_param,
        weather_param=weather_param,
        required_params=required_params,
        global_rules=global_rules,
        mj_style=style_param.get("value", "raw"),
        stylize=stylize,
        chaos=chaos,
        quality=quality,
        output_mode=output_mode,
        placement=("", ""),  # No canvas placement for now
        has_sref=bool(sref),
        habitat=species.get("habitat", "terrestrial"),
        secondary_species=secondary_species,
        interaction_type=interaction_type,
        perspective=perspective,
    )

    # Build title & tags
    title = make_title(species, mood_param, output_mode)
    tags = make_tags(
        species, style_param, lighting_param, camera_param, mood_param,
        condition_param, behavior_param, weather_param, output_mode
    ).split(",")

    # Generate fix variants (optional)
    feet_fix = None
    environment_fix = None

    try:
        mj_style = style_param.get("value", "raw")
        feet_fix = make_feet_fix_prompt(species, mj_style)
    except Exception:
        feet_fix = None

    try:
        environment_fix = make_environment_fix_prompt(
            species,
            parameters.get("output_mode", "portrait"),
            weather_param,
            lighting_param,
        )
    except Exception:
        environment_fix = None

    # Estimate CLIP tokens (rough: ~1 token per 4 chars)
    clip_estimate = len(prompt) // 4

    return PromptResult(
        main_prompt=prompt,
        feet_fix=feet_fix,
        environment_fix=environment_fix,
        tags=tags,
        clip_estimate=clip_estimate,
    )


# ─────────────────────────────────────────────────────────────────────────
# Helper functions (DB queries, etc.)
# ─────────────────────────────────────────────────────────────────────────


def _load_species(species_data: dict, db_path: Path) -> Optional[dict[str, Any]]:
    """Load full species record from DB."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # If species_data has an id, use it; otherwise look up by name
    if species_data.get("id"):
        cursor.execute("SELECT * FROM species WHERE id = ?", (species_data["id"],))
    else:
        cursor.execute("SELECT * FROM species WHERE name = ?", (species_data.get("name"),))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return dict(row)




def _get_parameter(
    param_name: str, category: str, habitat: str, db_path: Path
) -> Optional[dict[str, Any]]:
    """Look up a parameter by name and category."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # First try exact name + category match
    cursor.execute(
        "SELECT * FROM parameters WHERE name = ? AND category = ?",
        (param_name, category),
    )
    row = cursor.fetchone()

    # If not found, try to find any parameter with this category (fallback)
    if not row:
        cursor.execute(
            "SELECT * FROM parameters WHERE category = ? LIMIT 1",
            (category,),
        )
        row = cursor.fetchone()

    conn.close()

    return dict(row) if row else None


def _load_required_params(species_id: int, db_path: Path) -> list[dict[str, Any]]:
    """Load required parameters for a species."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT p.* FROM parameters p
        JOIN species_parameters sp ON p.id = sp.parameter_id
        WHERE sp.species_id = ?
        """,
        (species_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def _load_global_rules(db_path: Path) -> list[str]:
    """Load global blockers/rules."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT rule FROM global_rules")
    rows = cursor.fetchall()
    conn.close()

    return [row["rule"] for row in rows]


def _get_species_recommended_stylize(anatomy) -> int:
    """Get recommended --stylize value from anatomy module."""
    if anatomy and hasattr(anatomy, "recommended_stylize") and anatomy.recommended_stylize:
        _, default, _ = anatomy.recommended_stylize
        return default
    return 100  # Global fallback

"""Base dataclasses and prompt-building helpers for the species anatomy system."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ── Character budgets for MJ's effective attention window ────────────
# MJ (via CLIP) processes ~60 words / ~350 chars effectively.
# Beyond that, later tokens are increasingly ignored.
# These budgets include the anatomy portion only — subject name,
# environment, interaction, and flags are added separately.
BUDGET_CLOSE = 350   # chars — close-up: max detail within budget
BUDGET_MID   = 250   # chars — mid shots: key features only
BUDGET_WIDE  = 120   # chars — wide/landscape: silhouette hint only


# ── Sub-component dataclasses ────────────────────────────────────────

@dataclass
class SkullAnatomy:
    overall_shape: str = ""
    distinctive_features: str = ""
    eye_description: str = ""
    nostril_position: str = ""
    crest_or_horn: str = ""
    beak: str = ""                    # pterosaurs, turtles


@dataclass
class DentitionProfile:
    tooth_shape: str = ""
    tooth_count_note: str = ""
    jaw_mechanics: str = ""
    bite_force_note: str = ""
    visible_teeth: str = ""           # externally-prominent teeth


@dataclass
class LimbStructure:
    forelimb: str = ""
    hindlimb: str = ""
    wing_or_flipper: str = ""         # wings, flippers, fins, paddles, swimming lobes
    stance: str = ""
    digit_count: str = ""
    special_appendage: str = ""       # claws, spines, pincers


@dataclass
class Integument:
    primary_covering: str = ""
    texture_detail: str = ""
    special_structures: str = ""
    membrane: str = ""                # pterosaur wing membrane
    armor: str = ""                   # armored species


@dataclass
class BodyProportions:
    body_length_m: float = 0.0
    body_mass_kg: float = 0.0
    build: str = ""
    neck: str = ""
    tail: str = ""
    silhouette: str = ""
    size_comparison: str = ""


@dataclass
class ColorationEvidence:
    likely_pattern: str = ""
    display_structures: str = ""
    fossil_evidence: str = ""         # confirmed melanosome / iridescence
    additional_notes: str = ""


@dataclass
class LocomotionProfile:
    primary_mode: str = ""
    swimming: str = ""
    flight: str = ""
    gait_detail: str = ""
    speed_note: str = ""
    special: str = ""


@dataclass
class FloraAssociation:
    primary_flora: list[str] = field(default_factory=list)
    ground_cover: str = ""
    canopy: str = ""
    water_plants: str = ""
    banned_flora: list[str] = field(default_factory=list)


# ── Master anatomy dataclass ────────────────────────────────────────

@dataclass
class SpeciesAnatomy:
    species_name: str = ""
    common_name: str = ""
    period: str = ""
    habitat: str = ""                 # terrestrial / marine / aerial / arthropod / plant

    skull: Optional[SkullAnatomy] = None
    dentition: Optional[DentitionProfile] = None
    limbs: Optional[LimbStructure] = None
    integument: Optional[Integument] = None
    body: Optional[BodyProportions] = None
    coloration: Optional[ColorationEvidence] = None
    locomotion: Optional[LocomotionProfile] = None
    flora: Optional[FloraAssociation] = None

    unique_features: list[str] = field(default_factory=list)

    # ── MJ-optimized shorthand (Session 16) ──────────────────────────
    # 5-8 short CLIP-friendly phrases that MJ actually keys on.
    # These are the PRIMARY output — the detailed dataclass fields above
    # are the scientific reference that the shorthand is distilled from.
    # Each phrase should be 2-5 words, visually concrete, no explanations.
    # Priority order: [0] is the most visually distinctive feature.
    mj_shorthand: list[str] = field(default_factory=list)

    # ── Per-species stylize recommendation (Session 17) ──────────────
    # Different species render best at different MJ --stylize values.
    # Highly detailed species (T. rex, Triceratops) need lower stylize
    # to preserve anatomy accuracy. Simpler silhouettes (Brachiosaurus,
    # plants) can tolerate higher stylize for artistic quality.
    # (low, default, high) — the generator uses 'default' and surfaces
    # the range as a recommendation to the user.
    recommended_stylize: tuple[int, int, int] = (75, 100, 250)

    # ── Known MJ failure modes (Session 17) ──────────────────────────
    # Phrases that cause MJ to misrender this species. Used for prompt
    # notes and to actively avoid these terms in prompt assembly.
    known_failures: list[str] = field(default_factory=list)


# ── Prompt builders ──────────────────────────────────────────────────

def _budget_join(phrases: list, budget: int) -> str:
    """Join phrases with ', ' until budget is exhausted.

    Phrases are added in priority order (index 0 = highest priority).
    Once adding the next phrase would exceed the budget, stop.
    Always includes at least the first phrase regardless of budget.
    """
    if not phrases:
        return ""
    result = phrases[0]
    for p in phrases[1:]:
        candidate = result + ", " + p
        if len(candidate) > budget:
            break
        result = candidate
    return result


def build_anatomy_prompt(anatomy: SpeciesAnatomy, mode_type: str = "mid") -> str:
    """Build a budget-capped Midjourney-ready anatomy string.

    Uses mj_shorthand as the primary source — these are CLIP-optimized
    phrases tested to produce correct anatomy in MJ output. Falls back
    to extracting from detailed dataclass fields if no shorthand defined.

    mode_type controls detail level and budget:
        "close"  – up to BUDGET_CLOSE chars (~350) — all shorthand phrases
        "mid"    – up to BUDGET_MID chars (~250) — top shorthand + silhouette
        "wide"   – up to BUDGET_WIDE chars (~120) — silhouette only
    """
    budget = {"close": BUDGET_CLOSE, "mid": BUDGET_MID, "wide": BUDGET_WIDE}.get(
        mode_type, BUDGET_MID
    )

    # ── Shorthand path (preferred) ───────────────────────────────────
    if anatomy.mj_shorthand:
        if mode_type == "wide":
            # Wide: silhouette + first shorthand phrase
            parts: list[str] = []
            if anatomy.body and anatomy.body.silhouette:
                parts.append(anatomy.body.silhouette)
            parts.append(anatomy.mj_shorthand[0])
            return _budget_join(parts, budget)

        if mode_type == "mid":
            # Mid: silhouette + top shorthand phrases within budget
            parts = []
            if anatomy.body and anatomy.body.silhouette:
                parts.append(anatomy.body.silhouette)
            parts.extend(anatomy.mj_shorthand)
            return _budget_join(parts, budget)

        # Close: all shorthand + size comparison + coloration hint
        parts = list(anatomy.mj_shorthand)
        if anatomy.body and anatomy.body.size_comparison:
            parts.append(anatomy.body.size_comparison)
        if anatomy.coloration and anatomy.coloration.likely_pattern:
            parts.append(anatomy.coloration.likely_pattern)
        return _budget_join(parts, budget)

    # ── Fallback: extract from detailed fields ───────────────────────
    # Used only if mj_shorthand is empty (shouldn't happen once all
    # 42 species are populated, but kept for safety).
    return _fallback_prompt(anatomy, mode_type, budget)


def _fallback_prompt(anatomy: SpeciesAnatomy, mode_type: str, budget: int) -> str:
    """Legacy field-extraction path — used when mj_shorthand is empty."""
    if mode_type == "wide":
        parts: list[str] = []
        if anatomy.body and anatomy.body.silhouette:
            parts.append(anatomy.body.silhouette)
        if anatomy.unique_features:
            parts.append(anatomy.unique_features[0])
        return _budget_join(parts, budget)

    # Build a priority-ranked list from fields
    ranked: list[str] = []

    # 1. Silhouette (always first — tells MJ the overall shape)
    if anatomy.body and anatomy.body.silhouette:
        ranked.append(anatomy.body.silhouette)

    # 2. Key texture
    if anatomy.integument and anatomy.integument.primary_covering:
        ranked.append(anatomy.integument.primary_covering)

    # 3. Skull shape (close only)
    if mode_type == "close" and anatomy.skull and anatomy.skull.overall_shape:
        ranked.append(anatomy.skull.overall_shape)

    # 4. Teeth / beak
    if anatomy.dentition and anatomy.dentition.tooth_shape:
        ranked.append(anatomy.dentition.tooth_shape)

    # 5. Size anchor
    if anatomy.body and anatomy.body.size_comparison:
        ranked.append(anatomy.body.size_comparison)

    # 6. Top unique feature
    if anatomy.unique_features:
        ranked.append(anatomy.unique_features[0])

    # 7. Coloration
    if anatomy.coloration and anatomy.coloration.likely_pattern:
        ranked.append(anatomy.coloration.likely_pattern)

    return _budget_join(ranked, budget)


def build_anatomy_negative(anatomy: SpeciesAnatomy) -> str:
    """Build negative-prompt additions from banned flora and key inaccuracy notes."""
    negatives: list[str] = []

    if anatomy.flora and anatomy.flora.banned_flora:
        negatives.extend(anatomy.flora.banned_flora)

    return ", ".join(negatives)

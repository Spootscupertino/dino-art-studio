"""Tests for prompt assembly engine."""

import pytest
from pathlib import Path

from mj.prompt_engine import assemble_prompt, PromptResult
from species import get_anatomy


@pytest.fixture
def triceratops_anatomy():
    """Load Triceratops anatomy module."""
    return get_anatomy("Triceratops")


@pytest.fixture
def parameters_default():
    """Default parameters for a prompt."""
    return {
        "mood": "neutral",
        "lighting": "natural",
        "behavior": "neutral",
        "condition": "healthy",
        "weather": "clear",
        "camera": "eye-level",
        "output_mode": "portrait",
        "perspective": "default",
        "style": "raw",
    }


@pytest.fixture
def flags_default():
    """Default flags for a prompt."""
    return {
        "stylize": 100,
        "chaos": 0,
        "quality": 1.0,
        "sref": None,
        "cref": None,
    }


def test_assemble_prompt_returns_result(triceratops_anatomy, parameters_default, flags_default):
    """assemble_prompt() returns PromptResult object."""
    result = assemble_prompt(
        species_data={"name": "Triceratops"},
        anatomy=triceratops_anatomy,
        parameters=parameters_default,
        flags=flags_default,
    )
    assert isinstance(result, PromptResult)


def test_prompt_result_has_main_prompt(triceratops_anatomy, parameters_default, flags_default):
    """PromptResult.main_prompt is a non-empty string."""
    result = assemble_prompt(
        species_data={"name": "Triceratops"},
        anatomy=triceratops_anatomy,
        parameters=parameters_default,
        flags=flags_default,
    )
    assert isinstance(result.main_prompt, str)
    assert len(result.main_prompt) > 50


def test_prompt_contains_species_name(triceratops_anatomy, parameters_default, flags_default):
    """Prompt includes species name."""
    result = assemble_prompt(
        species_data={"name": "Triceratops"},
        anatomy=triceratops_anatomy,
        parameters=parameters_default,
        flags=flags_default,
    )
    assert "Triceratops" in result.main_prompt


def test_prompt_includes_mj_flags(triceratops_anatomy, parameters_default, flags_default):
    """Prompt includes Midjourney flags."""
    flags_default["stylize"] = 250
    flags_default["chaos"] = 20
    result = assemble_prompt(
        species_data={"name": "Triceratops"},
        anatomy=triceratops_anatomy,
        parameters=parameters_default,
        flags=flags_default,
    )
    assert "--stylize 250" in result.main_prompt
    assert "--chaos 20" in result.main_prompt
    assert "--q 1" in result.main_prompt


def test_prompt_result_tags_are_list(triceratops_anatomy, parameters_default, flags_default):
    """PromptResult.tags is a list of strings."""
    result = assemble_prompt(
        species_data={"name": "Triceratops"},
        anatomy=triceratops_anatomy,
        parameters=parameters_default,
        flags=flags_default,
    )
    assert isinstance(result.tags, list)
    assert all(isinstance(tag, str) for tag in result.tags)


def test_prompt_result_clip_estimate_is_int(triceratops_anatomy, parameters_default, flags_default):
    """PromptResult.clip_estimate is a positive integer."""
    result = assemble_prompt(
        species_data={"name": "Triceratops"},
        anatomy=triceratops_anatomy,
        parameters=parameters_default,
        flags=flags_default,
    )
    assert isinstance(result.clip_estimate, int)
    assert result.clip_estimate > 0


def test_variants_are_optional(triceratops_anatomy, parameters_default, flags_default):
    """PromptResult variants can be None or string."""
    result = assemble_prompt(
        species_data={"name": "Triceratops"},
        anatomy=triceratops_anatomy,
        parameters=parameters_default,
        flags=flags_default,
    )
    assert result.feet_fix is None or isinstance(result.feet_fix, str)
    assert result.environment_fix is None or isinstance(result.environment_fix, str)


def test_different_output_modes(triceratops_anatomy, parameters_default, flags_default):
    """Prompts differ based on output_mode."""
    parameters_default["output_mode"] = "portrait"
    result_portrait = assemble_prompt(
        species_data={"name": "Triceratops"},
        anatomy=triceratops_anatomy,
        parameters=parameters_default,
        flags=flags_default,
    )

    parameters_default["output_mode"] = "environmental"
    result_environmental = assemble_prompt(
        species_data={"name": "Triceratops"},
        anatomy=triceratops_anatomy,
        parameters=parameters_default,
        flags=flags_default,
    )

    # Prompts should be different (environmental mode is more landscape-focused)
    assert result_portrait.main_prompt != result_environmental.main_prompt


def test_invalid_species_raises(parameters_default, flags_default):
    """assemble_prompt() raises ValueError for unknown species."""
    with pytest.raises(ValueError, match="not found"):
        assemble_prompt(
            species_data={"name": "UnknownSpecies"},
            anatomy=None,
            parameters=parameters_default,
            flags=flags_default,
        )

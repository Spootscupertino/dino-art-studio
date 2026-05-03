"""Tests for reference image loading and validation."""

import json
import pytest
from pathlib import Path

from mj.refs import load_refs, get_refs_for_species


@pytest.fixture
def mock_refs_dir(tmp_path):
    """Create temporary refs directory with mock files."""
    refs_dir = tmp_path / "refs"
    refs_dir.mkdir()

    # paleoart_refs.json
    paleoart = {
        "Triceratops": [
            {"label": "triceratops_profile.jpg", "url": "https://example.com/triceratops_profile.jpg"},
            {"label": "triceratops_frill.jpg", "url": "https://example.com/triceratops_frill.jpg"},
        ],
        "Tyrannosaurus rex": [
            {"label": "t_rex_profile.jpg", "url": "https://example.com/t_rex.jpg"},
        ],
    }
    (refs_dir / "paleoart_refs.json").write_text(json.dumps(paleoart))

    # skeletal_refs.json
    skeletal = {
        "Triceratops": [
            {"label": "triceratops_skeleton.jpg", "url": "https://example.com/triceratops_skeleton.jpg"},
        ],
        "Tyrannosaurus rex": [
            {"label": "t_rex_skeleton.jpg", "url": "https://example.com/t_rex_skeleton.jpg"},
        ],
    }
    (refs_dir / "skeletal_refs.json").write_text(json.dumps(skeletal))

    return refs_dir


def test_load_refs_succeeds(mock_refs_dir):
    """load_refs() returns dict with paleoart and skeletal keys."""
    refs = load_refs(mock_refs_dir)
    assert "paleoart" in refs
    assert "skeletal" in refs
    assert isinstance(refs["paleoart"], dict)
    assert isinstance(refs["skeletal"], dict)


def test_load_refs_contains_species(mock_refs_dir):
    """load_refs() includes species from JSON files."""
    refs = load_refs(mock_refs_dir)
    assert "Triceratops" in refs["paleoart"]
    assert "Tyrannosaurus rex" in refs["skeletal"]


def test_load_refs_missing_file_raises(tmp_path):
    """load_refs() raises FileNotFoundError if refs files missing."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    with pytest.raises(FileNotFoundError):
        load_refs(empty_dir)


def test_load_refs_invalid_json_raises(tmp_path):
    """load_refs() raises ValueError on malformed JSON."""
    refs_dir = tmp_path / "refs"
    refs_dir.mkdir()
    (refs_dir / "paleoart_refs.json").write_text("{invalid json")
    (refs_dir / "skeletal_refs.json").write_text("{}")
    with pytest.raises(ValueError):
        load_refs(refs_dir)


def test_get_refs_for_species_returns_dict(mock_refs_dir):
    """get_refs_for_species() returns dict with sref/cref keys."""
    refs = load_refs(mock_refs_dir)
    result = get_refs_for_species("Triceratops", refs)
    assert isinstance(result, dict)
    assert "sref" in result
    assert "cref" in result


def test_get_refs_for_species_found(mock_refs_dir):
    """get_refs_for_species() returns URLs when refs exist."""
    refs = load_refs(mock_refs_dir)
    result = get_refs_for_species("Triceratops", refs)
    assert result["sref"] == "https://example.com/triceratops_profile.jpg"
    assert result["cref"] == "https://example.com/triceratops_skeleton.jpg"


def test_get_refs_for_species_missing(mock_refs_dir):
    """get_refs_for_species() returns None for unknown species."""
    refs = load_refs(mock_refs_dir)
    result = get_refs_for_species("UnknownSpecies", refs)
    assert result["sref"] is None
    assert result["cref"] is None


def test_get_refs_for_species_partial_match(mock_refs_dir):
    """get_refs_for_species() handles species with only paleoart or skeletal."""
    refs = load_refs(mock_refs_dir)
    result = get_refs_for_species("Tyrannosaurus rex", refs)
    # T. rex has both in the mock
    assert result["sref"] is not None
    assert result["cref"] is not None

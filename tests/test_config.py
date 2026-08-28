"""Tests for configuration and presets."""

from core.config import (
    DEFAULT_MAX_CHARS,
    DEFAULT_SPEAKER,
    FICTION_PRESETS,
    GENRE_CONFIGS,
    NONFICTION_PRESETS,
    get_presets_by_genre,
)


def test_config_presets():
    assert "fiction_storyteller" in FICTION_PRESETS
    assert "fiction_dramatic" in FICTION_PRESETS
    assert "nonfiction_business" in NONFICTION_PRESETS
    assert "nonfiction_documentary" in NONFICTION_PRESETS
    assert DEFAULT_SPEAKER == "Uncle_Fu"
    assert DEFAULT_MAX_CHARS == 200

    # Test genre retrieval helper
    fiction = get_presets_by_genre("fiction")
    assert "fiction_storyteller" in fiction
    assert "nonfiction_business" not in fiction

    nonfiction = get_presets_by_genre("nonfiction")
    assert "nonfiction_business" in nonfiction
    assert "fiction_storyteller" not in nonfiction

    # Test genre configs
    assert "fiction" in GENRE_CONFIGS
    assert "nonfiction" in GENRE_CONFIGS
    assert GENRE_CONFIGS["fiction"]["max_silence_s"] > GENRE_CONFIGS["nonfiction"]["max_silence_s"]

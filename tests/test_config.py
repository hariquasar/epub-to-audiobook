"""Tests for configuration and presets."""

from core.config import DEFAULT_MAX_CHARS, DEFAULT_SPEAKER, STYLE_PRESETS


def test_config_presets():
    assert "storyteller" in STYLE_PRESETS
    assert "calm_narrator" in STYLE_PRESETS
    assert DEFAULT_SPEAKER == "Uncle_Fu"
    assert DEFAULT_MAX_CHARS == 200
    for preset, prompt in STYLE_PRESETS.items():
        assert len(prompt) > 20
        assert "说书人" in prompt or "旁白" in prompt or "普通话" in prompt

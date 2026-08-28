"""Unit tests for web_ui functions."""

from web_ui import inspect_epub, update_genre_styles, update_speaker_choices


def test_inspect_epub_empty():
    assert "Please upload" in inspect_epub(None)


def test_update_genre_styles():
    fiction_dropdown = update_genre_styles("fiction")
    fiction_values = [c if isinstance(c, str) else c[0] for c in fiction_dropdown.choices]
    assert "fiction_storyteller" in fiction_values

    nonfiction_dropdown = update_genre_styles("nonfiction")
    nonfiction_values = [c if isinstance(c, str) else c[0] for c in nonfiction_dropdown.choices]
    assert "nonfiction_business" in nonfiction_values


def test_update_speaker_choices():
    edge_speakers = update_speaker_choices("edge")
    edge_values = [c if isinstance(c, str) else c[0] for c in edge_speakers.choices]
    assert "zh-CN-YunxiNeural" in edge_values

    qwen_speakers = update_speaker_choices("qwen3")
    qwen_values = [c if isinstance(c, str) else c[0] for c in qwen_speakers.choices]
    assert "Uncle_Fu" in qwen_values

"""Tests for BYOM TTS Engine factory and interfaces."""

import pytest

from core.tts_engine import BaseTTSEngine, EdgeTTSEngine, create_tts_engine


def test_create_tts_engine_edge():
    engine = create_tts_engine("edge")
    assert isinstance(engine, BaseTTSEngine)
    assert isinstance(engine, EdgeTTSEngine)


def test_create_tts_engine_invalid():
    with pytest.raises(ValueError, match="Unknown TTS engine type"):
        create_tts_engine("unsupported_backend")


def test_edge_tts_synthesize():
    engine = create_tts_engine("edge", voice="zh-CN-YunxiNeural")
    audio, sr, audit = engine.synthesize("这是一个测试。")
    assert len(audio) > 0
    assert sr > 0
    assert audit["duration_seconds"] > 0.5
    assert audit["peak"] > 0.0

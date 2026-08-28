"""Qwen3-TTS Audiobook Generator Core Package."""

from .audiobook_builder import AudiobookBuilder
from .config import DEFAULT_MAX_CHARS, DEFAULT_MODEL_DIR, DEFAULT_SPEAKER, STYLE_PRESETS
from .epub_parser import Chapter, ParsedBook, parse_epub
from .text_processor import chunk_text, split_sentences, to_simplified
from .tts_engine import TTSEngine, audit_audio, tighten_silences

__all__ = [
    "AudiobookBuilder",
    "TTSEngine",
    "parse_epub",
    "ParsedBook",
    "Chapter",
    "chunk_text",
    "split_sentences",
    "to_simplified",
    "audit_audio",
    "tighten_silences",
    "STYLE_PRESETS",
    "DEFAULT_SPEAKER",
    "DEFAULT_MAX_CHARS",
    "DEFAULT_MODEL_DIR",
]

"""EPUB to Audiobook Generator Core Package (BYOM Architecture)."""

from .audiobook_builder import AudiobookBuilder
from .config import DEFAULT_MAX_CHARS, DEFAULT_MODEL_DIR, DEFAULT_SPEAKER, STYLE_PRESETS
from .epub_parser import Chapter, ParsedBook, parse_epub
from .text_processor import chunk_text, split_sentences, to_simplified
from .tts_engine import (
    BaseTTSEngine,
    EdgeTTSEngine,
    QwenTTSEngine,
    TTSEngine,
    audit_audio,
    create_tts_engine,
    tighten_silences,
)

__all__ = [
    "AudiobookBuilder",
    "BaseTTSEngine",
    "QwenTTSEngine",
    "EdgeTTSEngine",
    "TTSEngine",
    "create_tts_engine",
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

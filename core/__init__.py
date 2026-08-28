"""EPUB to Audiobook Generator Core Package (BYOM & Multi-Genre Architecture)."""

from .audiobook_builder import AudiobookBuilder
from .config import (
    DEFAULT_MAX_CHARS,
    DEFAULT_MODEL_DIR,
    DEFAULT_SPEAKER,
    FICTION_PRESETS,
    GENRE_CONFIGS,
    NONFICTION_PRESETS,
    STYLE_PRESETS,
    get_presets_by_genre,
)
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
    "FICTION_PRESETS",
    "NONFICTION_PRESETS",
    "GENRE_CONFIGS",
    "get_presets_by_genre",
    "DEFAULT_SPEAKER",
    "DEFAULT_MAX_CHARS",
    "DEFAULT_MODEL_DIR",
]

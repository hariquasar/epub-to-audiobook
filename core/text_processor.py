"""Text processing, normalization, and sentence-preserving chunking."""

from __future__ import annotations

import re
from typing import List

try:
    import opencc

    _T2S_CONVERTER = opencc.OpenCC("t2s")
except Exception:
    _T2S_CONVERTER = None


def to_simplified(text: str) -> str:
    """Convert Traditional Chinese to Simplified Chinese for stable TTS reading."""
    if _T2S_CONVERTER is not None:
        return _T2S_CONVERTER.convert(text)
    return text


def split_sentences(text: str) -> List[str]:
    """Split text into sentence units keeping sentence terminators and trailing quotes together."""
    pattern = re.compile(r'([^。！？；…\n]*[。！？；…\n]+[”』」’\'"]*)')
    parts = pattern.findall(text)
    matched_len = sum(len(p) for p in parts)
    if matched_len < len(text):
        remainder = text[matched_len:]
        if remainder:
            parts.append(remainder)
    return [p for p in parts if p]


def chunk_text(text: str, max_chars: int = 200) -> List[str]:
    """Build bounded chunks without splitting inside sentences unless a single sentence exceeds max_chars.

    Guarantees:
    - Never breaks in the middle of a sentence unless an isolated sentence is > max_chars.
    - Concatenation of all chunks restores the exact input text.
    """
    sentences = split_sentences(text)
    chunks: List[str] = []
    current = ""

    for s in sentences:
        if not s:
            continue

        # If adding this complete sentence fits within max_chars, group it
        if len(current) + len(s) <= max_chars:
            current += s
            continue

        # Flush current chunk before handling the new sentence
        if current:
            chunks.append(current)
            current = ""

        # If the sentence alone fits within max_chars, start current with it
        if len(s) <= max_chars:
            current = s
            continue

        # Only when an individual sentence exceeds max_chars, split at clause punctuation
        clauses = re.findall(r'([^，、：]*[，、：]+[”』」’\'"]*)', s)
        clause_len = sum(len(c) for c in clauses)
        if clause_len < len(s):
            rem = s[clause_len:]
            if rem:
                clauses.append(rem)

        for c in clauses:
            if not c:
                continue
            if len(current) + len(c) <= max_chars:
                current += c
            else:
                if current:
                    chunks.append(current)
                    current = ""
                if len(c) <= max_chars:
                    current = c
                else:
                    chunks.append(c)

    if current:
        chunks.append(current)

    assert "".join(chunks) == text, "Concatenation of chunks must restore the exact original text"
    return chunks

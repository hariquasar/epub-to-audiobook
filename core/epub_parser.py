"""EPUB file parser and text extractor."""
from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub


@dataclass
class Chapter:
    index: int
    title: str
    text: str
    file_name: str
    character_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.character_count = len(self.text)


@dataclass
class ParsedBook:
    title: str
    author: str
    language: str
    chapters: List[Chapter]
    total_characters: int = field(init=False)

    def __post_init__(self) -> None:
        self.total_characters = sum(c.character_count for c in self.chapters)


def clean_html_text(html_content: bytes | str) -> tuple[str, str]:
    """Clean HTML content into (chapter_title, cleaned_body_text)."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script and style tags
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # Extract title if present in h1/h2/title
    title = ""
    for heading in soup.find_all(["h1", "h2", "h3", "title"]):
        heading_text = heading.get_text(strip=True)
        if heading_text and len(heading_text) < 80:
            title = heading_text
            break

    # Get paragraph-separated text
    paragraphs = []
    for p in soup.find_all(["p", "div", "h1", "h2", "h3", "h4", "h5", "li", "blockquote"]):
        text = p.get_text(strip=True)
        if text:
            paragraphs.append(text)

    if not paragraphs:
        raw_text = soup.get_text("\n", strip=True)
        paragraphs = [line.strip() for line in raw_text.splitlines() if line.strip()]

    # Normalize whitespace inside paragraphs
    cleaned_paragraphs = []
    seen = set()
    for p in paragraphs:
        normalized = re.sub(r"[ \t\u3000]+", " ", p).strip()
        # Avoid duplicate header additions
        if normalized:
            cleaned_paragraphs.append(normalized)

    full_text = "\n\n".join(cleaned_paragraphs)
    return title, full_text


def parse_epub(epub_path: str | Path, min_chapter_chars: int = 100) -> ParsedBook:
    """Parse an EPUB file into structured metadata and clean chapter texts."""
    path = Path(epub_path)
    if not path.is_file():
        raise FileNotFoundError(f"EPUB file not found: {path}")

    try:
        book = epub.read_epub(str(path))
    except Exception as exc:
        raise ValueError(f"Failed to read EPUB file '{path.name}': {exc}") from exc

    # Extract metadata
    title_meta = book.get_metadata("DC", "title")
    title = title_meta[0][0] if title_meta else path.stem

    author_meta = book.get_metadata("DC", "creator")
    author = author_meta[0][0] if author_meta else "Unknown"

    lang_meta = book.get_metadata("DC", "language")
    language = lang_meta[0][0] if lang_meta else "zh"

    chapters: List[Chapter] = []
    chapter_idx = 1

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        item_name = item.get_name()
        content = item.get_body_content()
        if not content:
            continue

        doc_title, text = clean_html_text(content)
        if len(text) < min_chapter_chars:
            # Skip tiny navigational / copyright / cover stubs
            continue

        if not doc_title:
            # Try to infer chapter title from first line
            first_line = text.splitlines()[0][:50]
            if re.match(r"^第[一二三四五六七八九十百千万0-9]+[回章节卷]", first_line):
                doc_title = first_line
            else:
                doc_title = f"Chapter {chapter_idx}"

        chapters.append(
            Chapter(
                index=chapter_idx,
                title=doc_title,
                text=text,
                file_name=item_name,
            )
        )
        chapter_idx += 1

    if not chapters:
        raise ValueError(f"No readable chapter text found in EPUB: '{path.name}'")

    return ParsedBook(
        title=title,
        author=author,
        language=language,
        chapters=chapters,
    )

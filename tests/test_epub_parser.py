"""Tests for EPUB parsing and HTML text cleaning."""

import pytest

from core.epub_parser import clean_html_text, parse_epub


def test_clean_html_text():
    html = """
    <html>
      <head><style>p { color: red; }</style></head>
      <body>
        <h1>第一章 冒险的开端</h1>
        <p>在一个风和日丽的早晨，探险队员们整装待发。</p>
        <p>年轻的队员背起行囊，快步走向集合大厅。</p>
        <script>console.log('remove me');</script>
      </body>
    </html>
    """
    title, text = clean_html_text(html)
    assert "第一章 冒险的开端" in title
    assert "console.log" not in text
    assert "color: red" not in text
    assert "在一个风和日丽的早晨" in text
    assert "年轻的队员" in text


def test_parse_epub_not_found():
    with pytest.raises(FileNotFoundError):
        parse_epub("/non/existent/path.epub")

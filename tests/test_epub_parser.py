"""Tests for EPUB parsing and HTML text cleaning."""

import pytest

from core.epub_parser import clean_html_text, parse_epub


def test_clean_html_text():
    html = """
    <html>
      <head><style>p { color: red; }</style></head>
      <body>
        <h1>第一回 古道腾驹惊白发</h1>
        <p>清乾隆十八年六月，陕西扶风延绥镇总兵衙门内院。</p>
        <p>一个十四岁的女孩儿跳跳蹦蹦的走向教书先生书房。</p>
        <script>console.log('remove me');</script>
      </body>
    </html>
    """
    title, text = clean_html_text(html)
    assert "第一回 古道腾驹惊白发" in title
    assert "console.log" not in text
    assert "color: red" not in text
    assert "清乾隆十八年六月" in text
    assert "十四岁的女孩儿" in text


def test_parse_epub_not_found():
    with pytest.raises(FileNotFoundError):
        parse_epub("/non/existent/path.epub")

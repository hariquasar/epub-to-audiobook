"""Tests for sentence-safe chunking, quotation handling, and text conversion."""

from core.text_processor import chunk_text, split_sentences, to_simplified


def test_split_sentences_basic():
    text = "第一句话。第二句话！第三句话？第四句话；第五句话…第六句"
    sentences = split_sentences(text)
    assert len(sentences) == 6
    assert "".join(sentences) == text
    assert sentences[0] == "第一句话。"
    assert sentences[1] == "第二句话！"
    assert sentences[2] == "第三句话？"
    assert sentences[3] == "第四句话；"
    assert sentences[4] == "第五句话…"
    assert sentences[5] == "第六句"


def test_split_sentences_closing_quotes():
    text = "张明大叫：「小华，你教我这招！」李老师微笑道：「明天教你。」张明道：「一言为定！」"
    sentences = split_sentences(text)
    assert "".join(sentences) == text
    # Ensure quotes are not detached
    assert sentences[0] == "张明大叫：「小华，你教我这招！」"
    assert sentences[1] == "李老师微笑道：「明天教你。」"
    assert sentences[2] == "张明道：「一言为定！」"


def test_chunk_text_preserves_sentences():
    text = (
        "这是一个阳光明媚的早晨，小镇街道上行人熙熙攘攘。"
        "图书馆里陈列着各式各样的历史典籍，记录着过去岁月的故事。"
        "午后阳光透过落地窗洒在书桌上，让人感到格外宁静与舒适。"
    )
    chunks = chunk_text(text, max_chars=100)
    assert "".join(chunks) == text
    for c in chunks:
        # None of the chunks should end with a comma
        assert not c.endswith("，")
        assert len(c) <= 100


def test_chunk_text_long_sentence_fallback():
    # A single sentence with no period that exceeds max_chars should safely split on commas
    long_sentence = "一二三四五，六七八九十，十一十二，十三十四，十五十六，十七十八，十九二十，二十一二十二。"
    chunks = chunk_text(long_sentence, max_chars=20)
    assert "".join(chunks) == long_sentence
    for c in chunks:
        assert len(c) <= 20


def test_to_simplified():
    traditional = "這是一個測試文本，沒想到腳步這麼輕。"
    simplified = to_simplified(traditional)
    assert "没" in simplified or "沒" in simplified
    assert "这是一个" in simplified

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
    text = "李沅芷大叫：「老师，你教我这玩意儿！」陆高止微笑道：「明天教你。」李沅芷道：「一言为定！」"
    sentences = split_sentences(text)
    assert "".join(sentences) == text
    # Ensure quotes are not detached
    assert sentences[0] == "李沅芷大叫：「老师，你教我这玩意儿！」"
    assert sentences[1] == "陆高止微笑道：「明天教你。」"
    assert sentences[2] == "李沅芷道：「一言为定！」"


def test_chunk_text_preserves_sentences():
    text = (
        "清乾隆十八年六月，陕西扶风延绥镇总兵衙门内院，一个十四岁的女孩儿跳跳蹦蹦的走向教书先生书房。"
        "上午老师讲完了《资治通鉴》上「赤壁之战」的一段书，随口讲了些诸葛亮、周瑜的故事。"
        "午后本来没功课，那女孩儿却兴犹未尽，要老师再讲三国故事。"
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

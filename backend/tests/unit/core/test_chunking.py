"""core 分块业务规则的测试。"""

import pytest

from app.core.services.chunking import split_text


def test_short_text_returns_single_segment():
    segments = split_text("hello world", chunk_size=100, overlap=10)
    assert len(segments) == 1
    assert segments[0].index == 0
    assert segments[0].text == "hello world"


def test_empty_text_returns_no_segments():
    assert split_text("   \n  ", chunk_size=100, overlap=10) == []


def test_indices_are_continuous_from_zero():
    text = "a" * 250
    segments = split_text(text, chunk_size=100, overlap=20)
    assert [seg.index for seg in segments] == list(range(len(segments)))
    assert len(segments) > 1


def test_consecutive_segments_overlap():
    text = "0123456789" * 30  # 300 字符
    segments = split_text(text, chunk_size=100, overlap=20)
    # 上一段的尾部 20 字符应出现在下一段开头（重叠窗口）
    assert segments[0].text[-20:] == segments[1].text[:20]


def test_tiny_tail_is_merged_into_previous_segment():
    # 210 字符、步长 50：最后只剩 10 字符的碎片（< overlap 50），应并入上一段而非独立成段
    text = "x" * 210
    segments = split_text(text, chunk_size=100, overlap=50)
    assert [len(seg.text) for seg in segments] == [100, 100, 100, 70]


def test_invalid_params_raise():
    with pytest.raises(ValueError):
        split_text("abc", chunk_size=0, overlap=0)
    with pytest.raises(ValueError):
        split_text("abc", chunk_size=100, overlap=100)

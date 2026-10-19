"""core 增量判定（内容哈希）规则的测试。"""

from app.core.services.hashing import compute_content_hash


def test_same_text_gives_same_hash():
    assert compute_content_hash("hello") == compute_content_hash("hello")


def test_whitespace_difference_is_ignored():
    assert compute_content_hash("  hello \n") == compute_content_hash("hello")


def test_content_change_gives_different_hash():
    assert compute_content_hash("hello") != compute_content_hash("hello!")

"""引用格式规则的业务测试：编号、标记解析、防编造来源。"""

from app.core.entities.models import SearchHit
from app.core.services.citation import build_citations, extract_markers, format_context


def _hit(i: int) -> SearchHit:
    return SearchHit(
        chunk_id=f"doc1:{i:04d}",
        doc_id="doc1",
        index=i,
        text=f"片段内容{i}",
        title="测试笔记",
        source="note.md",
        score=0.9 - i * 0.1,
    )


def test_format_context_numbers_hits_from_one():
    block = format_context([_hit(0), _hit(1)])

    assert block.startswith("[1] 《测试笔记》 来源: note.md\n片段内容0")
    assert "\n\n[2] 《测试笔记》 来源: note.md\n片段内容1" in block


def test_extract_markers_dedupes_and_keeps_order():
    assert extract_markers("结论 [2]，补充 [1]，再看 [2] 与 [abc] 和 [007]") == [2, 1, 7]


def test_build_citations_only_keeps_used_and_real_markers():
    hits = [_hit(0), _hit(1)]
    # [2] 用到且真实；[99] 超出检索范围属编造，必须丢弃；[1] 未引用，不产出
    citations = build_citations("答案 [2]，据称 [99]。", hits)

    assert [c.marker for c in citations] == [2]
    assert citations[0].chunk_id == "doc1:0001"
    assert citations[0].excerpt == "片段内容1"
    assert citations[0].title == "测试笔记"
    assert citations[0].source == "note.md"


def test_build_citations_follows_appearance_order():
    citations = build_citations("先 [2] 后 [1]", [_hit(0), _hit(1)])

    assert [c.marker for c in citations] == [2, 1]


def test_build_citations_without_markers_returns_empty():
    assert build_citations("我不知道。", [_hit(0)]) == []

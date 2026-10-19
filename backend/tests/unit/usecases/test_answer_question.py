"""问答用例的 Mock 测试：检索、prompt 组装、引用校验；一律不出网。"""

import pytest

from app.core.entities.models import Chunk, Document
from app.usecases.answer_question import answer_question
from app.usecases.create_section import create_section
from tests.fakes import (
    FakeEmbeddingProvider,
    FakeLLMProvider,
    InMemoryDocumentRepository,
    InMemorySectionRepository,
    InMemoryVectorStore,
)

CHUNK_TEXT = "手冲咖啡建议使用九十二度的水温。"


def _seeded_store() -> tuple[InMemoryVectorStore, FakeEmbeddingProvider]:
    embedder = FakeEmbeddingProvider()
    store = InMemoryVectorStore()
    document = Document(
        doc_id="doc1",
        title="咖啡笔记",
        source_type="file",
        source="coffee.md",
        content_hash="hash",
        chunk_count=1,
        imported_at="2026-01-01T00:00:00+00:00",
    )
    chunk = Chunk(chunk_id="doc1:0000", doc_id="doc1", index=0, text=CHUNK_TEXT)
    store.add_chunks(document, [chunk], embedder.embed_documents([CHUNK_TEXT]))
    return store, embedder


def test_answer_cites_real_hit_and_builds_prompt():
    store, embedder = _seeded_store()
    llm = FakeLLMProvider("手冲咖啡建议九十二度水温 [1]。")

    answer = answer_question("手冲咖啡水温多少？", llm=llm, embedder=embedder, vector_store=store)

    assert answer.text == "手冲咖啡建议九十二度水温 [1]。"
    assert len(answer.citations) == 1
    citation = answer.citations[0]
    assert citation.marker == 1
    assert citation.title == "咖啡笔记"
    assert citation.source == "coffee.md"
    assert citation.excerpt == CHUNK_TEXT

    assert len(llm.calls) == 1
    system, user = llm.calls[0]
    assert "[1]" in system  # 系统提示要求标注引用
    assert "手冲咖啡水温多少？" in user
    assert f"[1] 《咖啡笔记》 来源: coffee.md\n{CHUNK_TEXT}" in user


def test_fabricated_citation_marker_is_dropped():
    store, embedder = _seeded_store()
    llm = FakeLLMProvider("第一段 [1]，另外据说 [99] 也是。")

    answer = answer_question("水温多少？", llm=llm, embedder=embedder, vector_store=store)

    assert [c.marker for c in answer.citations] == [1]


def test_empty_knowledge_base_skips_llm_call():
    embedder = FakeEmbeddingProvider()
    llm = FakeLLMProvider("不该被调用")

    answer = answer_question(
        "任何问题", llm=llm, embedder=embedder, vector_store=InMemoryVectorStore()
    )

    assert answer.citations == []
    assert "没有找到" in answer.text
    assert llm.calls == []


def test_empty_question_is_rejected():
    store, embedder = _seeded_store()
    llm = FakeLLMProvider("x")

    with pytest.raises(ValueError):
        answer_question("   ", llm=llm, embedder=embedder, vector_store=store)


def test_section_scoped_answer_only_cites_section_docs():
    store, embedder = _seeded_store()
    # 知识库里再加一篇"茶叶"文档，归入另一个板块
    tea_text = "绿茶的冲泡水温建议八十度。"
    tea_doc = Document(
        doc_id="doc2",
        title="茶叶笔记",
        source_type="file",
        source="tea.md",
        content_hash="hash2",
        chunk_count=1,
        imported_at="2026-01-01T00:00:00+00:00",
    )
    tea_chunk = Chunk(chunk_id="doc2:0000", doc_id="doc2", index=0, text=tea_text)
    store.add_chunks(tea_doc, [tea_chunk], embedder.embed_documents([tea_text]))

    section_repo = InMemorySectionRepository()
    doc_repo = InMemoryDocumentRepository()
    coffee_section = create_section("咖啡", section_repo=section_repo)
    doc_repo.save(
        Document(
            doc_id="doc1",
            title="咖啡笔记",
            source_type="file",
            source="coffee.md",
            content_hash="hash",
            chunk_count=1,
            imported_at="2026-01-01T00:00:00+00:00",
            section_id=coffee_section.section_id,
        )
    )
    doc_repo.save(tea_doc)

    llm = FakeLLMProvider("咖啡水温九十二度 [1]。")
    answer = answer_question(
        "冲泡水温多少？",
        llm=llm,
        embedder=embedder,
        vector_store=store,
        top_k=5,
        section="咖啡",
        section_repo=section_repo,
        doc_repo=doc_repo,
    )

    assert [c.doc_id for c in answer.citations] == ["doc1"]  # 引用只来自板块内的文档

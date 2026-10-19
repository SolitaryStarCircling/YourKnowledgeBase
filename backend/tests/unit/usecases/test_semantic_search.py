"""用例 semantic_search 的测试：全部使用 Mock 端口，不调用真实 API。"""

import pytest

from app.core.entities.models import Chunk, Document
from app.usecases.create_section import create_section
from app.usecases.semantic_search import semantic_search
from tests.fakes import (
    FakeEmbeddingProvider,
    InMemoryDocumentRepository,
    InMemorySectionRepository,
    InMemoryVectorStore,
)


def _filled_store() -> tuple[InMemoryVectorStore, FakeEmbeddingProvider]:
    store = InMemoryVectorStore()
    embedder = FakeEmbeddingProvider()
    doc = Document(
        doc_id="d1",
        title="笔记",
        source_type="file",
        source="note.md",
        content_hash="h",
        chunk_count=2,
        imported_at="2026-01-01T00:00:00+00:00",
    )
    chunks = [
        Chunk(chunk_id="d1:0000", doc_id="d1", index=0, text="向量数据库负责存储嵌入向量"),
        Chunk(chunk_id="d1:0001", doc_id="d1", index=1, text="咖啡的冲泡水温建议在九十度左右"),
    ]
    store.add_chunks(doc, chunks, embedder.embed_documents([c.text for c in chunks]))
    return store, embedder


def test_search_returns_hits_with_source():
    store, embedder = _filled_store()
    hits = semantic_search("咖啡冲泡水温", embedder=embedder, vector_store=store, top_k=1)

    assert len(hits) == 1
    assert "咖啡" in hits[0].text
    assert hits[0].title == "笔记"
    assert hits[0].source == "note.md"


def test_search_respects_top_k():
    store, embedder = _filled_store()
    hits = semantic_search("知识", embedder=embedder, vector_store=store, top_k=2)
    assert len(hits) == 2


def test_empty_query_is_rejected():
    store, embedder = _filled_store()
    with pytest.raises(ValueError):
        semantic_search("   ", embedder=embedder, vector_store=store)


def _section_env() -> tuple:
    """两篇文档分别归入两个板块。"""
    store, embedder = _filled_store()
    section_repo = InMemorySectionRepository()
    doc_repo = InMemoryDocumentRepository()
    tech = create_section("技术", section_repo=section_repo)
    life = create_section("生活", section_repo=section_repo)
    doc_repo.save(
        Document(
            doc_id="d1",
            title="笔记",
            source_type="file",
            source="note.md",
            content_hash="h",
            chunk_count=2,
            imported_at="2026-01-01T00:00:00+00:00",
            section_id=tech.section_id,
        )
    )
    doc_repo.save(
        Document(
            doc_id="d2",
            title="另一篇",
            source_type="file",
            source="other.md",
            content_hash="h2",
            chunk_count=0,
            imported_at="2026-01-01T00:00:00+00:00",
            section_id=life.section_id,
        )
    )
    return store, embedder, section_repo, doc_repo


def test_search_filters_by_section():
    store, embedder, section_repo, doc_repo = _section_env()

    hits = semantic_search(
        "咖啡",
        embedder=embedder,
        vector_store=store,
        section="技术",
        section_repo=section_repo,
        doc_repo=doc_repo,
    )
    assert all(hit.doc_id == "d1" for hit in hits)

    # 生活板块没有 d1 的向量，检索无命中
    assert (
        semantic_search(
            "咖啡",
            embedder=embedder,
            vector_store=store,
            section="生活",
            section_repo=section_repo,
            doc_repo=doc_repo,
        )
        == []
    )


def test_search_empty_section_returns_nothing():
    store, embedder, section_repo, doc_repo = _section_env()
    create_section("空板块", section_repo=section_repo)

    hits = semantic_search(
        "咖啡",
        embedder=embedder,
        vector_store=store,
        section="空板块",
        section_repo=section_repo,
        doc_repo=doc_repo,
    )

    assert hits == []


def test_search_with_section_without_repos_is_rejected():
    store, embedder = _filled_store()
    with pytest.raises(ValueError, match="section_repo"):
        semantic_search("咖啡", embedder=embedder, vector_store=store, section="技术")

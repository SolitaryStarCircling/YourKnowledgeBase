"""用例 import_document 的测试：全部使用 Mock 端口，不调用真实 API。"""

import pytest

from app.core.entities.models import ParsedDocument
from app.usecases.create_section import create_section
from app.usecases.import_document import import_document
from tests.fakes import (
    FakeChunker,
    FakeEmbeddingProvider,
    FakeParser,
    InMemoryDocumentRepository,
    InMemorySectionRepository,
    InMemoryVectorStore,
)


def _build_env(text: str):
    parser = FakeParser({"note.md": ParsedDocument(title="测试笔记", text=text)})
    chunker = FakeChunker()
    embedder = FakeEmbeddingProvider()
    store = InMemoryVectorStore()
    repo = InMemoryDocumentRepository()
    return parser, chunker, embedder, store, repo


def _run(parser, chunker, embedder, store, repo, **kwargs):
    return import_document(
        "note.md",
        parser=parser,
        chunker=chunker,
        embedder=embedder,
        vector_store=store,
        doc_repo=repo,
        **kwargs,
    )


def test_import_new_document_creates_index():
    parser, chunker, embedder, store, repo = _build_env("第一段\n\n第二段")
    result = _run(parser, chunker, embedder, store, repo)

    assert result.status == "created"
    assert result.title == "测试笔记"
    assert result.chunk_count == 2
    assert len(store.rows) == 2
    assert repo.get_by_source("note.md") is not None
    assert embedder.document_calls == 1


def test_reimport_unchanged_document_skips_embedding():
    parser, chunker, embedder, store, repo = _build_env("第一段\n\n第二段")
    _run(parser, chunker, embedder, store, repo)
    result = _run(parser, chunker, embedder, store, repo)

    assert result.status == "skipped"
    # 内容没变：绝不重复嵌入，这就是增量更新省 API 钱的意义
    assert embedder.document_calls == 1
    assert len(store.rows) == 2


def test_reimport_changed_document_reindexes_and_reuses_doc_id():
    parser, chunker, embedder, store, repo = _build_env("第一段\n\n第二段")
    first = _run(parser, chunker, embedder, store, repo)

    parser.documents["note.md"] = ParsedDocument(
        title="测试笔记", text="第一段改写\n\n第二段\n\n新增第三段"
    )
    result = _run(parser, chunker, embedder, store, repo)

    assert result.status == "updated"
    assert result.doc_id == first.doc_id  # 复用原 id，引用保持稳定
    assert result.chunk_count == 3
    assert store.deleted_doc_ids == [first.doc_id]  # 旧向量被清掉，无残留
    assert len(store.rows) == 3
    assert embedder.document_calls == 2


def test_empty_document_is_rejected():
    parser, chunker, embedder, store, repo = _build_env("   ")
    with pytest.raises(ValueError):
        _run(parser, chunker, embedder, store, repo)


def test_import_into_section_records_section_id():
    parser, chunker, embedder, store, repo = _build_env("第一段")
    section_repo = InMemorySectionRepository()
    _run(parser, chunker, embedder, store, repo)  # 先建一个没板块的

    section = create_section("技术笔记", section_repo=section_repo)
    parser.documents["note.md"] = ParsedDocument(title="测试笔记", text="第一段改写")
    result = _run(
        parser, chunker, embedder, store, repo, section_repo=section_repo, section="技术笔记"
    )

    assert result.status == "updated"
    assert repo.get_by_source("note.md").section_id == section.section_id


def test_import_with_unknown_section_is_rejected():
    parser, chunker, embedder, store, repo = _build_env("第一段")
    with pytest.raises(ValueError, match="板块不存在"):
        _run(
            parser,
            chunker,
            embedder,
            store,
            repo,
            section_repo=InMemorySectionRepository(),
            section="没有这个",
        )


def test_section_only_change_updates_metadata_without_reembedding():
    parser, chunker, embedder, store, repo = _build_env("第一段")
    section_repo = InMemorySectionRepository()
    create_section("技术笔记", section_repo=section_repo)
    first = _run(
        parser, chunker, embedder, store, repo, section_repo=section_repo, section="技术笔记"
    )

    result = _run(
        parser, chunker, embedder, store, repo, section_repo=section_repo, section="技术笔记"
    )
    assert result.status == "skipped"

    create_section("生活笔记", section_repo=section_repo)
    moved = _run(
        parser, chunker, embedder, store, repo, section_repo=section_repo, section="生活笔记"
    )

    assert moved.status == "updated"
    assert moved.doc_id == first.doc_id
    assert embedder.document_calls == 1  # 只换板块：绝不重新嵌入
    assert repo.get_by_source("note.md").section_id is not None


def test_reimport_without_section_keeps_original_section():
    parser, chunker, embedder, store, repo = _build_env("第一段")
    section_repo = InMemorySectionRepository()
    section = create_section("技术笔记", section_repo=section_repo)
    _run(parser, chunker, embedder, store, repo, section_repo=section_repo, section="技术笔记")

    parser.documents["note.md"] = ParsedDocument(title="测试笔记", text="内容改了")
    result = _run(parser, chunker, embedder, store, repo, section_repo=section_repo)

    assert result.status == "updated"
    assert repo.get_by_source("note.md").section_id == section.section_id

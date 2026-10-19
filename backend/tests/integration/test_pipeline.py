"""最小闭环集成测试：真实 LanceDB + SQLite（临时目录）+ 确定性嵌入替身（不出网）。

覆盖：导入 -> 解析 -> 分块 -> 嵌入 -> 存储 -> 语义搜索（片段 + 来源），
增量跳过、内容变更重建、按 doc_id 删除，以及 RAG 问答（回答 + 真实引用）。
"""

from pathlib import Path

from app.infra.chunking.fixed_size_chunker import FixedSizeChunker
from app.infra.db.sqlite_document_repository import SqliteDocumentRepository
from app.infra.db.sqlite_section_repository import SqliteSectionRepository
from app.infra.parsers.composite_parser import CompositeParser
from app.infra.parsers.markdown_parser import MarkdownParser
from app.infra.parsers.pdf_parser import PdfParser
from app.infra.vectordb.lancedb_store import LanceDbVectorStore
from app.usecases.answer_question import answer_question
from app.usecases.create_section import create_section
from app.usecases.delete_section import delete_section
from app.usecases.import_document import import_document
from app.usecases.semantic_search import semantic_search
from app.usecases.update_section import update_section
from tests.fakes import FakeEmbeddingProvider, FakeLLMProvider, make_pdf_bytes

COFFEE_NOTE = """# 咖啡冲泡笔记

咖啡的冲泡水温建议在九十度左右。水温过高会带来苦涩味，水温偏低则萃取不足。
"""

VECTOR_NOTE = """# 向量数据库

向量数据库负责存储嵌入向量，并提供 Top-K 近邻检索能力，是语义搜索的基础设施。
"""


def _services(tmp_path: Path):
    return (
        CompositeParser([MarkdownParser(), PdfParser()]),
        FixedSizeChunker(chunk_size=40, overlap=10),
        FakeEmbeddingProvider(),
        LanceDbVectorStore(tmp_path / "vectordb"),
        SqliteDocumentRepository(tmp_path / "meta.db"),
    )


def test_full_loop_import_then_search_with_source(tmp_path: Path):
    coffee_path = tmp_path / "coffee.md"
    vector_path = tmp_path / "vector.md"
    coffee_path.write_text(COFFEE_NOTE, encoding="utf-8")
    vector_path.write_text(VECTOR_NOTE, encoding="utf-8")

    parser, chunker, embedder, store, repo = _services(tmp_path)
    result = import_document(
        str(coffee_path),
        parser=parser,
        chunker=chunker,
        embedder=embedder,
        vector_store=store,
        doc_repo=repo,
    )
    import_document(
        str(vector_path),
        parser=parser,
        chunker=chunker,
        embedder=embedder,
        vector_store=store,
        doc_repo=repo,
    )

    assert result.status == "created"
    assert result.chunk_count >= 2

    hits = semantic_search("咖啡冲泡的水温", embedder=embedder, vector_store=store, top_k=3)
    assert hits, "检索不应为空"
    top = hits[0]
    assert "咖啡" in top.text
    assert top.title == "咖啡冲泡笔记"
    assert top.source == str(coffee_path)


def test_incremental_skip_then_update_then_delete(tmp_path: Path):
    coffee_path = tmp_path / "coffee.md"
    coffee_path.write_text(COFFEE_NOTE, encoding="utf-8")

    parser, chunker, embedder, store, repo = _services(tmp_path)
    first = import_document(
        str(coffee_path),
        parser=parser,
        chunker=chunker,
        embedder=embedder,
        vector_store=store,
        doc_repo=repo,
    )

    # 1) 内容未变：跳过且不重复嵌入
    second = import_document(
        str(coffee_path),
        parser=parser,
        chunker=chunker,
        embedder=embedder,
        vector_store=store,
        doc_repo=repo,
    )
    assert second.status == "skipped"
    assert embedder.document_calls == 1

    # 2) 内容变更：原 doc_id 重建索引
    coffee_path.write_text("# 咖啡冲泡笔记\n\n手冲咖啡更推荐九十二度的水温。\n", encoding="utf-8")
    third = import_document(
        str(coffee_path),
        parser=parser,
        chunker=chunker,
        embedder=embedder,
        vector_store=store,
        doc_repo=repo,
    )
    assert third.status == "updated"
    assert third.doc_id == first.doc_id
    assert embedder.document_calls == 2

    hits = semantic_search("手冲咖啡水温", embedder=embedder, vector_store=store, top_k=3)
    assert "手冲咖啡" in hits[0].text

    # 3) 删除：向量与元数据一起清掉，检索不再命中
    store.delete_by_doc(first.doc_id)
    repo.delete(first.doc_id)
    hits = semantic_search("手冲咖啡水温", embedder=embedder, vector_store=store, top_k=3)
    assert all(hit.doc_id != first.doc_id for hit in hits)


def test_rag_answer_with_verified_citations(tmp_path: Path):
    coffee_path = tmp_path / "coffee.md"
    coffee_path.write_text(COFFEE_NOTE, encoding="utf-8")

    parser, chunker, embedder, store, repo = _services(tmp_path)
    import_document(
        str(coffee_path),
        parser=parser,
        chunker=chunker,
        embedder=embedder,
        vector_store=store,
        doc_repo=repo,
    )

    llm = FakeLLMProvider("咖啡冲泡水温建议九十度左右 [1]，另有说法称 [42] 也对。")
    answer = answer_question(
        "咖啡冲泡的水温是多少？", llm=llm, embedder=embedder, vector_store=store, top_k=3
    )

    assert "九十度" in answer.text
    # [42] 超出检索范围属编造，被丢弃；引用只来自真实片段
    assert [c.marker for c in answer.citations] == [1]
    citation = answer.citations[0]
    assert citation.title == "咖啡冲泡笔记"
    assert citation.source == str(coffee_path)
    assert "咖啡" in citation.excerpt


def test_pdf_import_then_search_with_source(tmp_path: Path):
    pdf_path = tmp_path / "coffee.pdf"
    pdf_path.write_bytes(
        make_pdf_bytes("Coffee Notes", "Coffee brewing needs ninety two degree water.")
    )

    parser, chunker, embedder, store, repo = _services(tmp_path)
    result = import_document(
        str(pdf_path),
        parser=parser,
        chunker=chunker,
        embedder=embedder,
        vector_store=store,
        doc_repo=repo,
    )

    assert result.status == "created"
    assert result.title == "Coffee Notes"

    hits = semantic_search("coffee brewing water", embedder=embedder, vector_store=store, top_k=3)
    assert hits
    assert hits[0].title == "Coffee Notes"
    assert hits[0].source == str(pdf_path)
    assert "Coffee" in hits[0].text


def test_section_flow_import_filter_rename_delete(tmp_path: Path):
    coffee_path = tmp_path / "coffee.md"
    vector_path = tmp_path / "vector.md"
    coffee_path.write_text(COFFEE_NOTE, encoding="utf-8")
    vector_path.write_text(VECTOR_NOTE, encoding="utf-8")

    parser, chunker, embedder, store, repo = _services(tmp_path)
    section_repo = SqliteSectionRepository(tmp_path / "meta.db")
    create_section("生活", section_repo=section_repo)
    create_section("技术", section_repo=section_repo)

    import_document(
        str(coffee_path),
        parser=parser,
        chunker=chunker,
        embedder=embedder,
        vector_store=store,
        doc_repo=repo,
        section_repo=section_repo,
        section="生活",
    )
    import_document(
        str(vector_path),
        parser=parser,
        chunker=chunker,
        embedder=embedder,
        vector_store=store,
        doc_repo=repo,
        section_repo=section_repo,
        section="技术",
    )

    def search_in(section: str):
        return semantic_search(
            "冲泡水温",
            embedder=embedder,
            vector_store=store,
            top_k=3,
            section=section,
            section_repo=section_repo,
            doc_repo=repo,
        )

    # 板块过滤下推：只命中板块内的文档
    life_hits = search_in("生活")
    assert life_hits
    assert all(hit.doc_id == repo.get_by_source(str(coffee_path)).doc_id for hit in life_hits)
    assert all(hit.source == str(coffee_path) for hit in life_hits)
    # 技术板块只可能命中技术板块的文档（即使相似度低也不会越界）
    tech_hits = search_in("技术")
    assert tech_hits
    assert all(hit.source == str(vector_path) for hit in tech_hits)

    # 重命名不动文档归属（内部键是 section_id）
    update_section("生活", section_repo=section_repo, new_name="日常")
    assert all(hit.source == str(coffee_path) for hit in search_in("日常"))

    # 删除板块：文档回归未分板块，向量仍在，全库检索能命中
    delete_section("日常", section_repo=section_repo, doc_repo=repo)
    assert repo.get_by_source(str(coffee_path)).section_id is None
    hits = semantic_search("冲泡水温", embedder=embedder, vector_store=store, top_k=3)
    assert any(hit.source == str(coffee_path) for hit in hits)

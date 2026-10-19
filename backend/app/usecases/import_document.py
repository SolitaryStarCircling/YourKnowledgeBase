"""用例：导入一篇文档（解析 → 增量判定 → 分块 → 嵌入 → 存储）。

一个用例一个文件；只依赖领域层的实体与端口，具体实现由入口层注入。
"""

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import uuid4

from app.core.entities.models import Chunk, Document
from app.core.ports.chunker import Chunker
from app.core.ports.document_repository import DocumentRepository
from app.core.ports.embedding import EmbeddingProvider
from app.core.ports.parser import Parser
from app.core.ports.section_repository import SectionRepository
from app.core.ports.vector_store import VectorStore
from app.core.services.hashing import compute_content_hash
from app.core.services.sections import find_section_by_name


@dataclass(frozen=True)
class ImportResult:
    """导入结果，供入口层展示。"""

    status: str  # "created" | "updated" | "skipped"
    doc_id: str
    title: str
    chunk_count: int


def import_document(
    source: str,
    *,
    parser: Parser,
    chunker: Chunker,
    embedder: EmbeddingProvider,
    vector_store: VectorStore,
    doc_repo: DocumentRepository,
    section_repo: SectionRepository | None = None,
    section: str | None = None,
) -> ImportResult:
    """导入文档；内容哈希未变则直接跳过，避免重复嵌入的 API 开销。

    section 指定所属板块（按名称）；不传则沿用文档原有板块。
    """
    section_id = _resolve_section_id(section, section_repo)

    parsed = parser.parse(source)
    content_hash = compute_content_hash(parsed.text)
    existing = doc_repo.get_by_source(source)

    if existing is not None and existing.content_hash == content_hash:
        # 内容未变只可能需要换板块：改元数据即可，不重新嵌入
        if section_id is not None and existing.section_id != section_id:
            doc_repo.save(replace(existing, section_id=section_id))
            return ImportResult(
                status="updated",
                doc_id=existing.doc_id,
                title=existing.title,
                chunk_count=existing.chunk_count,
            )
        return ImportResult(
            status="skipped",
            doc_id=existing.doc_id,
            title=existing.title,
            chunk_count=existing.chunk_count,
        )

    segments = chunker.chunk(parsed.text)
    if not segments:
        raise ValueError(f"文档没有可索引的文本内容：{source}")

    # 内容变更时复用原 doc_id，先清旧向量与旧元数据，防止残留脏数据
    doc_id = existing.doc_id if existing is not None else uuid4().hex
    if existing is not None:
        vector_store.delete_by_doc(existing.doc_id)
        doc_repo.delete(existing.doc_id)

    chunks = [
        Chunk(chunk_id=f"{doc_id}:{seg.index:04d}", doc_id=doc_id, index=seg.index, text=seg.text)
        for seg in segments
    ]
    vectors = embedder.embed_documents([chunk.text for chunk in chunks])

    # 没指定板块时沿用原文档的板块归属
    target_section_id = (
        section_id if section_id is not None else (existing.section_id if existing else None)
    )
    document = Document(
        doc_id=doc_id,
        title=parsed.title,
        source_type="url" if source.startswith(("http://", "https://")) else "file",
        source=source,
        content_hash=content_hash,
        chunk_count=len(chunks),
        imported_at=datetime.now(UTC).isoformat(),
        section_id=target_section_id,
    )
    vector_store.add_chunks(document, chunks, vectors)
    doc_repo.save(document)

    return ImportResult(
        status="updated" if existing is not None else "created",
        doc_id=doc_id,
        title=document.title,
        chunk_count=len(chunks),
    )


def _resolve_section_id(
    section: str | None,
    section_repo: SectionRepository | None,
) -> str | None:
    """把板块名称解析成 section_id；未指定板块返回 None。"""
    if section is None:
        return None
    if section_repo is None:
        raise ValueError("指定板块时必须提供 section_repo")
    return find_section_by_name(section, section_repo=section_repo).section_id

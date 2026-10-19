"""用例：语义搜索（查询向量化 → Top-K 召回，返回片段 + 来源）。"""

from app.core.entities.models import SearchHit
from app.core.ports.document_repository import DocumentRepository
from app.core.ports.embedding import EmbeddingProvider
from app.core.ports.section_repository import SectionRepository
from app.core.ports.vector_store import VectorStore
from app.core.services.sections import find_section_by_name


def semantic_search(
    query: str,
    *,
    embedder: EmbeddingProvider,
    vector_store: VectorStore,
    top_k: int = 5,
    section: str | None = None,
    section_repo: SectionRepository | None = None,
    doc_repo: DocumentRepository | None = None,
) -> list[SearchHit]:
    """对查询做语义检索，返回得分降序的相关片段（含来源）。

    section 限定板块范围（按名称）；板块内没有文档时直接返回空。
    """
    query = query.strip()
    if not query:
        raise ValueError("查询内容不能为空")
    if top_k <= 0:
        raise ValueError("top_k 必须为正数")

    doc_ids = _resolve_doc_ids(section, section_repo, doc_repo)
    if doc_ids is not None and not doc_ids:
        return []

    vector = embedder.embed_query(query)
    return vector_store.search(vector, top_k, doc_ids=doc_ids)


def _resolve_doc_ids(
    section: str | None,
    section_repo: SectionRepository | None,
    doc_repo: DocumentRepository | None,
) -> list[str] | None:
    """把板块范围解析成文档 id 白名单；不限范围返回 None。"""
    if section is None:
        return None
    if section_repo is None or doc_repo is None:
        raise ValueError("按板块检索需要提供 section_repo 与 doc_repo")
    found = find_section_by_name(section, section_repo=section_repo)
    return [doc.doc_id for doc in doc_repo.list_by_section(found.section_id)]

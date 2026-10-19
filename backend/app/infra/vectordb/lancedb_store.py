"""向量存储（VectorStore 端口实现）：LanceDB 嵌入式向量库，文件即库、零服务。"""

from collections.abc import Sequence
from pathlib import Path

import lancedb

from app.core.entities.models import Chunk, Document, SearchHit
from app.core.ports.vector_store import VectorStore

_TABLE_NAME = "chunks"


class LanceDbVectorStore(VectorStore):
    """表在第一次写入时创建（schema 由首批数据推断），读到空库返回空结果。"""

    def __init__(self, db_path: str | Path) -> None:
        self._db = lancedb.connect(str(db_path))

    def _table_exists(self) -> bool:
        # list_tables() 返回响应对象，表名列表在 .tables 里
        return _TABLE_NAME in self._db.list_tables().tables

    def add_chunks(
        self,
        document: Document,
        chunks: Sequence[Chunk],
        vectors: Sequence[Sequence[float]],
    ) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks 与 vectors 数量不一致")
        if not chunks:
            return

        rows = [
            {
                "chunk_id": chunk.chunk_id,
                "doc_id": chunk.doc_id,
                "index": chunk.index,
                "text": chunk.text,
                "title": document.title,
                "source": document.source,
                "vector": list(vector),
            }
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        if self._table_exists():
            self._db.open_table(_TABLE_NAME).add(rows)
        else:
            self._db.create_table(_TABLE_NAME, data=rows)

    def search(
        self,
        vector: Sequence[float],
        top_k: int,
        *,
        doc_ids: Sequence[str] | None = None,
    ) -> list[SearchHit]:
        if doc_ids is not None and not doc_ids:
            return []
        if not self._table_exists():
            return []

        query = self._db.open_table(_TABLE_NAME).search(list(vector))
        if doc_ids is not None:
            query = query.where(f"doc_id IN ({_id_list_sql(doc_ids)})")
        rows = query.limit(top_k).to_list()
        return [
            SearchHit(
                chunk_id=row["chunk_id"],
                doc_id=row["doc_id"],
                index=int(row["index"]),
                text=row["text"],
                title=row["title"],
                source=row["source"],
                score=_distance_to_score(row),
            )
            for row in rows
        ]

    def delete_by_doc(self, doc_id: str) -> None:
        if not self._table_exists():
            return
        self._db.open_table(_TABLE_NAME).delete(where=f"doc_id = '{doc_id}'")


def _distance_to_score(row: dict) -> float:
    """把 LanceDB 的距离转成"越大越相关"的得分，便于上层直接排序展示。"""
    distance = row.get("_distance")
    if distance is None:
        return float(row.get("score", 0.0))
    return 1.0 / (1.0 + float(distance))


def _id_list_sql(doc_ids: Sequence[str]) -> str:
    """把 doc_id 列表拼成 SQL IN 列表（单引号转义防注入）。"""
    escaped = [doc_id.replace("'", "''") for doc_id in doc_ids]
    return ", ".join(f"'{item}'" for item in escaped)

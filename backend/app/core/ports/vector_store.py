"""端口：向量存储。实现放 infra/vectordb/（LanceDB）。"""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.core.entities.models import Chunk, Document, SearchHit


class VectorStore(ABC):
    """向量的增 / 删 / Top-K 检索（按 doc_id 批量清理）。"""

    @abstractmethod
    def add_chunks(
        self,
        document: Document,
        chunks: Sequence[Chunk],
        vectors: Sequence[Sequence[float]],
    ) -> None:
        """写入一篇文档的全部片段与对应向量（三者长度一致、顺序对应）。"""

    @abstractmethod
    def search(
        self,
        vector: Sequence[float],
        top_k: int,
        *,
        doc_ids: Sequence[str] | None = None,
    ) -> list[SearchHit]:
        """Top-K 近邻检索，返回相关片段 + 来源，得分越高越相关。

        doc_ids 限定文档范围（板块过滤下推）：None 不限，空序列无命中。
        """

    @abstractmethod
    def delete_by_doc(self, doc_id: str) -> None:
        """删除某文档的全部向量（增量更新 / 删除文档时调用）。"""

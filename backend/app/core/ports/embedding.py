"""端口：文本向量化。实现放 infra/providers/（这是全系统出网点之一）。"""

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """文本 -> 向量。文档与查询走不同方法，便于不同厂商的差异化处理。"""

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """批量把文档片段转为向量，返回顺序与输入一致。"""

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """把查询文本转为向量。"""

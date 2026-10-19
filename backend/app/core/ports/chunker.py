"""端口：文本分块器。实现放 infra/chunking/（规则在 core/services/chunking.py）。"""

from abc import ABC, abstractmethod

from app.core.entities.models import TextSegment


class Chunker(ABC):
    """把正文切成有序片段（含序号定位信息）。"""

    @abstractmethod
    def chunk(self, text: str) -> list[TextSegment]:
        """返回按顺序编号的文本片段。"""

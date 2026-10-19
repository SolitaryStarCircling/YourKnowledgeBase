"""端口：文档解析器。实现放 infra/parsers/。"""

from abc import ABC, abstractmethod

from app.core.entities.models import ParsedDocument


class Parser(ABC):
    """把来源（文件 / URL）解析为结构化文本。"""

    @abstractmethod
    def can_parse(self, source: str) -> bool:
        """判断本解析器是否支持该来源。"""

    @abstractmethod
    def parse(self, source: str) -> ParsedDocument:
        """解析来源，返回标题与正文。"""

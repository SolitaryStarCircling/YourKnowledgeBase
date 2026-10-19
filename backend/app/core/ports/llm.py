"""端口：大模型文本生成。实现放 infra/providers/（这是全系统出网点之二）。"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """提示词 -> 回答文本。只负责生成，检索与引用组装在用例层完成。"""

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """给定系统提示与用户提示，返回回答文本。"""

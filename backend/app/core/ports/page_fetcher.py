"""端口：网页抓取。实现放 infra/providers/（这是全系统出网点之三）。

单独成端口的原因：出网白名单要求网络请求只出现在 infra/providers/，
而网页解析（HTML -> 文本）属于解析器职责，两者必须分开。
"""

from abc import ABC, abstractmethod


class PageFetcher(ABC):
    """URL -> 网页 HTML 文本。只负责抓取，不理解内容。"""

    @abstractmethod
    def fetch(self, url: str) -> str:
        """抓取 URL 返回 HTML 文本；失败时抛 RuntimeError。"""

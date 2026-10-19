"""HTTP 网页抓取适配器（PageFetcher 端口实现）。

这是全系统仅有的三处出网点之一（另两处是嵌入与 LLM）。
安全红线：绝不把 URL 响应正文写日志，异常信息只保留状态码与异常类名。
"""

import httpx

from app.core.ports.page_fetcher import PageFetcher


class HttpPageFetcher(PageFetcher):
    """httpx GET 抓取网页 HTML。"""

    def __init__(self, timeout: float = 15.0) -> None:
        self._timeout = timeout

    def fetch(self, url: str) -> str:
        try:
            response = httpx.get(url, timeout=self._timeout, follow_redirects=True)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as exc:
            # from None 断开异常链，防止底层异常意外带出请求细节
            raise RuntimeError(f"网页抓取失败：HTTP {exc.response.status_code}") from None
        except httpx.HTTPError as exc:
            raise RuntimeError(f"网页抓取网络错误：{exc.__class__.__name__}") from None

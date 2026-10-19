"""OpenAI 兼容嵌入 API 适配器（EmbeddingProvider 端口实现）。

这是全系统仅有的两处出网点之一（另一处是 RAG 生成）。
安全红线：密钥只放请求头，绝不进入日志与异常信息。
"""

import httpx

from app.core.ports.embedding import EmbeddingProvider


class OpenAiCompatibleEmbedding(EmbeddingProvider):
    """对接任何兼容 POST {base_url}/embeddings 的厂商，不绑定具体供应商。"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._post({"input": texts, "model": self._model})
        # 部分厂商不保证顺序返回，按 index 归位
        items = sorted(response["data"], key=lambda item: item["index"])
        return [item["embedding"] for item in items]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    def _post(self, payload: dict) -> dict:
        try:
            response = httpx.post(
                f"{self._base_url}/embeddings",
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=self._timeout,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            # from None 断开异常链，防止底层异常意外带出请求细节
            raise RuntimeError(f"嵌入 API 调用失败：HTTP {exc.response.status_code}") from None
        except httpx.HTTPError as exc:
            raise RuntimeError(f"嵌入 API 网络错误：{exc.__class__.__name__}") from None

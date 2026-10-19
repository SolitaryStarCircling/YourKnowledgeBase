"""OpenAI 兼容对话 API 适配器（LLMProvider 端口实现）。

这是全系统仅有的两处出网点之一（另一处是嵌入向量化）。
安全红线：密钥只放请求头，绝不进入日志与异常信息。
"""

import httpx

from app.core.ports.llm import LLMProvider


class OpenAiCompatibleLlm(LLMProvider):
    """对接任何兼容 POST {base_url}/chat/completions 的厂商，不绑定具体供应商。"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    def complete(self, system: str, user: str) -> str:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        response = self._post(payload)
        return response["choices"][0]["message"]["content"]

    def _post(self, payload: dict) -> dict:
        try:
            response = httpx.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=self._timeout,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            # from None 断开异常链，防止底层异常意外带出请求细节
            raise RuntimeError(f"LLM API 调用失败：HTTP {exc.response.status_code}") from None
        except httpx.HTTPError as exc:
            raise RuntimeError(f"LLM API 网络错误：{exc.__class__.__name__}") from None

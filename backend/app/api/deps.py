"""API 依赖注入：容器获取 + BYOK 会话密钥头。

会话密钥只进内存（随请求传给组装工厂），不落盘、不进日志、不进响应。
"""

from collections.abc import Mapping
from typing import Annotated

from fastapi import Depends, Header, Request

from app.bootstrap import ServiceContainer


def get_container(request: Request) -> ServiceContainer:
    return request.app.state.container


def session_secrets(
    x_embedding_api_key: Annotated[str | None, Header()] = None,
    x_llm_api_key: Annotated[str | None, Header()] = None,
) -> Mapping[str, str] | None:
    """把 BYOK 会话头映射为密钥覆盖（会话模式：仅本次请求有效）。"""
    session: dict[str, str] = {}
    if x_embedding_api_key:
        session["EMBEDDING_API_KEY"] = x_embedding_api_key
    if x_llm_api_key:
        session["LLM_API_KEY"] = x_llm_api_key
    return session or None


ContainerDep = Annotated[ServiceContainer, Depends(get_container)]
SessionDep = Annotated[Mapping[str, str] | None, Depends(session_secrets)]

"""配置加载：读取优先级 运行时输入（会话）> 环境变量 > .env 文件。

安全红线：本模块任何报错信息都不回显密钥内容。
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from app.core.ports.local_config_store import LocalConfigStore
from app.core.services.secrets import resolve_value
from app.infra.secrets.env_file_config_store import EnvFileConfigStore

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


@dataclass(frozen=True)
class EmbeddingConfig:
    api_key: str
    base_url: str
    model: str


@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    base_url: str
    model: str


def load_embedding_config(
    *,
    session_secrets: Mapping[str, str] | None = None,
    store: LocalConfigStore | None = None,
) -> EmbeddingConfig:
    """读取嵌入配置；缺失密钥时抛出带指引的友好错误。"""
    api_key = _require(
        "EMBEDDING_API_KEY",
        session_secrets=session_secrets,
        store=store,
    )
    return EmbeddingConfig(
        api_key=api_key,
        base_url=_get("EMBEDDING_BASE_URL", session_secrets, store),
        model=_get("EMBEDDING_MODEL", session_secrets, store),
    )


def load_llm_config(
    *,
    session_secrets: Mapping[str, str] | None = None,
    store: LocalConfigStore | None = None,
) -> LLMConfig:
    """读取问答生成配置；缺失密钥时抛出带指引的友好错误。"""
    api_key = _require("LLM_API_KEY", session_secrets=session_secrets, store=store)
    return LLMConfig(
        api_key=api_key,
        base_url=_get("LLM_BASE_URL", session_secrets, store),
        model=_get("LLM_MODEL", session_secrets, store),
    )


def _get(
    name: str,
    session_secrets: Mapping[str, str] | None,
    store: LocalConfigStore | None,
) -> str:
    value, _ = resolve_value(
        name,
        session=session_secrets or {},
        env=os.environ,
        file_values=_store(store).load_all(),
    )
    return value


def _require(
    name: str,
    *,
    session_secrets: Mapping[str, str] | None,
    store: LocalConfigStore | None,
) -> str:
    value = _get(name, session_secrets, store)
    if not value:
        raise RuntimeError(
            f"未配置 {name}。可选方式：① 命令加 --api-key 参数仅本次会话使用；"
            "② 运行 config init 生成 backend/.env 后手动填入（不进 git）；"
            "③ 设置同名环境变量。"
        )
    return value


def _store(store: LocalConfigStore | None) -> LocalConfigStore:
    return store if store is not None else EnvFileConfigStore(_ENV_FILE)

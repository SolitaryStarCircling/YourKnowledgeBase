"""配置加载测试：会话 > 环境变量 > .env 的优先级与"报错不回显 Key"红线。"""

import pytest

from app.config import load_embedding_config, load_llm_config
from tests.fakes import InMemoryConfigStore

RAW_KEY = "sk-super-secret-key-9527"
ENV_KEY = "sk-from-env-1111"
FILE_KEY = "sk-from-file-2222"


@pytest.fixture()
def clean_env(monkeypatch):
    """清掉测试环境里可能存在的真实配置，避免用例互相污染。"""
    for name in (
        "LLM_API_KEY",
        "LLM_BASE_URL",
        "LLM_MODEL",
        "EMBEDDING_API_KEY",
        "EMBEDDING_BASE_URL",
        "EMBEDDING_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)


class TestPriority:
    def test_session_wins_over_env_and_file(self, clean_env, monkeypatch):
        monkeypatch.setenv("EMBEDDING_API_KEY", ENV_KEY)
        store = InMemoryConfigStore()
        store.set("EMBEDDING_API_KEY", FILE_KEY)
        cfg = load_embedding_config(session_secrets={"EMBEDDING_API_KEY": RAW_KEY}, store=store)
        assert cfg.api_key == RAW_KEY

    def test_env_wins_over_file(self, clean_env, monkeypatch):
        monkeypatch.setenv("EMBEDDING_API_KEY", ENV_KEY)
        store = InMemoryConfigStore()
        store.set("EMBEDDING_API_KEY", FILE_KEY)
        cfg = load_embedding_config(store=store)
        assert cfg.api_key == ENV_KEY

    def test_file_used_when_env_absent(self, clean_env):
        store = InMemoryConfigStore()
        store.set("LLM_API_KEY", FILE_KEY)
        cfg = load_llm_config(store=store)
        assert cfg.api_key == FILE_KEY

    def test_defaults_fill_base_url_and_model(self, clean_env):
        store = InMemoryConfigStore()
        cfg = load_llm_config(session_secrets={"LLM_API_KEY": RAW_KEY}, store=store)
        assert cfg.base_url == "https://api.openai.com/v1"
        assert cfg.model == "gpt-4o-mini"

    def test_file_can_override_model(self, clean_env):
        store = InMemoryConfigStore()
        store.set("LLM_MODEL", "my-model")
        cfg = load_llm_config(session_secrets={"LLM_API_KEY": RAW_KEY}, store=store)
        assert cfg.model == "my-model"


class TestMissingKeyError:
    def test_missing_key_raises_friendly_error(self, clean_env):
        store = InMemoryConfigStore()
        with pytest.raises(RuntimeError, match="EMBEDDING_API_KEY"):
            load_embedding_config(store=store)

    def test_error_lists_all_three_options(self, clean_env):
        store = InMemoryConfigStore()
        with pytest.raises(RuntimeError) as exc_info:
            load_llm_config(store=store)
        message = str(exc_info.value)
        assert "--api-key" in message
        assert "config init" in message
        assert "环境变量" in message

    def test_error_does_not_echo_configured_keys(self, clean_env, monkeypatch):
        """红线：缺 LLM Key 的报错里不能出现已在别处配置的 Key 原文。"""
        monkeypatch.setenv("EMBEDDING_API_KEY", RAW_KEY)
        store = InMemoryConfigStore()
        store.set("LLM_BASE_URL", "https://my.example.com/v1")
        with pytest.raises(RuntimeError) as exc_info:
            load_llm_config(store=store)
        assert RAW_KEY not in str(exc_info.value)

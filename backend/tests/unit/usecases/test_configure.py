"""配置用例测试：Key 拒落盘、非密写入、状态展示脱敏（一律 Mock 端口，不出网）。"""

import pytest

from app.usecases.clear_provider_config import clear_provider_config
from app.usecases.configure_provider import configure_provider
from app.usecases.show_config_status import show_config_status
from tests.fakes import InMemoryConfigStore

RAW_KEY = "sk-super-secret-key-9527"


class TestConfigureProvider:
    def test_writes_non_secret_to_store(self):
        store = InMemoryConfigStore()
        var = configure_provider("llm_model", "my-model", store=store)
        assert var == "LLM_MODEL"
        assert store.load_all()["LLM_MODEL"] == "my-model"

    def test_refuses_api_key(self):
        store = InMemoryConfigStore()
        with pytest.raises(ValueError, match="不允许写入"):
            configure_provider("LLM_API_KEY", RAW_KEY, store=store)
        assert RAW_KEY not in store.load_all().values()

    def test_refusal_error_does_not_leak_key(self):
        store = InMemoryConfigStore()
        with pytest.raises(ValueError) as exc_info:
            configure_provider("EMBEDDING_API_KEY", RAW_KEY, store=store)
        assert RAW_KEY not in str(exc_info.value)

    def test_refusal_error_points_to_alternatives(self):
        store = InMemoryConfigStore()
        with pytest.raises(ValueError, match="--api-key"):
            configure_provider("LLM_API_KEY", RAW_KEY, store=store)

    @pytest.mark.parametrize("name", ["LLM_API_KEY", "EMBEDDING_API_KEY"])
    def test_all_key_vars_refused(self, name):
        store = InMemoryConfigStore()
        with pytest.raises(ValueError):
            configure_provider(name, RAW_KEY, store=store)

    def test_empty_value_rejected_with_hint(self):
        store = InMemoryConfigStore()
        with pytest.raises(ValueError, match="config clear"):
            configure_provider("LLM_MODEL", "   ", store=store)

    def test_unknown_var_rejected(self):
        store = InMemoryConfigStore()
        with pytest.raises(ValueError, match="不支持的配置项"):
            configure_provider("OPENAI_API_KEY", "whatever", store=store)

    def test_overwrites_existing_value(self):
        store = InMemoryConfigStore()
        configure_provider("LLM_MODEL", "model-a", store=store)
        configure_provider("LLM_MODEL", "model-b", store=store)
        assert store.load_all()["LLM_MODEL"] == "model-b"


class TestClearProviderConfig:
    def test_clears_existing(self):
        store = InMemoryConfigStore()
        configure_provider("LLM_MODEL", "model-a", store=store)
        var = clear_provider_config("LLM_MODEL", store=store)
        assert var == "LLM_MODEL"
        assert store.load_all() == {}

    def test_clear_missing_is_silent(self):
        store = InMemoryConfigStore()
        assert clear_provider_config("LLM_MODEL", store=store) == "LLM_MODEL"

    def test_clear_unknown_var_rejected(self):
        store = InMemoryConfigStore()
        with pytest.raises(ValueError, match="不支持的配置项"):
            clear_provider_config("WHATEVER", store=store)


class TestShowConfigStatus:
    def test_secret_display_is_masked(self):
        store = InMemoryConfigStore()
        statuses = show_config_status(session={"LLM_API_KEY": RAW_KEY}, env={}, store=store)
        entry = next(s for s in statuses if s.name == "LLM_API_KEY")
        assert RAW_KEY not in entry.display_value
        assert entry.display_value.endswith("9527")
        assert entry.source == "session"

    def test_no_status_leaks_any_raw_key(self):
        store = InMemoryConfigStore()
        store.set("EMBEDDING_API_KEY", RAW_KEY)
        statuses = show_config_status(env={"LLM_API_KEY": RAW_KEY}, store=store)
        joined = " ".join(s.display_value for s in statuses)
        assert RAW_KEY not in joined

    def test_source_priority_visible(self):
        store = InMemoryConfigStore()
        store.set("LLM_MODEL", "file-model")
        statuses = show_config_status(env={"LLM_MODEL": "env-model"}, store=store)
        entry = next(s for s in statuses if s.name == "LLM_MODEL")
        assert entry.display_value == "env-model"
        assert entry.source == "env"

    def test_default_source_for_unconfigured_model(self):
        store = InMemoryConfigStore()
        statuses = show_config_status(env={}, store=store)
        entry = next(s for s in statuses if s.name == "EMBEDDING_MODEL")
        assert entry.source == "default"
        assert entry.display_value == "text-embedding-3-small"

    def test_missing_secret_marked_unset(self):
        store = InMemoryConfigStore()
        statuses = show_config_status(env={}, store=store)
        entry = next(s for s in statuses if s.name == "LLM_API_KEY")
        assert entry.source == "missing"
        assert entry.display_value == "（未设置）"

    def test_covers_all_allowed_vars(self):
        statuses = show_config_status(env={}, store=InMemoryConfigStore())
        assert {s.name for s in statuses} == {
            "LLM_API_KEY",
            "LLM_BASE_URL",
            "LLM_MODEL",
            "EMBEDDING_API_KEY",
            "EMBEDDING_BASE_URL",
            "EMBEDDING_MODEL",
        }

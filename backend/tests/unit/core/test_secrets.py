"""core 密钥规则测试：白名单、脱敏、来源优先级（AGENTS.md 安全红线）。"""

import pytest

from app.core.services.secrets import (
    SOURCE_DEFAULT,
    SOURCE_ENV,
    SOURCE_FILE,
    SOURCE_MISSING,
    SOURCE_SESSION,
    is_secret_var,
    mask_secret,
    normalize_var_name,
    resolve_value,
)


class TestNormalizeVarName:
    def test_strips_and_uppercases(self):
        assert normalize_var_name("  embedding_model ") == "EMBEDDING_MODEL"

    def test_rejects_unknown_var(self):
        with pytest.raises(ValueError, match="不支持的配置项"):
            normalize_var_name("OPENAI_API_KEY")

    def test_error_lists_allowed_vars(self):
        with pytest.raises(ValueError, match="LLM_API_KEY"):
            normalize_var_name("whatever")


class TestIsSecretVar:
    @pytest.mark.parametrize("name", ["LLM_API_KEY", "EMBEDDING_API_KEY", "llm_api_key"])
    def test_api_key_vars_are_secret(self, name):
        assert is_secret_var(name)

    @pytest.mark.parametrize("name", ["LLM_MODEL", "LLM_BASE_URL", "EMBEDDING_MODEL"])
    def test_non_key_vars_are_not_secret(self, name):
        assert not is_secret_var(name)


class TestMaskSecret:
    def test_empty_is_marked_unset(self):
        assert mask_secret("") == "（未设置）"

    def test_short_value_fully_masked(self):
        assert mask_secret("sk-12") == "****"

    def test_long_value_shows_only_last_four(self):
        masked = mask_secret("sk-abcdefghijklmnop")
        assert masked == "****...mnop"
        assert "abcdefghijklmnop" not in masked


class TestResolveValue:
    def test_session_wins_over_all(self):
        value, source = resolve_value(
            "LLM_API_KEY",
            session={"LLM_API_KEY": "session-key-123456"},
            env={"LLM_API_KEY": "env-key-123456"},
            file_values={"LLM_API_KEY": "file-key-123456"},
        )
        assert (value, source) == ("session-key-123456", SOURCE_SESSION)

    def test_env_wins_over_file(self):
        value, source = resolve_value(
            "LLM_API_KEY",
            session={},
            env={"LLM_API_KEY": "env-key-123456"},
            file_values={"LLM_API_KEY": "file-key-123456"},
        )
        assert (value, source) == ("env-key-123456", SOURCE_ENV)

    def test_file_used_when_higher_layers_empty(self):
        value, source = resolve_value(
            "LLM_MODEL",
            session={},
            env={},
            file_values={"LLM_MODEL": "my-model"},
        )
        assert (value, source) == ("my-model", SOURCE_FILE)

    def test_default_used_when_nothing_configured(self):
        value, source = resolve_value("EMBEDDING_MODEL", session={}, env={}, file_values={})
        assert (value, source) == ("text-embedding-3-small", SOURCE_DEFAULT)

    def test_secret_without_default_is_missing(self):
        value, source = resolve_value("LLM_API_KEY", session={}, env={}, file_values={})
        assert (value, source) == ("", SOURCE_MISSING)

    def test_empty_string_treated_as_unset(self):
        value, source = resolve_value(
            "LLM_API_KEY",
            session={"LLM_API_KEY": ""},
            env={"LLM_API_KEY": "env-key-123456"},
            file_values={},
        )
        assert (value, source) == ("env-key-123456", SOURCE_ENV)

    def test_whitespace_only_treated_as_unset(self):
        value, source = resolve_value(
            "LLM_API_KEY",
            session={"LLM_API_KEY": "   "},
            env={},
            file_values={},
        )
        assert (value, source) == ("", SOURCE_MISSING)

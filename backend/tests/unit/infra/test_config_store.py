"""EnvFileConfigStore 测试：本地 .env 读写（真实文件，写入 tmp_path，测试后自动清理）。"""

from app.infra.secrets.env_file_config_store import EnvFileConfigStore


class TestInitTemplate:
    def test_creates_template_with_empty_keys(self, tmp_path):
        store = EnvFileConfigStore(tmp_path / ".env")
        assert store.init_template() is True
        values = store.load_all()
        assert values["EMBEDDING_API_KEY"] == ""
        assert values["LLM_API_KEY"] == ""
        assert values["EMBEDDING_MODEL"] == "text-embedding-3-small"

    def test_existing_file_untouched(self, tmp_path):
        path = tmp_path / ".env"
        path.write_text("LLM_MODEL=my-model\n", encoding="utf-8")
        store = EnvFileConfigStore(path)
        assert store.init_template() is False
        assert store.load_all() == {"LLM_MODEL": "my-model"}


class TestLoadAll:
    def test_missing_file_gives_empty(self, tmp_path):
        store = EnvFileConfigStore(tmp_path / "nope.env")
        assert store.load_all() == {}

    def test_parses_and_ignores_noise(self, tmp_path):
        path = tmp_path / ".env"
        path.write_text(
            "# comment line\n\nLLM_MODEL=my-model\nno-equal-sign\n  SPACED_VAR = spaced value  \n",
            encoding="utf-8",
        )
        assert EnvFileConfigStore(path).load_all() == {
            "LLM_MODEL": "my-model",
            "SPACED_VAR": "spaced value",
        }


class TestSetAndClear:
    def test_set_appends_new_key(self, tmp_path):
        store = EnvFileConfigStore(tmp_path / ".env")
        store.set("LLM_MODEL", "model-a")
        store.set("LLM_BASE_URL", "https://my.example.com/v1")
        assert store.load_all() == {
            "LLM_MODEL": "model-a",
            "LLM_BASE_URL": "https://my.example.com/v1",
        }

    def test_set_overwrites_in_place(self, tmp_path):
        path = tmp_path / ".env"
        path.write_text("LLM_MODEL=model-a\nLLM_BASE_URL=url-a\n", encoding="utf-8")
        store = EnvFileConfigStore(path)
        store.set("LLM_MODEL", "model-b")
        assert store.load_all() == {"LLM_MODEL": "model-b", "LLM_BASE_URL": "url-a"}
        assert path.read_text(encoding="utf-8").count("LLM_MODEL") == 1

    def test_clear_removes_key(self, tmp_path):
        path = tmp_path / ".env"
        path.write_text("LLM_MODEL=model-a\nLLM_BASE_URL=url-a\n", encoding="utf-8")
        store = EnvFileConfigStore(path)
        store.clear("LLM_MODEL")
        assert store.load_all() == {"LLM_BASE_URL": "url-a"}

    def test_clear_missing_is_silent(self, tmp_path):
        store = EnvFileConfigStore(tmp_path / ".env")
        store.clear("LLM_MODEL")
        assert store.load_all() == {}

    def test_set_creates_parent_dir(self, tmp_path):
        store = EnvFileConfigStore(tmp_path / "nested" / "dir" / ".env")
        store.set("LLM_MODEL", "model-a")
        assert store.load_all()["LLM_MODEL"] == "model-a"

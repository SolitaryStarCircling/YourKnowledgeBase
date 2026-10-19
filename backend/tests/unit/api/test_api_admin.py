"""API 管理接口测试：板块 CRUD、BYOK 配置（脱敏 / 不代写 Key）与错误映射。"""

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.core.services.secrets import ALLOWED_VARS
from tests.unit.api.conftest import FakeServices


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ALLOWED_VARS:
        monkeypatch.delenv(var, raising=False)


def test_section_crud(client: TestClient) -> None:
    created = client.post("/sections", json={"name": "技术", "description": "RAG 笔记"})
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "技术"
    assert body["description"] == "RAG 笔记"
    assert body["section_id"]

    listed = client.get("/sections")
    assert [s["name"] for s in listed.json()] == ["技术"]

    renamed = client.patch("/sections/技术", json={"new_name": "新技术"})
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "新技术"
    assert renamed.json()["section_id"] == body["section_id"]

    deleted = client.delete("/sections/新技术")
    assert deleted.status_code == 204
    assert deleted.text == ""
    assert client.get("/sections").json() == []


def test_section_duplicate_name_400(client: TestClient) -> None:
    client.post("/sections", json={"name": "技术"})
    resp = client.post("/sections", json={"name": "技术"})
    assert resp.status_code == 400
    assert "已存在" in resp.json()["detail"]


def test_section_blank_name_400(client: TestClient) -> None:
    resp = client.post("/sections", json={"name": "   "})
    assert resp.status_code == 400


def test_section_update_without_fields_400(client: TestClient) -> None:
    client.post("/sections", json={"name": "技术"})
    resp = client.patch("/sections/技术", json={})
    assert resp.status_code == 400
    assert "请指定" in resp.json()["detail"]


def test_section_delete_missing_400(client: TestClient) -> None:
    resp = client.delete("/sections/无此板块")
    assert resp.status_code == 400
    assert "板块不存在" in resp.json()["detail"]


def test_config_status_masks_keys(client: TestClient, fakes: FakeServices, clean_env: None) -> None:
    fakes.config_store.values["LLM_API_KEY"] = "sk-secret-abcdef"
    fakes.config_store.values["LLM_MODEL"] = "gpt-test"
    resp = client.get("/config")
    assert resp.status_code == 200
    items = {item["name"]: item for item in resp.json()}
    assert items["LLM_API_KEY"]["source"] == "file"
    assert items["LLM_API_KEY"]["display_value"].startswith("****")
    assert items["LLM_MODEL"] == {
        "name": "LLM_MODEL",
        "source": "file",
        "display_value": "gpt-test",
    }
    assert items["EMBEDDING_API_KEY"]["source"] == "missing"
    assert "sk-secret-abcdef" not in resp.text


def test_config_status_shows_session_source(
    client: TestClient, fakes: FakeServices, clean_env: None
) -> None:
    secret = "sk-session-secret-1234"
    resp = client.get("/config", headers={"X-Llm-Api-Key": secret})
    items = {item["name"]: item for item in resp.json()}
    assert items["LLM_API_KEY"]["source"] == "session"
    assert items["LLM_API_KEY"]["display_value"].startswith("****")
    assert secret not in resp.text


def test_config_set_non_secret(client: TestClient, fakes: FakeServices, clean_env: None) -> None:
    resp = client.put("/config/LLM_MODEL", json={"value": "gpt-test"})
    assert resp.status_code == 200
    assert resp.json() == {"name": "LLM_MODEL"}
    assert fakes.config_store.values["LLM_MODEL"] == "gpt-test"


def test_config_set_secret_rejected(
    client: TestClient, fakes: FakeServices, clean_env: None
) -> None:
    secret = "sk-should-not-persist-9876"
    resp = client.put("/config/LLM_API_KEY", json={"value": secret})
    assert resp.status_code == 400
    assert fakes.config_store.values == {}
    assert secret not in resp.text


def test_config_set_unknown_var_400(client: TestClient, clean_env: None) -> None:
    resp = client.put("/config/NOT_A_VAR", json={"value": "x"})
    assert resp.status_code == 400


def test_config_clear(client: TestClient, fakes: FakeServices, clean_env: None) -> None:
    fakes.config_store.values["LLM_MODEL"] = "gpt-test"
    resp = client.delete("/config/LLM_MODEL")
    assert resp.status_code == 204
    assert resp.text == ""
    assert "LLM_MODEL" not in fakes.config_store.values


def test_validation_error_strips_input(client: TestClient) -> None:
    secret = "sk-in-body-secret-42"
    resp = client.post("/ask", json={"question": {"nested": secret}})
    assert resp.status_code == 422
    errors = resp.json()["detail"]
    assert errors
    for error in errors:
        assert set(error) == {"loc", "msg", "type"}
    assert secret not in resp.text


def test_unexpected_error_returns_500_fixed_message(
    monkeypatch: pytest.MonkeyPatch, fakes: FakeServices
) -> None:
    def boom() -> list:
        raise Exception("内部实现细节 secret=sk-leak")

    monkeypatch.setattr(fakes.section_repo, "list_all", boom)
    client = TestClient(create_app(fakes.container), raise_server_exceptions=False)
    resp = client.get("/sections")
    assert resp.status_code == 500
    assert resp.json() == {"detail": "服务内部错误"}
    assert "sk-leak" not in resp.text

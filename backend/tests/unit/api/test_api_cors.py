"""CORS 测试：Web 端（浏览器）跨域访问必须放行，否则网页版前端无法使用。"""

from fastapi.testclient import TestClient


def test_preflight_allows_browser_origin(client: TestClient) -> None:
    resp = client.options(
        "/search",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-llm-api-key",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "*"
    assert "POST" in resp.headers["access-control-allow-methods"]
    assert resp.headers.get("access-control-allow-headers")


def test_actual_response_carries_allow_origin(client: TestClient) -> None:
    resp = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "*"

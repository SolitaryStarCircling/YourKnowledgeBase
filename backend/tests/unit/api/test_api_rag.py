"""API 核心链路测试：导入 -> 语义搜索 -> RAG 问答（含引用校验）与 BYOK 会话头。"""

from fastapi.testclient import TestClient

from app.core.entities.models import ParsedDocument
from tests.unit.api.conftest import FakeServices


def test_health_needs_no_keys(client: TestClient, fakes: FakeServices) -> None:
    fakes.missing_embedding_key = True
    fakes.missing_llm_key = True
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert fakes.sessions == []


def test_import_created(client: TestClient) -> None:
    resp = client.post("/documents/import", json={"source": "note.md"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "created"
    assert body["title"] == "测试笔记"
    assert body["chunk_count"] == 2
    assert body["doc_id"]


def test_import_unchanged_skips_without_reembed(client: TestClient, fakes: FakeServices) -> None:
    client.post("/documents/import", json={"source": "note.md"})
    calls = fakes.embedder.document_calls
    resp = client.post("/documents/import", json={"source": "note.md"})
    assert resp.json()["status"] == "skipped"
    assert fakes.embedder.document_calls == calls


def test_import_move_to_section_is_update_without_reembed(
    client: TestClient, fakes: FakeServices
) -> None:
    client.post("/documents/import", json={"source": "note.md"})
    client.post("/sections", json={"name": "技术"})
    calls = fakes.embedder.document_calls
    resp = client.post("/documents/import", json={"source": "note.md", "section": "技术"})
    assert resp.json()["status"] == "updated"
    assert fakes.embedder.document_calls == calls


def test_import_unknown_section_400(client: TestClient) -> None:
    resp = client.post("/documents/import", json={"source": "note.md", "section": "无此板块"})
    assert resp.status_code == 400
    assert "板块不存在" in resp.json()["detail"]


def test_import_unsupported_source_400(client: TestClient, fakes: FakeServices) -> None:
    # 与真实 CompositeParser 同语义：未知来源报 ValueError -> 400
    def parse(source: str) -> ParsedDocument:
        raise ValueError(f"不支持的来源格式：{source}（当前支持 md/txt/pdf/URL）")

    fakes.parser.parse = parse  # type: ignore[method-assign]
    resp = client.post("/documents/import", json={"source": "笔记.docx"})
    assert resp.status_code == 400
    assert "不支持的来源格式" in resp.json()["detail"]


def test_import_empty_document_400(client: TestClient, fakes: FakeServices) -> None:
    fakes.parser.documents["empty.md"] = ParsedDocument(title="空文档", text="")
    resp = client.post("/documents/import", json={"source": "empty.md"})
    assert resp.status_code == 400
    assert "没有可索引" in resp.json()["detail"]


def test_search_returns_hits_with_source(client: TestClient) -> None:
    client.post("/documents/import", json={"source": "note.md"})
    resp = client.post("/search", json={"query": "检索增强生成"})
    assert resp.status_code == 200
    hits = resp.json()["hits"]
    assert hits
    hit = hits[0]
    assert hit["title"] == "测试笔记"
    assert hit["source"] == "note.md"
    assert hit["text"]
    assert isinstance(hit["score"], float)


def test_search_filtered_by_section(client: TestClient) -> None:
    client.post("/sections", json={"name": "技术"})
    client.post("/sections", json={"name": "生活"})
    client.post("/documents/import", json={"source": "note.md", "section": "技术"})
    resp = client.post("/search", json={"query": "检索增强生成", "section": "技术"})
    hits = resp.json()["hits"]
    # note.md 按段落分块为 2 个 chunk，全部命中且都属于"技术"板块
    assert hits
    assert all(hit["title"] == "测试笔记" and hit["source"] == "note.md" for hit in hits)
    empty = client.post("/search", json={"query": "检索增强生成", "section": "生活"})
    assert empty.json()["hits"] == []


def test_search_unknown_section_400(client: TestClient) -> None:
    resp = client.post("/search", json={"query": "任意", "section": "无此板块"})
    assert resp.status_code == 400
    assert "板块不存在" in resp.json()["detail"]


def test_ask_returns_answer_with_citations(client: TestClient) -> None:
    client.post("/documents/import", json={"source": "note.md"})
    resp = client.post("/ask", json={"question": "什么是 RAG"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["text"] == "这是答案 [1]"
    assert body["citations"]
    citation = body["citations"][0]
    assert citation["marker"] == 1
    assert citation["title"] == "测试笔记"
    assert citation["source"] == "note.md"
    assert citation["excerpt"]


def test_ask_drops_fabricated_markers(client: TestClient, fakes: FakeServices) -> None:
    client.post("/documents/import", json={"source": "note.md"})
    fakes.llm.answer_text = "答案 [1] 和 [9]"
    body = client.post("/ask", json={"question": "什么是 RAG"}).json()
    assert [c["marker"] for c in body["citations"]] == [1]


def test_ask_empty_store_skips_llm(client: TestClient, fakes: FakeServices) -> None:
    body = client.post("/ask", json={"question": "什么是 RAG"}).json()
    assert body["text"] == "知识库中没有找到与问题相关的内容，无法回答。"
    assert body["citations"] == []
    assert fakes.llm.calls == []


def test_ask_empty_question_400(client: TestClient) -> None:
    resp = client.post("/ask", json={"question": ""})
    assert resp.status_code == 400
    assert "问题不能为空" in resp.json()["detail"]


def test_search_without_embedding_key_503(client: TestClient, fakes: FakeServices) -> None:
    fakes.missing_embedding_key = True
    resp = client.post("/search", json={"query": "任意"})
    assert resp.status_code == 503
    assert "EMBEDDING_API_KEY" in resp.json()["detail"]


def test_ask_without_llm_key_503(client: TestClient, fakes: FakeServices) -> None:
    client.post("/documents/import", json={"source": "note.md"})
    fakes.missing_llm_key = True
    resp = client.post("/ask", json={"question": "什么是 RAG"})
    assert resp.status_code == 503
    assert "LLM_API_KEY" in resp.json()["detail"]


def test_session_headers_reach_factories_without_leaking(
    client: TestClient, fakes: FakeServices
) -> None:
    secret = "sk-session-secret-1234"
    resp = client.post(
        "/search", json={"query": "检索增强生成"}, headers={"X-Embedding-Api-Key": secret}
    )
    assert resp.status_code == 200
    assert fakes.sessions[-1] == {"EMBEDDING_API_KEY": secret}
    assert secret not in resp.text


def test_ask_session_headers_carry_both_keys(client: TestClient, fakes: FakeServices) -> None:
    client.post("/documents/import", json={"source": "note.md"})
    emb_secret = "sk-emb-secret-1234"
    llm_secret = "sk-llm-secret-5678"
    resp = client.post(
        "/ask",
        json={"question": "什么是 RAG"},
        headers={"X-Embedding-Api-Key": emb_secret, "X-Llm-Api-Key": llm_secret},
    )
    assert resp.status_code == 200
    assert fakes.sessions[-1] == {"EMBEDDING_API_KEY": emb_secret, "LLM_API_KEY": llm_secret}
    assert emb_secret not in resp.text
    assert llm_secret not in resp.text

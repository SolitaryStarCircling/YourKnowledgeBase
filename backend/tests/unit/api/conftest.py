"""API 层测试夹具：内存假件拼装 ServiceContainer + TestClient（零出网、零 API 花费）。"""

from collections.abc import Mapping

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.bootstrap import ServiceContainer
from app.core.entities.models import ParsedDocument
from tests.fakes import (
    FakeChunker,
    FakeEmbeddingProvider,
    FakeLLMProvider,
    FakeParser,
    InMemoryConfigStore,
    InMemoryDocumentRepository,
    InMemorySectionRepository,
    InMemoryVectorStore,
)


class FakeServices:
    """一组内存假件 + 可注入"缺 Key"行为的工厂（模拟 BYOK 未配置的报错路径）。"""

    def __init__(self) -> None:
        self.parser = FakeParser(
            {
                "note.md": ParsedDocument(
                    title="测试笔记", text="RAG 是检索增强生成。\n\n引用来自真实片段。"
                )
            }
        )
        self.chunker = FakeChunker()
        self.embedder = FakeEmbeddingProvider()
        self.llm = FakeLLMProvider("这是答案 [1]")
        self.vector_store = InMemoryVectorStore()
        self.doc_repo = InMemoryDocumentRepository()
        self.section_repo = InMemorySectionRepository()
        self.config_store = InMemoryConfigStore()
        self.sessions: list[dict[str, str] | None] = []
        self.missing_embedding_key = False
        self.missing_llm_key = False

    def embedder_factory(self, session: Mapping[str, str] | None) -> FakeEmbeddingProvider:
        self.sessions.append(dict(session) if session else None)
        if self.missing_embedding_key:
            raise RuntimeError(
                "未配置 EMBEDDING_API_KEY，无法生成向量。请先配置密钥（config init/status）。"
            )
        return self.embedder

    def llm_factory(self, session: Mapping[str, str] | None) -> FakeLLMProvider:
        self.sessions.append(dict(session) if session else None)
        if self.missing_llm_key:
            raise RuntimeError(
                "未配置 LLM_API_KEY，无法生成回答。请先配置密钥（config init/status）。"
            )
        return self.llm

    @property
    def container(self) -> ServiceContainer:
        return ServiceContainer(
            parser=self.parser,
            chunker=self.chunker,
            vector_store=self.vector_store,
            doc_repo=self.doc_repo,
            section_repo=self.section_repo,
            config_store=self.config_store,
            embedder_factory=self.embedder_factory,
            llm_factory=self.llm_factory,
        )


@pytest.fixture
def fakes() -> FakeServices:
    return FakeServices()


@pytest.fixture
def client(fakes: FakeServices) -> TestClient:
    return TestClient(create_app(fakes.container))

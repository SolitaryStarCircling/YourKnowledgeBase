"""组装根：拼装端口的具体实现（换厂商 / 换向量库只改这里）。

CLI 与 API 共用同一套拼装；业务逻辑全部在用例层，本文件不含业务。
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from app.config import load_embedding_config, load_llm_config
from app.core.ports.chunker import Chunker
from app.core.ports.document_repository import DocumentRepository
from app.core.ports.embedding import EmbeddingProvider
from app.core.ports.llm import LLMProvider
from app.core.ports.local_config_store import LocalConfigStore
from app.core.ports.parser import Parser
from app.core.ports.section_repository import SectionRepository
from app.core.ports.vector_store import VectorStore
from app.infra.chunking.fixed_size_chunker import FixedSizeChunker
from app.infra.db.sqlite_document_repository import SqliteDocumentRepository
from app.infra.db.sqlite_section_repository import SqliteSectionRepository
from app.infra.parsers.composite_parser import CompositeParser
from app.infra.parsers.markdown_parser import MarkdownParser
from app.infra.parsers.pdf_parser import PdfParser
from app.infra.parsers.url_parser import UrlParser
from app.infra.providers.http_page_fetcher import HttpPageFetcher
from app.infra.providers.openai_compatible_embedding import OpenAiCompatibleEmbedding
from app.infra.providers.openai_compatible_llm import OpenAiCompatibleLlm
from app.infra.secrets.env_file_config_store import EnvFileConfigStore
from app.infra.vectordb.lancedb_store import LanceDbVectorStore

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


@dataclass
class ServiceContainer:
    """API 入口层持有的服务集合；embedder / llm 由工厂按请求惰性构造。"""

    parser: Parser
    chunker: Chunker
    vector_store: VectorStore
    doc_repo: DocumentRepository
    section_repo: SectionRepository
    config_store: LocalConfigStore
    embedder_factory: Callable[[Mapping[str, str] | None], EmbeddingProvider]
    llm_factory: Callable[[Mapping[str, str] | None], LLMProvider]


def build_repos() -> tuple[SqliteDocumentRepository, SqliteSectionRepository]:
    """只拼装元数据仓储；板块命令零 API Key 依赖。"""
    doc_repo = SqliteDocumentRepository(DATA_DIR / "meta.db")
    section_repo = SqliteSectionRepository(DATA_DIR / "meta.db")
    return doc_repo, section_repo


def build_config_store() -> LocalConfigStore:
    return EnvFileConfigStore(ENV_FILE)


def build_parser() -> Parser:
    return CompositeParser([MarkdownParser(), PdfParser(), UrlParser(HttpPageFetcher())])


def build_embedder(session_secrets: Mapping[str, str] | None = None) -> EmbeddingProvider:
    embedding = load_embedding_config(session_secrets=session_secrets)
    return OpenAiCompatibleEmbedding(
        api_key=embedding.api_key,
        base_url=embedding.base_url,
        model=embedding.model,
    )


def build_llm(session_secrets: Mapping[str, str] | None = None) -> LLMProvider:
    llm_cfg = load_llm_config(session_secrets=session_secrets)
    return OpenAiCompatibleLlm(
        api_key=llm_cfg.api_key,
        base_url=llm_cfg.base_url,
        model=llm_cfg.model,
    )


def build_services(session_secrets: Mapping[str, str] | None = None) -> tuple:
    """CLI 用的平铺拼装；LLM 不在这里拼装，ask 命令按需构造。

    session_secrets 是会话模式的密钥覆盖（只存内存，进程退出即失效）。
    """
    parser = build_parser()
    chunker = FixedSizeChunker()
    embedder = build_embedder(session_secrets)
    vector_store = LanceDbVectorStore(DATA_DIR / "vectordb")
    doc_repo, section_repo = build_repos()
    return parser, chunker, embedder, vector_store, doc_repo, section_repo


def build_api_container() -> ServiceContainer:
    """API 入口层的组装根；embedder / llm 延迟到请求时才构造（缺 Key 只影响相关端点）。"""
    doc_repo, section_repo = build_repos()
    return ServiceContainer(
        parser=build_parser(),
        chunker=FixedSizeChunker(),
        vector_store=LanceDbVectorStore(DATA_DIR / "vectordb"),
        doc_repo=doc_repo,
        section_repo=section_repo,
        config_store=build_config_store(),
        embedder_factory=build_embedder,
        llm_factory=build_llm,
    )

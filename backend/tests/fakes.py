"""测试替身：内存版端口实现与确定性嵌入（测试一律不出网、不花 API 钱）。"""

import math
from dataclasses import replace

from app.core.entities.models import (
    Chunk,
    Document,
    ParsedDocument,
    SearchHit,
    Section,
    TextSegment,
)
from app.core.ports.chunker import Chunker
from app.core.ports.document_repository import DocumentRepository
from app.core.ports.embedding import EmbeddingProvider
from app.core.ports.llm import LLMProvider
from app.core.ports.local_config_store import LocalConfigStore
from app.core.ports.page_fetcher import PageFetcher
from app.core.ports.parser import Parser
from app.core.ports.section_repository import SectionRepository
from app.core.ports.vector_store import VectorStore


def make_pdf_bytes(title: str, text: str) -> bytes:
    """手工拼一个最小合法 PDF（单页 + Helvetica 文本 + 元数据标题）。

    测试用的 PDF 样例由此构造，不依赖仓库里的二进制文件。
    """
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("latin-1")
    bodies = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
        ),
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Title (" + title.encode("latin-1") + b") >>",
    ]

    pdf = b"%PDF-1.4\n"
    offsets = []
    for index, body in enumerate(bodies, start=1):
        offsets.append(len(pdf))
        pdf += f"{index} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_pos = len(pdf)
    pdf += f"xref\n0 {len(bodies) + 1}\n".encode()
    pdf += b"0000000000 65535 f \n"
    for offset in offsets:
        pdf += f"{offset:010d} 00000 n \n".encode()
    pdf += (
        f"trailer\n<< /Root 1 0 R /Info 6 0 R /Size {len(bodies) + 1} >>\n"
        f"startxref\n{xref_pos}\n%%EOF"
    ).encode()
    return pdf


class FakeParser(Parser):
    """按预置字典返回解析结果，可随时改内容模拟"文档被编辑"。"""

    def __init__(self, documents: dict[str, ParsedDocument]) -> None:
        self.documents = documents

    def can_parse(self, source: str) -> bool:
        return source in self.documents

    def parse(self, source: str) -> ParsedDocument:
        return self.documents[source]


class FakeChunker(Chunker):
    """按空行分段，与 core 的分块规则无关（规则本身在 core 测试里覆盖）。"""

    def chunk(self, text: str) -> list[TextSegment]:
        pieces = [piece.strip() for piece in text.split("\n\n") if piece.strip()]
        return [TextSegment(index=i, text=piece) for i, piece in enumerate(pieces)]


class FakeEmbeddingProvider(EmbeddingProvider):
    """确定性"字符频率"伪向量：不出网、可复现，文本越接近向量越近。

    document_calls 计数用来验证增量逻辑：内容没变就绝不重复嵌入。
    """

    def __init__(self, dim: int = 16) -> None:
        self.dim = dim
        self.document_calls = 0

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.document_calls += 1
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)

    def _vector(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for char in text:
            vec[ord(char) % self.dim] += 1.0
        norm = math.sqrt(sum(value * value for value in vec)) or 1.0
        return [value / norm for value in vec]


class FakePageFetcher(PageFetcher):
    """预置网页 HTML，验证 UrlParser 的 HTML -> 文本逻辑（不出网）。"""

    def __init__(self, pages: dict[str, str] | None = None) -> None:
        self.pages = pages or {}
        self.fetched: list[str] = []

    def fetch(self, url: str) -> str:
        self.fetched.append(url)
        if url not in self.pages:
            raise RuntimeError("网页抓取失败：HTTP 404")
        return self.pages[url]


class FakeLLMProvider(LLMProvider):
    """返回预置回答文本并记录收到的提示词，验证 prompt 组装与引用校验。"""

    def __init__(self, answer_text: str) -> None:
        self.answer_text = answer_text
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        return self.answer_text


class InMemoryVectorStore(VectorStore):
    """内存向量库：用朴素余弦相似度模拟 Top-K 检索。"""

    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.deleted_doc_ids: list[str] = []

    def add_chunks(
        self,
        document: Document,
        chunks: list[Chunk],
        vectors: list[list[float]],
    ) -> None:
        for chunk, vector in zip(chunks, vectors, strict=True):
            self.rows.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "doc_id": chunk.doc_id,
                    "index": chunk.index,
                    "text": chunk.text,
                    "title": document.title,
                    "source": document.source,
                    "vector": list(vector),
                }
            )

    def search(
        self,
        vector: list[float],
        top_k: int,
        *,
        doc_ids: list[str] | None = None,
    ) -> list[SearchHit]:
        rows = self.rows if doc_ids is None else [r for r in self.rows if r["doc_id"] in doc_ids]
        scored = sorted(
            rows,
            key=lambda row: _cosine(vector, row["vector"]),
            reverse=True,
        )[:top_k]
        return [
            SearchHit(
                chunk_id=row["chunk_id"],
                doc_id=row["doc_id"],
                index=row["index"],
                text=row["text"],
                title=row["title"],
                source=row["source"],
                score=_cosine(vector, row["vector"]),
            )
            for row in scored
        ]

    def delete_by_doc(self, doc_id: str) -> None:
        self.rows = [row for row in self.rows if row["doc_id"] != doc_id]
        self.deleted_doc_ids.append(doc_id)


class InMemoryDocumentRepository(DocumentRepository):
    def __init__(self) -> None:
        self.docs: dict[str, Document] = {}

    def get_by_source(self, source: str) -> Document | None:
        return next((doc for doc in self.docs.values() if doc.source == source), None)

    def save(self, document: Document) -> None:
        self.docs[document.doc_id] = document

    def delete(self, doc_id: str) -> None:
        self.docs.pop(doc_id, None)

    def list_by_section(self, section_id: str) -> list[Document]:
        return [doc for doc in self.docs.values() if doc.section_id == section_id]

    def unassign_section(self, section_id: str) -> None:
        self.docs = {
            doc_id: replace(doc, section_id=None) if doc.section_id == section_id else doc
            for doc_id, doc in self.docs.items()
        }


class InMemorySectionRepository(SectionRepository):
    def __init__(self) -> None:
        self.sections: dict[str, Section] = {}

    def get_by_name(self, name: str) -> Section | None:
        return next((s for s in self.sections.values() if s.name == name), None)

    def list_all(self) -> list[Section]:
        return list(self.sections.values())

    def save(self, section: Section) -> None:
        self.sections[section.section_id] = section

    def delete(self, section_id: str) -> None:
        self.sections.pop(section_id, None)


class InMemoryConfigStore(LocalConfigStore):
    """内存 .env 替身；init_template 记录是否被调用过。"""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.inited = False

    def load_all(self) -> dict[str, str]:
        return dict(self.values)

    def set(self, name: str, value: str) -> None:
        self.values[name] = value

    def clear(self, name: str) -> None:
        self.values.pop(name, None)

    def init_template(self) -> bool:
        self.inited = True
        return True


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (norm_a * norm_b)

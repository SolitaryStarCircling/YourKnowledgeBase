"""用例：RAG 问答（检索 -> 组装提示词 -> LLM 生成 -> 校验引用）。

一个用例一个文件；只依赖领域层的实体与端口，具体实现由入口层注入。
引用红线：回答中的引用只能来自检索到的真实片段，模型编造的编号在校验时被丢弃。
"""

from dataclasses import dataclass

from app.core.entities.models import Citation
from app.core.ports.document_repository import DocumentRepository
from app.core.ports.embedding import EmbeddingProvider
from app.core.ports.llm import LLMProvider
from app.core.ports.section_repository import SectionRepository
from app.core.ports.vector_store import VectorStore
from app.core.services.citation import build_citations, format_context
from app.usecases.semantic_search import semantic_search

_SYSTEM_PROMPT = (
    "你是个人知识库的问答助手。请仅根据给出的资料片段回答问题，"
    "不要编造资料之外的信息；资料不足以回答时明确说不知道。"
    "回答中用 [1]、[2] 这样的编号标注所引用的片段，编号必须来自资料片段。"
)

_NO_HITS_MESSAGE = "知识库中没有找到与问题相关的内容，无法回答。"


@dataclass(frozen=True)
class Answer:
    """问答结果：回答文本 + 校验后的真实引用。"""

    text: str
    citations: list[Citation]


def answer_question(
    question: str,
    *,
    llm: LLMProvider,
    embedder: EmbeddingProvider,
    vector_store: VectorStore,
    top_k: int = 5,
    section: str | None = None,
    section_repo: SectionRepository | None = None,
    doc_repo: DocumentRepository | None = None,
) -> Answer:
    """对提问做 RAG 问答；检索为空时直接返回，不发起 LLM 调用（省 API 费用）。

    section 限定回答只依据该板块内的文档（按名称）。
    """
    question = question.strip()
    if not question:
        raise ValueError("问题不能为空")

    hits = semantic_search(
        question,
        embedder=embedder,
        vector_store=vector_store,
        top_k=top_k,
        section=section,
        section_repo=section_repo,
        doc_repo=doc_repo,
    )
    if not hits:
        return Answer(text=_NO_HITS_MESSAGE, citations=[])

    user_prompt = f"问题：{question}\n\n资料片段：\n{format_context(hits)}"
    text = llm.complete(system=_SYSTEM_PROMPT, user=user_prompt).strip()
    return Answer(text=text, citations=build_citations(text, hits))

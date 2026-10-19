"""API 请求 / 响应模型（Pydantic）：只做数据形状与基础校验。"""

from pydantic import BaseModel, Field

from app.core.entities.models import Citation, SearchHit, Section
from app.usecases.answer_question import Answer
from app.usecases.import_document import ImportResult


class ImportRequest(BaseModel):
    source: str = Field(description="本地 md/txt/PDF 文件路径，或 http(s) 网页 URL")
    section: str | None = Field(default=None, description="所属板块名称")


class ImportResponse(BaseModel):
    status: str = Field(description="created | updated | skipped")
    doc_id: str
    title: str
    chunk_count: int

    @classmethod
    def from_result(cls, result: ImportResult) -> "ImportResponse":
        return cls(
            status=result.status,
            doc_id=result.doc_id,
            title=result.title,
            chunk_count=result.chunk_count,
        )


class SearchRequest(BaseModel):
    query: str = Field(description="查询文本")
    top_k: int = Field(default=5, ge=1, le=50, description="返回条数")
    section: str | None = Field(default=None, description="限定板块名称")


class SearchHitModel(BaseModel):
    chunk_id: str
    doc_id: str
    index: int
    text: str
    title: str
    source: str
    score: float

    @classmethod
    def from_hit(cls, hit: SearchHit) -> "SearchHitModel":
        return cls(
            chunk_id=hit.chunk_id,
            doc_id=hit.doc_id,
            index=hit.index,
            text=hit.text,
            title=hit.title,
            source=hit.source,
            score=hit.score,
        )


class SearchResponse(BaseModel):
    hits: list[SearchHitModel]


class AskRequest(BaseModel):
    question: str = Field(description="问题文本")
    top_k: int = Field(default=5, ge=1, le=50, description="检索片段数")
    section: str | None = Field(default=None, description="限定板块名称")


class CitationModel(BaseModel):
    marker: int = Field(description="回答正文中的引用编号 [n]")
    chunk_id: str
    doc_id: str
    title: str
    source: str
    excerpt: str
    score: float

    @classmethod
    def from_citation(cls, citation: Citation) -> "CitationModel":
        return cls(
            marker=citation.marker,
            chunk_id=citation.chunk_id,
            doc_id=citation.doc_id,
            title=citation.title,
            source=citation.source,
            excerpt=citation.excerpt,
            score=citation.score,
        )


class AskResponse(BaseModel):
    text: str
    citations: list[CitationModel]

    @classmethod
    def from_answer(cls, answer: Answer) -> "AskResponse":
        return cls(
            text=answer.text,
            citations=[CitationModel.from_citation(c) for c in answer.citations],
        )


class SectionCreateRequest(BaseModel):
    name: str = Field(description="板块名称")
    description: str = Field(default="", description="板块描述")


class SectionUpdateRequest(BaseModel):
    new_name: str | None = Field(default=None, description="新名称")
    description: str | None = Field(default=None, description="新描述")


class SectionModel(BaseModel):
    section_id: str
    name: str
    description: str

    @classmethod
    def from_section(cls, section: Section) -> "SectionModel":
        return cls(
            section_id=section.section_id,
            name=section.name,
            description=section.description,
        )


class ConfigItem(BaseModel):
    name: str
    source: str = Field(description="session | env | file | default | missing")
    display_value: str = Field(description="已脱敏的显示值")


class ConfigSetRequest(BaseModel):
    value: str


class ConfigVarResponse(BaseModel):
    name: str

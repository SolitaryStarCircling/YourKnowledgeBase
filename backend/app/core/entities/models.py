"""领域模型：实体与值对象（纯 Python，无框架依赖）。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    """一篇已导入的文档（元数据；正文不在这里）。"""

    doc_id: str
    title: str
    source_type: str  # "file" | "url"
    source: str  # 文件路径或 URL
    content_hash: str  # 正文内容哈希，增量更新的判定依据
    chunk_count: int
    imported_at: str  # ISO 8601 时间
    section_id: str | None = None  # 所属板块；None 表示未分板块


@dataclass(frozen=True)
class Section:
    """板块（Section）：用户自建的数据分区（id、名称、描述）。"""

    section_id: str
    name: str
    description: str


@dataclass(frozen=True)
class Chunk:
    """文档被切出的一个片段；向量由 VectorStore 管理，不放在实体里。"""

    chunk_id: str
    doc_id: str
    index: int
    text: str


@dataclass(frozen=True)
class TextSegment:
    """分块规则的产物：带序号的纯文本片段（尚未绑定 doc_id）。"""

    index: int
    text: str


@dataclass(frozen=True)
class ParsedDocument:
    """解析器的产物：文档标题与正文。"""

    title: str
    text: str


@dataclass(frozen=True)
class SearchHit:
    """一次检索命中：相关片段 + 来源 + 得分（得分越高越相关）。"""

    chunk_id: str
    doc_id: str
    index: int
    text: str
    title: str
    source: str
    score: float


@dataclass(frozen=True)
class Citation:
    """问答引用的载体：只能来自检索到的真实片段，不允许模型编造来源。"""

    marker: int  # 回答正文中的引用编号，对应 [1]、[2]
    chunk_id: str
    doc_id: str
    title: str
    source: str
    excerpt: str  # 原文摘录
    score: float  # 相关度得分

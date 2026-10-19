"""引用格式规则：上下文编号、回答内引用标记的解析与校验（纯函数）。

红线：引用只能来自检索到的真实片段——超出检索范围的编号视为模型编造，直接丢弃。
"""

import re

from app.core.entities.models import Citation, SearchHit

_MARKER_PATTERN = re.compile(r"\[(\d{1,3})\]")


def format_context(hits: list[SearchHit]) -> str:
    """把检索片段拼成带编号的资料块，编号从 1 开始，与回答中的 [n] 对应。"""
    blocks = []
    for marker, hit in enumerate(hits, start=1):
        blocks.append(f"[{marker}] 《{hit.title}》 来源: {hit.source}\n{hit.text}")
    return "\n\n".join(blocks)


def extract_markers(answer_text: str) -> list[int]:
    """提取回答中的引用编号，去重并保持出现顺序。"""
    seen: set[int] = set()
    markers: list[int] = []
    for match in _MARKER_PATTERN.finditer(answer_text):
        marker = int(match.group(1))
        if marker not in seen:
            seen.add(marker)
            markers.append(marker)
    return markers


def build_citations(answer_text: str, hits: list[SearchHit]) -> list[Citation]:
    """按回答实际用到的编号生成引用；编号超出检索范围的直接丢弃（防编造来源）。"""
    citations = []
    for marker in extract_markers(answer_text):
        if not 1 <= marker <= len(hits):
            continue
        hit = hits[marker - 1]
        citations.append(
            Citation(
                marker=marker,
                chunk_id=hit.chunk_id,
                doc_id=hit.doc_id,
                title=hit.title,
                source=hit.source,
                excerpt=hit.text,
                score=hit.score,
            )
        )
    return citations

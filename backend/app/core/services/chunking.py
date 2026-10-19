"""分块业务规则（纯 Python）：定长滑动窗口 + 重叠，产出有序 TextSegment。

实现类在 infra/chunking/（端口 Chunker 的适配器），规则本身放这里，
保证分块行为可独立测试、与任何框架无关。
"""

from app.core.entities.models import TextSegment

DEFAULT_CHUNK_SIZE = 500
DEFAULT_OVERLAP = 100


def split_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[TextSegment]:
    """把正文切成定长片段，相邻片段重叠 overlap 个字符，序号从 0 连续递增。

    重叠是为了避免语义被切断在片段边界上；尾部不足一个窗口的剩余文本并入最后一段。
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须为正数")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap 必须满足 0 <= overlap < chunk_size")

    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [TextSegment(index=0, text=text)]

    step = chunk_size - overlap
    starts = list(range(0, len(text), step))
    segments: list[TextSegment] = []
    for start in starts:
        piece = text[start : start + chunk_size].strip()
        if not piece:
            continue
        # 尾部碎片不足以独立成段时并入上一段，避免出现一两个字的无意义片段
        if len(piece) < overlap and segments:
            segments[-1] = TextSegment(index=len(segments) - 1, text=segments[-1].text + piece)
            continue
        segments.append(TextSegment(index=len(segments), text=piece))
    return segments

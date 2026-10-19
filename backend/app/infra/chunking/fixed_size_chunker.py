"""定长分块器（Chunker 端口实现）：把 core/services 的分块规则适配成端口。"""

from app.core.entities.models import TextSegment
from app.core.ports.chunker import Chunker
from app.core.services.chunking import DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP, split_text


class FixedSizeChunker(Chunker):
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP,
    ) -> None:
        self._chunk_size = chunk_size
        self._overlap = overlap

    def chunk(self, text: str) -> list[TextSegment]:
        return split_text(text, chunk_size=self._chunk_size, overlap=self._overlap)

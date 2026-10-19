"""PDF 解析器（Parser 端口实现）：pypdf 提取全文与标题。"""

from pathlib import Path

from pypdf import PdfReader

from app.core.entities.models import ParsedDocument
from app.core.ports.parser import Parser


class PdfParser(Parser):
    """支持 .pdf；标题取文档元数据标题，缺省用首个非空文本行，再退回文件名。"""

    SUPPORTED_SUFFIXES = {".pdf"}

    def can_parse(self, source: str) -> bool:
        return Path(source).suffix.lower() in self.SUPPORTED_SUFFIXES

    def parse(self, source: str) -> ParsedDocument:
        path = Path(source)
        if not path.is_file():
            raise FileNotFoundError(f"文件不存在：{source}")
        if not self.can_parse(source):
            raise ValueError(f"不支持的文件类型：{path.suffix}（当前支持 pdf）")

        try:
            reader = PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages]
        except Exception as exc:  # pypdf 解析损坏 PDF 会抛各种异常，统一转成友好错误
            raise ValueError(f"PDF 解析失败：{exc.__class__.__name__}") from None

        text = "\n\n".join(pages).strip()
        if not text:
            raise ValueError("PDF 解析结果为空（可能是扫描版图片 PDF，暂不支持）")

        title = self._resolve_title(reader, text, path)
        return ParsedDocument(title=title, text=text)

    @staticmethod
    def _resolve_title(reader: PdfReader, text: str, path: Path) -> str:
        meta_title = (reader.metadata.title or "").strip() if reader.metadata else ""
        if meta_title:
            return meta_title
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
        return first_line[:50] or path.stem

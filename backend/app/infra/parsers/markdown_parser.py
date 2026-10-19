"""Markdown / 纯文本解析器（Parser 端口实现）。"""

import re
from pathlib import Path

from app.core.entities.models import ParsedDocument
from app.core.ports.parser import Parser

# 一级标题作为文档标题（没有就退回文件名）
_H1_PATTERN = re.compile(r"^#\s+(.+)$", re.MULTILINE)


class MarkdownParser(Parser):
    """支持 .md / .markdown / .txt；标题取第一个一级标题，缺省用文件名。"""

    SUPPORTED_SUFFIXES = {".md", ".markdown", ".txt"}

    def can_parse(self, source: str) -> bool:
        return Path(source).suffix.lower() in self.SUPPORTED_SUFFIXES

    def parse(self, source: str) -> ParsedDocument:
        path = Path(source)
        if not path.is_file():
            raise FileNotFoundError(f"文件不存在：{source}")
        if not self.can_parse(source):
            raise ValueError(f"不支持的文件类型：{path.suffix}（当前支持 md/txt）")

        # utf-8-sig 兼容带 BOM 的编辑器导出文件
        text = path.read_text(encoding="utf-8-sig")
        match = _H1_PATTERN.search(text)
        title = match.group(1).strip() if match else path.stem
        return ParsedDocument(title=title, text=text)

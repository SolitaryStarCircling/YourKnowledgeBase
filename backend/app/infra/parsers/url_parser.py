"""网页 URL 解析器（Parser 端口实现）：抓取交给 PageFetcher，本类只做 HTML -> 文本。

出网白名单要求网络请求只在 infra/providers/，所以抓取动作通过端口注入。
"""

import re
from html.parser import HTMLParser

from app.core.entities.models import ParsedDocument
from app.core.ports.page_fetcher import PageFetcher
from app.core.ports.parser import Parser

_SKIP_TAGS = {"script", "style", "noscript"}
_BLOCK_TAGS = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section"}


class _HtmlTextExtractor(HTMLParser):
    """剔除脚本/样式后抽取正文与 <title>，块级标签转行。"""

    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._chunks: list[str] = []
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        elif tag == "title":
            self._in_title = True
        elif tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        elif self._skip_depth == 0:
            self._chunks.append(data)

    def text(self) -> str:
        raw = "".join(self._chunks)
        raw = re.sub(r"[ \t]+", " ", raw)
        lines = [line.strip() for line in raw.splitlines()]
        return "\n".join(line for line in lines if line)


class UrlParser(Parser):
    """支持 http(s):// 来源；标题取 <title>，缺省用 URL。"""

    def __init__(self, fetcher: PageFetcher) -> None:
        self._fetcher = fetcher

    def can_parse(self, source: str) -> bool:
        return source.startswith(("http://", "https://"))

    def parse(self, source: str) -> ParsedDocument:
        if not self.can_parse(source):
            raise ValueError(f"不是网页 URL：{source}")

        html = self._fetcher.fetch(source)
        extractor = _HtmlTextExtractor()
        extractor.feed(html)
        extractor.close()

        text = extractor.text()
        if not text:
            raise ValueError("网页正文为空或无法提取文本")

        title = extractor.title.strip() or source
        return ParsedDocument(title=title, text=text)

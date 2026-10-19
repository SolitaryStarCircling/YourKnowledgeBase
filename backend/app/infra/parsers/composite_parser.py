"""组合解析器（Parser 端口实现）：按来源类型分发给具体解析器。

用例层只依赖一个 Parser 端口，新增来源格式 = 新增解析器并在此注册。
"""

from app.core.entities.models import ParsedDocument
from app.core.ports.parser import Parser


class CompositeParser(Parser):
    """依次询问子解析器，交给第一个能处理的；都不认则报友好错误。"""

    def __init__(self, parsers: list[Parser]) -> None:
        self._parsers = parsers

    def can_parse(self, source: str) -> bool:
        return any(parser.can_parse(source) for parser in self._parsers)

    def parse(self, source: str) -> ParsedDocument:
        for parser in self._parsers:
            if parser.can_parse(source):
                return parser.parse(source)
        raise ValueError(f"不支持的来源格式：{source}（当前支持 md/txt/pdf/URL）")

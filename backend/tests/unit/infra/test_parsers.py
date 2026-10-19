"""解析器测试：来源分发、PDF 提取、网页 HTML -> 文本（一律不出网）。"""

from pathlib import Path

import pytest

from app.infra.parsers.composite_parser import CompositeParser
from app.infra.parsers.markdown_parser import MarkdownParser
from app.infra.parsers.pdf_parser import PdfParser
from app.infra.parsers.url_parser import UrlParser
from tests.fakes import FakePageFetcher, make_pdf_bytes

PDF_TEXT = "Coffee brewing needs ninety two degree water."


def _write_pdf(path: Path, title: str, text: str) -> Path:
    path.write_bytes(make_pdf_bytes(title, text))
    return path


def _composite(fetcher: FakePageFetcher | None = None) -> CompositeParser:
    return CompositeParser([MarkdownParser(), PdfParser(), UrlParser(fetcher or FakePageFetcher())])


# ---- CompositeParser 分发 ----


def test_composite_dispatches_by_source_type(tmp_path: Path):
    fetcher = FakePageFetcher({"https://a.dev": "<html><body>hi</body></html>"})
    parser = _composite(fetcher)
    note = tmp_path / "n.md"
    note.write_text("# 你好", encoding="utf-8")
    pdf = _write_pdf(tmp_path / "p.pdf", "P", PDF_TEXT)

    assert parser.can_parse(str(note))
    assert parser.can_parse(str(pdf))
    assert parser.can_parse("https://a.dev")
    assert not parser.can_parse(str(tmp_path / "x.docx"))
    assert parser.parse(str(note)).title == "你好"
    assert "Coffee" in parser.parse(str(pdf)).text
    assert "hi" in parser.parse("https://a.dev").text
    assert fetcher.fetched == ["https://a.dev"]


def test_composite_rejects_unsupported_source(tmp_path: Path):
    with pytest.raises(ValueError, match="不支持的来源格式"):
        _composite().parse(str(tmp_path / "x.docx"))


# ---- PdfParser ----


def test_pdf_parser_extracts_title_and_text(tmp_path: Path):
    pdf = _write_pdf(tmp_path / "note.pdf", "Coffee Notes", PDF_TEXT)

    parsed = PdfParser().parse(str(pdf))

    assert parsed.title == "Coffee Notes"
    assert PDF_TEXT in parsed.text


def test_pdf_parser_falls_back_to_first_line_without_metadata(tmp_path: Path):
    path = tmp_path / "plain.pdf"
    path.write_bytes(make_pdf_bytes("", PDF_TEXT))  # 空标题走首行文本
    parsed = PdfParser().parse(str(path))

    assert parsed.title == PDF_TEXT[:50]


def test_pdf_parser_rejects_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        PdfParser().parse(str(tmp_path / "missing.pdf"))


def test_pdf_parser_rejects_broken_pdf(tmp_path: Path):
    broken = tmp_path / "broken.pdf"
    broken.write_bytes(b"%PDF-1.4 not really a pdf")

    with pytest.raises(ValueError, match="PDF 解析失败"):
        PdfParser().parse(str(broken))


# ---- UrlParser ----


def test_url_parser_extracts_title_and_body_without_script():
    html = """<html><head><title>测试页</title>
    <style>.x{color:red}</style><script>alert(1)</script></head>
    <body><h1>正文标题</h1><p>第一段内容。</p><p>第二段内容。</p></body></html>"""
    fetcher = FakePageFetcher({"https://a.dev/post": html})

    parsed = UrlParser(fetcher).parse("https://a.dev/post")

    assert parsed.title == "测试页"
    assert "正文标题" in parsed.text
    assert "第一段内容。" in parsed.text
    assert "alert" not in parsed.text
    assert "color:red" not in parsed.text


def test_url_parser_title_falls_back_to_url():
    fetcher = FakePageFetcher({"https://a.dev": "<html><body><p>只有正文</p></body></html>"})

    parsed = UrlParser(fetcher).parse("https://a.dev")

    assert parsed.title == "https://a.dev"


def test_url_parser_rejects_non_url():
    with pytest.raises(ValueError, match="不是网页 URL"):
        UrlParser(FakePageFetcher()).parse("note.md")


def test_url_parser_rejects_empty_body():
    fetcher = FakePageFetcher({"https://a.dev": "<html><script>only()</script></html>"})

    with pytest.raises(ValueError, match="正文为空"):
        UrlParser(fetcher).parse("https://a.dev")

"""SQLite 仓储的测试：真实 SQLite + 临时文件，测后自动清理。"""

import sqlite3
from concurrent.futures import ThreadPoolExecutor

from app.core.entities.models import Document, Section
from app.infra.db.sqlite_document_repository import SqliteDocumentRepository
from app.infra.db.sqlite_section_repository import SqliteSectionRepository


def _doc(doc_id: str = "d1", section_id: str | None = None) -> Document:
    return Document(
        doc_id=doc_id,
        title=f"文档{doc_id}",
        source_type="file",
        source=f"{doc_id}.md",
        content_hash="hash",
        chunk_count=2,
        imported_at="2026-01-01T00:00:00+00:00",
        section_id=section_id,
    )


def test_document_round_trip_with_section(tmp_path):
    repo = SqliteDocumentRepository(tmp_path / "meta.db")
    repo.save(_doc("d1", section_id="s1"))

    doc = repo.get_by_source("d1.md")
    assert doc == _doc("d1", section_id="s1")
    assert repo.list_by_section("s1") == [doc]
    assert repo.list_by_section("s2") == []


def test_unassign_section_only_touches_target(tmp_path):
    repo = SqliteDocumentRepository(tmp_path / "meta.db")
    repo.save(_doc("d1", section_id="s1"))
    repo.save(_doc("d2", section_id="s2"))

    repo.unassign_section("s1")

    assert repo.get_by_source("d1.md").section_id is None
    assert repo.get_by_source("d2.md").section_id == "s2"


def test_old_seven_column_schema_is_migrated(tmp_path):
    # 先手工建老版 7 列表并塞一条旧数据，模拟升级前的库
    db_path = tmp_path / "meta.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE documents (
            doc_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source TEXT NOT NULL UNIQUE,
            content_hash TEXT NOT NULL,
            chunk_count INTEGER NOT NULL,
            imported_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "INSERT INTO documents VALUES ('old1', '旧文档', 'file', 'old1.md', 'h', 1, '2025-01-01')"
    )
    conn.commit()
    conn.close()

    repo = SqliteDocumentRepository(db_path)

    doc = repo.get_by_source("old1.md")
    assert doc is not None
    assert doc.doc_id == "old1"
    assert doc.section_id is None  # 迁移出的列默认未分板块
    repo.save(_doc("d2", section_id="s1"))
    assert repo.list_by_section("s1") == [_doc("d2", section_id="s1")]


def test_section_repository_round_trip(tmp_path):
    repo = SqliteSectionRepository(tmp_path / "meta.db")
    section = Section(section_id="s1", name="技术笔记", description="编程相关")
    repo.save(section)

    assert repo.get_by_name("技术笔记") == section
    assert repo.get_by_name("没有这个") is None
    assert repo.list_all() == [section]

    renamed = Section(section_id="s1", name="新名字", description="")
    repo.save(renamed)
    assert repo.get_by_name("技术笔记") is None
    assert repo.list_all() == [renamed]

    repo.delete("s1")
    repo.delete("s1")  # 不存在时静默成功
    assert repo.list_all() == []


def test_repositories_usable_from_worker_thread(tmp_path):
    # 回归：FastAPI 把同步端点放进线程池执行，仓储若限制同线程使用会抛
    # sqlite3.ProgrammingError（线上 /sections 全 500 的根因）
    doc_repo = SqliteDocumentRepository(tmp_path / "meta.db")
    section_repo = SqliteSectionRepository(tmp_path / "meta.db")
    section = Section(section_id="s1", name="技术笔记", description="")

    def work() -> tuple[Section | None, Document | None]:
        section_repo.save(section)
        doc_repo.save(_doc("d1", section_id="s1"))
        return section_repo.get_by_name("技术笔记"), doc_repo.get_by_source("d1.md")

    with ThreadPoolExecutor(max_workers=1) as pool:
        got_section, got_doc = pool.submit(work).result()

    assert got_section == section
    assert got_doc == _doc("d1", section_id="s1")

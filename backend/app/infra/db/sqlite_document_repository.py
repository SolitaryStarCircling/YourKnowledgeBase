"""文档元数据仓储（DocumentRepository 端口实现）：SQLite，单文件零运维。"""

import sqlite3
import threading
from pathlib import Path

from app.core.entities.models import Document
from app.core.ports.document_repository import DocumentRepository

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source TEXT NOT NULL UNIQUE,
    content_hash TEXT NOT NULL,
    chunk_count INTEGER NOT NULL,
    imported_at TEXT NOT NULL,
    section_id TEXT
)
"""

# section_id 必须放最后，保证 Document(*row) 位置还原与实体字段顺序一致
_COLUMNS = "doc_id, title, source_type, source, content_hash, chunk_count, imported_at, section_id"


class SqliteDocumentRepository(DocumentRepository):
    def __init__(self, db_path: str | Path) -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        # FastAPI 把同步端点放进线程池执行，连接需允许跨线程使用；
        # 同一连接并发交叉读写会串语句，用锁把访问串行化。
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._lock = threading.Lock()
        self._conn.execute(_SCHEMA)
        self._ensure_section_column()
        self._conn.commit()

    def _ensure_section_column(self) -> None:
        """老库（无 section_id 列）就地补列，保留已有文档数据。"""
        columns = [row[1] for row in self._conn.execute("PRAGMA table_info(documents)")]
        if "section_id" not in columns:
            self._conn.execute("ALTER TABLE documents ADD COLUMN section_id TEXT")

    def get_by_source(self, source: str) -> Document | None:
        with self._lock:
            row = self._conn.execute(
                f"SELECT {_COLUMNS} FROM documents WHERE source = ?",
                (source,),
            ).fetchone()
        return Document(*row) if row else None

    def save(self, document: Document) -> None:
        with self._lock:
            self._conn.execute(
                f"INSERT OR REPLACE INTO documents ({_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    document.doc_id,
                    document.title,
                    document.source_type,
                    document.source,
                    document.content_hash,
                    document.chunk_count,
                    document.imported_at,
                    document.section_id,
                ),
            )
            self._conn.commit()

    def delete(self, doc_id: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            self._conn.commit()

    def list_by_section(self, section_id: str) -> list[Document]:
        with self._lock:
            rows = self._conn.execute(
                f"SELECT {_COLUMNS} FROM documents WHERE section_id = ? ORDER BY imported_at",
                (section_id,),
            ).fetchall()
        return [Document(*row) for row in rows]

    def unassign_section(self, section_id: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE documents SET section_id = NULL WHERE section_id = ?",
                (section_id,),
            )
            self._conn.commit()

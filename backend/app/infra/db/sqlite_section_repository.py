"""板块元数据仓储（SectionRepository 端口实现）：SQLite，与文档元数据共用 meta.db。"""

import sqlite3
import threading
from pathlib import Path

from app.core.entities.models import Section
from app.core.ports.section_repository import SectionRepository

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sections (
    section_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT ''
)
"""

_COLUMNS = "section_id, name, description"


class SqliteSectionRepository(SectionRepository):
    def __init__(self, db_path: str | Path) -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        # FastAPI 把同步端点放进线程池执行，连接需允许跨线程使用；
        # 同一连接并发交叉读写会串语句，用锁把访问串行化。
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._lock = threading.Lock()
        self._conn.execute(_SCHEMA)
        self._conn.commit()

    def get_by_name(self, name: str) -> Section | None:
        with self._lock:
            row = self._conn.execute(
                f"SELECT {_COLUMNS} FROM sections WHERE name = ?",
                (name,),
            ).fetchone()
        return Section(*row) if row else None

    def list_all(self) -> list[Section]:
        with self._lock:
            rows = self._conn.execute(f"SELECT {_COLUMNS} FROM sections ORDER BY rowid").fetchall()
        return [Section(*row) for row in rows]

    def save(self, section: Section) -> None:
        with self._lock:
            self._conn.execute(
                f"INSERT OR REPLACE INTO sections ({_COLUMNS}) VALUES (?, ?, ?)",
                (section.section_id, section.name, section.description),
            )
            self._conn.commit()

    def delete(self, section_id: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM sections WHERE section_id = ?", (section_id,))
            self._conn.commit()

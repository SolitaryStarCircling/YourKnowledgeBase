"""端口：板块元数据仓储。实现放 infra/db/（SQLite）。"""

from abc import ABC, abstractmethod

from app.core.entities.models import Section


class SectionRepository(ABC):
    """板块（数据分区）元数据的 CRUD（文档归属由 DocumentRepository 管）。"""

    @abstractmethod
    def get_by_name(self, name: str) -> Section | None:
        """按名称查板块（名称唯一）；不存在返回 None。"""

    @abstractmethod
    def list_all(self) -> list[Section]:
        """列出全部板块，按创建顺序。"""

    @abstractmethod
    def save(self, section: Section) -> None:
        """新增或更新板块（按 section_id 覆盖）。"""

    @abstractmethod
    def delete(self, section_id: str) -> None:
        """删除板块；不存在时静默成功。"""

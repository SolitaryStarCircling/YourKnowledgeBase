"""端口：文档元数据仓储。实现放 infra/db/（SQLite）。"""

from abc import ABC, abstractmethod

from app.core.entities.models import Document


class DocumentRepository(ABC):
    """文档元数据的 CRUD（正文与向量不归它管）。"""

    @abstractmethod
    def get_by_source(self, source: str) -> Document | None:
        """按来源查已导入的文档；未导入过返回 None。"""

    @abstractmethod
    def save(self, document: Document) -> None:
        """新增或更新文档元数据（按 doc_id 覆盖）。"""

    @abstractmethod
    def delete(self, doc_id: str) -> None:
        """删除文档元数据；不存在时静默成功。"""

    @abstractmethod
    def list_by_section(self, section_id: str) -> list[Document]:
        """列出归属某板块的全部文档（板块过滤检索的依据）。"""

    @abstractmethod
    def unassign_section(self, section_id: str) -> None:
        """把某板块下的全部文档回归"未分板块"（删除板块时调用）。"""

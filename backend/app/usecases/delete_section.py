"""用例：删除板块；板块下的文档回归"未分板块"，文档本身不删除。"""

from app.core.ports.document_repository import DocumentRepository
from app.core.ports.section_repository import SectionRepository
from app.core.services.sections import find_section_by_name


def delete_section(
    name: str,
    *,
    section_repo: SectionRepository,
    doc_repo: DocumentRepository,
) -> None:
    """按名称删除板块，文档归属清空但文档保留。"""
    section = find_section_by_name(name, section_repo=section_repo)
    doc_repo.unassign_section(section.section_id)
    section_repo.delete(section.section_id)

"""用例：列出全部板块。"""

from app.core.entities.models import Section
from app.core.ports.section_repository import SectionRepository


def list_sections(*, section_repo: SectionRepository) -> list[Section]:
    """按创建顺序返回全部板块。"""
    return section_repo.list_all()

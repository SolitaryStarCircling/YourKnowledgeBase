"""用例：创建板块（数据分区）。"""

from uuid import uuid4

from app.core.entities.models import Section
from app.core.ports.section_repository import SectionRepository
from app.core.services.sections import normalize_section_name


def create_section(
    name: str,
    *,
    section_repo: SectionRepository,
    description: str = "",
) -> Section:
    """新建板块；名称唯一，重名报错。"""
    clean_name = normalize_section_name(name)
    if section_repo.get_by_name(clean_name) is not None:
        raise ValueError(f"板块名称已存在：{clean_name}")

    section = Section(
        section_id=uuid4().hex,
        name=clean_name,
        description=description.strip(),
    )
    section_repo.save(section)
    return section

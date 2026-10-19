"""用例：修改板块的名称或描述（按名称定位，section_id 保持不变）。"""

from app.core.entities.models import Section
from app.core.ports.section_repository import SectionRepository
from app.core.services.sections import find_section_by_name, normalize_section_name


def update_section(
    name: str,
    *,
    section_repo: SectionRepository,
    new_name: str | None = None,
    description: str | None = None,
) -> Section:
    """修改板块；section_id 不变，所以文档归属不受重命名影响。"""
    if new_name is None and description is None:
        raise ValueError("请指定要修改的名称或描述")

    section = find_section_by_name(name, section_repo=section_repo)

    updated_name = normalize_section_name(new_name) if new_name is not None else section.name
    if updated_name != section.name:
        conflict = section_repo.get_by_name(updated_name)
        if conflict is not None and conflict.section_id != section.section_id:
            raise ValueError(f"板块名称已存在：{updated_name}")

    updated = Section(
        section_id=section.section_id,
        name=updated_name,
        description=description.strip() if description is not None else section.description,
    )
    section_repo.save(updated)
    return updated

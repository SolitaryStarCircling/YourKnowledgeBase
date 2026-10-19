"""板块业务规则：名称规范化与按名称定位（纯 Python）。"""

from app.core.entities.models import Section
from app.core.ports.section_repository import SectionRepository


def normalize_section_name(name: str) -> str:
    """去掉首尾空白后的名称；空白名称是无效输入。"""
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("板块名称不能为空")
    return cleaned


def find_section_by_name(name: str, *, section_repo: SectionRepository) -> Section:
    """按名称定位板块；不存在时报错。"""
    clean_name = normalize_section_name(name)
    section = section_repo.get_by_name(clean_name)
    if section is None:
        raise ValueError(f"板块不存在：{clean_name}（先用 section create 创建）")
    return section

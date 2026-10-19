"""core 板块业务规则的测试：名称规范化与按名称定位。"""

import pytest

from app.core.entities.models import Section
from app.core.services.sections import find_section_by_name, normalize_section_name
from tests.fakes import InMemorySectionRepository


def test_normalize_strips_whitespace():
    assert normalize_section_name("  技术笔记  ") == "技术笔记"


@pytest.mark.parametrize("bad", ["", "   ", "\t\n"])
def test_normalize_rejects_blank_name(bad: str):
    with pytest.raises(ValueError, match="名称不能为空"):
        normalize_section_name(bad)


def test_find_returns_existing_section():
    repo = InMemorySectionRepository()
    section = Section(section_id="s1", name="技术笔记", description="")
    repo.save(section)

    assert find_section_by_name(" 技术笔记 ", section_repo=repo) == section


def test_find_missing_section_raises():
    repo = InMemorySectionRepository()
    with pytest.raises(ValueError, match="板块不存在"):
        find_section_by_name("不存在的板块", section_repo=repo)

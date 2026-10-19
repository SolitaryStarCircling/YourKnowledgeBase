"""板块 CRUD 用例的测试：全部使用 Mock 端口，不调用真实 API。"""

import pytest

from app.core.entities.models import Document
from app.usecases.create_section import create_section
from app.usecases.delete_section import delete_section
from app.usecases.list_sections import list_sections
from app.usecases.update_section import update_section
from tests.fakes import InMemoryDocumentRepository, InMemorySectionRepository


def _doc(doc_id: str, section_id: str | None) -> Document:
    return Document(
        doc_id=doc_id,
        title=f"文档{doc_id}",
        source_type="file",
        source=f"{doc_id}.md",
        content_hash="h",
        chunk_count=1,
        imported_at="2026-01-01T00:00:00+00:00",
        section_id=section_id,
    )


def test_create_section_and_list():
    repo = InMemorySectionRepository()
    created = create_section("  技术笔记 ", section_repo=repo, description="  编程相关  ")

    assert created.name == "技术笔记"
    assert created.description == "编程相关"
    assert list_sections(section_repo=repo) == [created]


def test_create_duplicate_name_is_rejected():
    repo = InMemorySectionRepository()
    create_section("技术笔记", section_repo=repo)

    with pytest.raises(ValueError, match="已存在"):
        create_section("技术笔记", section_repo=repo)


def test_create_blank_name_is_rejected():
    repo = InMemorySectionRepository()
    with pytest.raises(ValueError, match="名称不能为空"):
        create_section("   ", section_repo=repo)


def test_update_renames_without_touching_section_id():
    repo = InMemorySectionRepository()
    created = create_section("旧名", section_repo=repo)

    updated = update_section("旧名", section_repo=repo, new_name="新名")

    assert updated.section_id == created.section_id
    assert updated.name == "新名"
    assert repo.get_by_name("旧名") is None


def test_update_to_existing_name_is_rejected():
    repo = InMemorySectionRepository()
    create_section("技术笔记", section_repo=repo)
    create_section("生活笔记", section_repo=repo)

    with pytest.raises(ValueError, match="已存在"):
        update_section("生活笔记", section_repo=repo, new_name="技术笔记")


def test_update_without_change_request_is_rejected():
    repo = InMemorySectionRepository()
    create_section("技术笔记", section_repo=repo)

    with pytest.raises(ValueError, match="请指定"):
        update_section("技术笔记", section_repo=repo)


def test_update_missing_section_is_rejected():
    repo = InMemorySectionRepository()
    with pytest.raises(ValueError, match="板块不存在"):
        update_section("没有这个", section_repo=repo, new_name="新名")


def test_delete_unassigns_docs_but_keeps_them():
    section_repo = InMemorySectionRepository()
    doc_repo = InMemoryDocumentRepository()
    section = create_section("技术笔记", section_repo=section_repo)
    doc_repo.save(_doc("d1", section.section_id))
    doc_repo.save(_doc("d2", None))

    delete_section("技术笔记", section_repo=section_repo, doc_repo=doc_repo)

    assert section_repo.list_all() == []
    assert doc_repo.docs["d1"].section_id is None  # 文档回归未分板块
    assert "d2" in doc_repo.docs  # 文档本身不删


def test_delete_missing_section_is_rejected():
    repo = InMemorySectionRepository()
    with pytest.raises(ValueError, match="板块不存在"):
        delete_section("没有这个", section_repo=repo, doc_repo=InMemoryDocumentRepository())

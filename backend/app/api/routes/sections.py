"""板块管理路由：POST /sections、GET /sections、PATCH /sections/{name}、DELETE /sections/{name}。"""

from fastapi import APIRouter, Response

from app.api.deps import ContainerDep
from app.api.schemas import SectionCreateRequest, SectionModel, SectionUpdateRequest
from app.usecases.create_section import create_section
from app.usecases.delete_section import delete_section
from app.usecases.list_sections import list_sections
from app.usecases.update_section import update_section

router = APIRouter()


@router.post("/sections", response_model=SectionModel, status_code=201)
def section_create(body: SectionCreateRequest, container: ContainerDep) -> SectionModel:
    section = create_section(
        body.name, section_repo=container.section_repo, description=body.description
    )
    return SectionModel.from_section(section)


@router.get("/sections", response_model=list[SectionModel])
def section_list(container: ContainerDep) -> list[SectionModel]:
    sections = list_sections(section_repo=container.section_repo)
    return [SectionModel.from_section(section) for section in sections]


@router.patch("/sections/{name}", response_model=SectionModel)
def section_update(name: str, body: SectionUpdateRequest, container: ContainerDep) -> SectionModel:
    section = update_section(
        name,
        section_repo=container.section_repo,
        new_name=body.new_name,
        description=body.description,
    )
    return SectionModel.from_section(section)


@router.delete("/sections/{name}", status_code=204)
def section_delete(name: str, container: ContainerDep) -> Response:
    delete_section(name, section_repo=container.section_repo, doc_repo=container.doc_repo)
    return Response(status_code=204)

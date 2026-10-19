"""文档导入路由：POST /documents/import。"""

from fastapi import APIRouter

from app.api.deps import ContainerDep, SessionDep
from app.api.schemas import ImportRequest, ImportResponse
from app.usecases.import_document import import_document

router = APIRouter()


@router.post("/documents/import", response_model=ImportResponse)
def import_doc(body: ImportRequest, container: ContainerDep, session: SessionDep) -> ImportResponse:
    embedder = container.embedder_factory(session)
    result = import_document(
        body.source,
        parser=container.parser,
        chunker=container.chunker,
        embedder=embedder,
        vector_store=container.vector_store,
        doc_repo=container.doc_repo,
        section_repo=container.section_repo,
        section=body.section,
    )
    return ImportResponse.from_result(result)

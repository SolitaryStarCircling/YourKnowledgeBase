"""检索与问答路由：POST /search、POST /ask。"""

from fastapi import APIRouter

from app.api.deps import ContainerDep, SessionDep
from app.api.schemas import AskRequest, AskResponse, SearchHitModel, SearchRequest, SearchResponse
from app.usecases.answer_question import answer_question
from app.usecases.semantic_search import semantic_search

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
def search(body: SearchRequest, container: ContainerDep, session: SessionDep) -> SearchResponse:
    embedder = container.embedder_factory(session)
    hits = semantic_search(
        body.query,
        embedder=embedder,
        vector_store=container.vector_store,
        top_k=body.top_k,
        section=body.section,
        section_repo=container.section_repo,
        doc_repo=container.doc_repo,
    )
    return SearchResponse(hits=[SearchHitModel.from_hit(hit) for hit in hits])


@router.post("/ask", response_model=AskResponse)
def ask(body: AskRequest, container: ContainerDep, session: SessionDep) -> AskResponse:
    embedder = container.embedder_factory(session)
    llm = container.llm_factory(session)
    answer = answer_question(
        body.question,
        llm=llm,
        embedder=embedder,
        vector_store=container.vector_store,
        top_k=body.top_k,
        section=body.section,
        section_repo=container.section_repo,
        doc_repo=container.doc_repo,
    )
    return AskResponse.from_answer(answer)

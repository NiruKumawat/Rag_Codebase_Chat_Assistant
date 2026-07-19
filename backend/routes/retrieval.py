from fastapi import APIRouter, HTTPException

from backend.core.settings import settings
from backend.services.groq_service import generate_answer
from backend.services.retrieval_service import retrieve_top_chunks
from backend.schemas.retrieval import RetrievalRequest, RetrievalResponse


router = APIRouter(prefix="/api", tags=["Retrieval"])


@router.post("/retrieve", response_model=RetrievalResponse)
def retrieve_chunks(payload: RetrievalRequest) -> RetrievalResponse:
    question = payload.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    results = retrieve_top_chunks(question, top_k=settings.retrieval_top_k)

    try:
        answer = generate_answer(question, results)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return RetrievalResponse(question=question, top_k=settings.retrieval_top_k, results=results, answer=answer)
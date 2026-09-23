from fastapi import APIRouter, HTTPException
import logging

from backend.core.settings import settings
from backend.services.groq_service import generate_answer
from backend.services.retrieval_service import retrieve_top_chunks
from backend.schemas.retrieval import RetrievalRequest, RetrievalResponse


logger = logging.getLogger("rag_app.retrieval")
router = APIRouter(prefix="/api", tags=["Retrieval"])


@router.post("/retrieve", response_model=RetrievalResponse)
def retrieve_chunks(payload: RetrievalRequest) -> RetrievalResponse:
    question = payload.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        results = retrieve_top_chunks(question, top_k=settings.retrieval_top_k)
    except Exception as exc:
        logger.exception("Retrieval failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(exc)}") from exc

    try:
        answer = generate_answer(question, results)
        print(f"🤖 GENERATED ANSWER:\n{answer}\n", flush=True)
    except ValueError as exc:
        logger.error("Groq generation rejected: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Groq generation crashed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Groq generation failed: {str(exc)}") from exc

    return RetrievalResponse(question=question, top_k=settings.retrieval_top_k, results=results, answer=answer)
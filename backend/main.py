import logging
import time
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.exception_handlers import register_exception_handlers
from backend.core.logging_config import configure_logging
from backend.core.settings import ensure_directories, settings
from backend.routes.upload import router as upload_router
from backend.routes.retrieval import router as retrieval_router


configure_logging()
ensure_directories()

logger = logging.getLogger("rag_app")


def _prewarm_model() -> None:
    """Load the embedding model at startup so the first upload isn't slow."""
    try:
        from backend.services.embedding_service import get_embedding_model
        logger.info("Pre-warming embedding model in background…")
        get_embedding_model()
        logger.info("Embedding model ready.")
    except Exception:
        logger.exception("Failed to pre-warm embedding model — it will load on first request instead.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start model warm-up in a daemon thread so startup isn't blocked.
    threading.Thread(target=_prewarm_model, daemon=True).start()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Backend API for document ingestion and retrieval-augmented chat.",
    version=settings.app_version,
    lifespan=lifespan,
)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request, call_next):
    started_at = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started_at) * 1000
    logger.info("%s %s -> %s in %.2fms", request.method, request.url.path, response.status_code, elapsed_ms)
    return response


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "message": "RAG backend is running",
        "status": "ok",
        "version": settings.app_version,
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }


app.include_router(upload_router)
app.include_router(retrieval_router)

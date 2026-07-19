import logging
from typing import Any

from backend.core.settings import settings


logger = logging.getLogger("rag_app.embedding")
MODEL_NAME = settings.embedding_model_name
_model: Any | None = None


def get_embedding_model() -> Any:
    global _model

    if _model is None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model: %s", MODEL_NAME)
        _model = SentenceTransformer(MODEL_NAME)

    return _model


def generate_embeddings(chunks: list[str]) -> list[list[float]]:
    if not chunks:
        return []

    model = get_embedding_model()
    embeddings = model.encode(
        chunks,
        convert_to_numpy=True,
        batch_size=32,
        show_progress_bar=False,
    )

    return embeddings.tolist()
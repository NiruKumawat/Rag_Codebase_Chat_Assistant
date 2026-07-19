import logging
from typing import Any

from backend.core.settings import settings
from backend.services.embedding_service import generate_embeddings
from backend.services.faiss_store import load_faiss_store


logger = logging.getLogger("rag_app.retrieval")


def retrieve_top_chunks(question: str, top_k: int = settings.retrieval_top_k) -> list[dict[str, object]]:
    import faiss
    import numpy as np

    cleaned_question = question.strip()

    if not cleaned_question:
        return []

    index, metadata = load_faiss_store()

    if index.ntotal == 0 or not metadata:
        logger.info("No FAISS content available for retrieval.")
        return []

    question_embedding = generate_embeddings([cleaned_question])[0]
    query_vector = np.asarray([question_embedding], dtype="float32")
    faiss.normalize_L2(query_vector)

    query_result = index.search(query_vector, top_k)
    scores = query_result[0][0]
    ids = query_result[1][0]

    metadata_by_id = {int(item["id"]): item for item in metadata}
    results: list[dict[str, object]] = []

    for score, vector_id in zip(scores, ids):
        if vector_id == -1:
            continue

        chunk_info = metadata_by_id.get(int(vector_id))

        if chunk_info is None:
            continue

        results.append(
            {
                "id": int(vector_id),
                "score": float(score),
                "chunk_index": chunk_info["chunk_index"],
                "source_files": chunk_info["source_files"],
                "text": chunk_info["text"],
            }
        )

    logger.info("Retrieved %s chunks for question.", len(results))
    return results
import logging
import sys
from typing import Any

from backend.core.settings import settings
from backend.services.embedding_service import generate_embeddings
from backend.services.faiss_store import load_faiss_store


logger = logging.getLogger("rag_app.retrieval")


def print_retrieved_chunks(question: str, results: list[dict[str, object]]) -> None:
    """Pretty-print the retrieval results directly to the terminal."""
    sep = "=" * 78
    line = "-" * 78
    output_lines = [
        "",
        sep,
        f"🔍 QUESTION: {question}",
        f"📊 RETRIEVED CHUNKS: {len(results)}",
        sep,
    ]

    if not results:
        output_lines.append("  ⚠️ No matching chunks found in FAISS index.")
    else:
        for i, chunk in enumerate(results, start=1):
            score = chunk.get("score", 0.0)
            sources = ", ".join(chunk.get("source_files", []))
            chunk_idx = chunk.get("chunk_index", "N/A")
            raw_text = str(chunk.get("text", "")).strip()

            output_lines.append(f"▶ [Chunk {i}] Similarity Score: {score:.4f} | Source: {sources} (Chunk #{chunk_idx})")
            output_lines.append(line)
            # Indent text for readability
            indented_text = "\n".join("   " + t for t in raw_text.splitlines())
            output_lines.append(indented_text)
            output_lines.append(line)

    output_lines.append(sep)
    output_lines.append("")

    full_output = "\n".join(output_lines)
    # Output to stdout safely
    print(full_output, flush=True)


def retrieve_top_chunks(question: str, top_k: int = settings.retrieval_top_k) -> list[dict[str, object]]:
    # pyrefly: ignore [missing-import]
    import faiss
    import numpy as np

    cleaned_question = question.strip()

    if not cleaned_question:
        return []

    logger.info("Starting retrieval for question: '%s' (top_k=%d)", cleaned_question, top_k)
    index, metadata = load_faiss_store()

    if index.ntotal == 0 or not metadata:
        logger.warning("No FAISS content available for retrieval. (total_vectors=0)")
        print_retrieved_chunks(cleaned_question, [])
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

    logger.info("Successfully retrieved %d chunks for question.", len(results))
    # Pretty-print retrieved chunks directly to terminal
    print_retrieved_chunks(cleaned_question, results)

    return results
import logging
import json

from typing import Any

from backend.core.settings import settings


logger = logging.getLogger("rag_app.faiss")


FAISS_DIR = settings.faiss_dir
INDEX_PATH = FAISS_DIR / "documents.index"
METADATA_PATH = FAISS_DIR / "chunk_metadata.json"
EMBEDDING_DIMENSION = 384

FAISS_DIR.mkdir(parents=True, exist_ok=True)


def build_index() -> Any:
    import faiss

    base_index = faiss.IndexFlatIP(EMBEDDING_DIMENSION)
    return faiss.IndexIDMap2(base_index)


def load_faiss_store() -> tuple[Any, list[dict[str, object]]]:
    import faiss

    if INDEX_PATH.exists():
        index = faiss.read_index(str(INDEX_PATH))
    else:
        index = build_index()

    if METADATA_PATH.exists():
        metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    else:
        metadata = []

    return index, metadata


def save_faiss_store(index: Any, metadata: list[dict[str, object]]) -> None:
    import faiss

    faiss.write_index(index, str(INDEX_PATH))
    METADATA_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def store_chunks_in_faiss(
    chunks: list[str],
    embeddings: list[list[float]],
    source_files: list[str],
) -> dict[str, object]:
    import faiss
    import numpy as np

    if not chunks or not embeddings:
        index, metadata = load_faiss_store()
        save_faiss_store(index, metadata)
        return {
            "added": 0,
            "total_vectors": index.ntotal,
            "index_path": str(INDEX_PATH),
            "metadata_path": str(METADATA_PATH),
        }

    index, metadata = load_faiss_store()

    if len(chunks) != len(embeddings):
        raise ValueError("The number of chunks must match the number of embeddings.")

    embedding_array = np.asarray(embeddings, dtype="float32")
    faiss.normalize_L2(embedding_array)

    if embedding_array.shape[1] != EMBEDDING_DIMENSION:
        raise ValueError(f"Expected embeddings with {EMBEDDING_DIMENSION} dimensions")

    next_id = max((int(item["id"]) for item in metadata), default=-1) + 1
    vector_ids = np.arange(next_id, next_id + len(chunks), dtype="int64")

    index.add_with_ids(embedding_array, vector_ids)

    for offset, chunk in enumerate(chunks):
        metadata.append(
            {
                "id": int(vector_ids[offset]),
                "chunk_index": offset,
                "source_files": source_files,
                "text": chunk,
            }
        )

    save_faiss_store(index, metadata)

    logger.info("Stored %s chunks in FAISS. Total vectors: %s", len(chunks), index.ntotal)

    return {
        "added": len(chunks),
        "total_vectors": index.ntotal,
        "index_path": str(INDEX_PATH),
        "metadata_path": str(METADATA_PATH),
    }
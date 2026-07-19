import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.core.settings import settings
from backend.services.embedding_service import generate_embeddings
from backend.services.faiss_store import store_chunks_in_faiss
from backend.services.pdf_text_extractor import extract_text_from_pdfs
from backend.services.text_chunker import chunk_text
from backend.schemas.upload import UploadResponse


router = APIRouter(prefix="/api", tags=["Upload"])
logger = logging.getLogger("rag_app.upload")

UPLOAD_DIR = settings.upload_dir
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", response_model=UploadResponse)
async def upload_pdfs(files: list[UploadFile] = File(...)) -> UploadResponse:
    if not files:
        raise HTTPException(status_code=400, detail="At least one PDF file is required.")

    if len(files) > settings.max_upload_files:
        raise HTTPException(
            status_code=413,
            detail=f"You can upload at most {settings.max_upload_files} PDF files at a time.",
        )

    saved_files: list[str] = []
    saved_paths: list[Path] = []
    written_paths: list[Path] = []
    staged_uploads: list[tuple[str, Path, bytes]] = []

    try:
        for file in files:
            try:
                original_name = file.filename or ""
                safe_name = Path(original_name).name
                is_pdf_name = safe_name.lower().endswith(".pdf")
                is_pdf_content_type = file.content_type == "application/pdf"

                if not (is_pdf_name and is_pdf_content_type):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Only PDF files are allowed. Invalid file: {original_name}",
                    )

                file_bytes = await file.read()

                if len(file_bytes) > settings.max_pdf_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"{original_name} exceeds the maximum allowed size of {settings.max_pdf_size_mb} MB.",
                    )

                stored_name = f"{Path(safe_name).stem}_{uuid4().hex[:8]}{Path(safe_name).suffix}"
                destination = UPLOAD_DIR / stored_name
                staged_uploads.append((safe_name, destination, file_bytes))
            finally:
                await file.close()

        for safe_name, destination, file_bytes in staged_uploads:
            destination.write_bytes(file_bytes)
            saved_files.append(safe_name)
            saved_paths.append(destination)
            written_paths.append(destination)

        logger.info("Accepted %s PDFs: %s", len(saved_files), ", ".join(saved_files))

        extracted_text = extract_text_from_pdfs(saved_paths)
        chunks = chunk_text(extracted_text, chunk_size=500, overlap=50)
        embeddings = generate_embeddings(chunks)
        faiss_result = store_chunks_in_faiss(chunks, embeddings, saved_files)

        logger.info("Indexed %s chunks into FAISS.", faiss_result["added"])

        return UploadResponse(
            message="PDF files uploaded, text extracted, chunked, embedded, and stored in FAISS successfully.",
            files=saved_files,
            count=len(saved_files),
            chunks=chunks,
            faiss=faiss_result,
        )
    except HTTPException:
        for path in written_paths:
            if path.exists():
                path.unlink(missing_ok=True)
        raise
    except ValueError as exc:
        for path in written_paths:
            if path.exists():
                path.unlink(missing_ok=True)
        logger.exception("Upload pipeline failed")
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        for path in written_paths:
            if path.exists():
                path.unlink(missing_ok=True)
        logger.exception("Unexpected upload failure")
        raise HTTPException(status_code=500, detail="Failed to process uploaded PDFs.") from exc
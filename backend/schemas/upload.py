from pydantic import BaseModel, Field


class FaissWriteResult(BaseModel):
    added: int = Field(..., ge=0)
    total_vectors: int = Field(..., ge=0)
    index_path: str
    metadata_path: str


class UploadResponse(BaseModel):
    message: str
    files: list[str]
    count: int = Field(..., ge=0)
    chunks: list[str]
    faiss: FaissWriteResult
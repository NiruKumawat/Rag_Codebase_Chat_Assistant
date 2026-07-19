from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="User question for semantic retrieval")


class RetrievedChunk(BaseModel):
    id: int
    score: float
    chunk_index: int
    source_files: list[str]
    text: str


class RetrievalResponse(BaseModel):
    question: str
    top_k: int
    results: list[RetrievedChunk]
    answer: str
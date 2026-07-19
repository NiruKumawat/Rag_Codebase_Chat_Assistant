# RAG-Based Document Chatbot

Production-oriented FastAPI + React RAG scaffold with PDF upload, text extraction, chunking, embeddings, FAISS persistence, retrieval, and Groq answer generation.

## Backend structure

- `backend/core/`: application settings, logging, and exception handling.
- `backend/routes/`: HTTP route handlers for upload and retrieval.
- `backend/schemas/`: typed request and response models.
- `backend/services/`: PDF extraction, chunking, embeddings, FAISS, retrieval, and Groq orchestration.
- `backend/uploads/`: local storage for uploaded PDFs.
- `backend/faiss_index/`: local FAISS index files and chunk metadata.
- `backend/logs/`: rotating application log files.

## Frontend structure

- `frontend/src/components/`: reusable UI pieces such as upload, chat, message bubble, and loading indicator.
- `frontend/src/services/`: Axios client reserved for future backend integration.
- `frontend/src/styles.css`: global styling and layout.

## Environment

Copy `.env.example` to `.env` and fill in the Groq API key before running the answer-generation endpoint.
# RAG-Based Document Chatbot

Step 1 project scaffold created.

## Structure

- backend/
  - routes/
  - services/
  - uploads/
  - faiss_index/
- frontend/
  - src/
  - public/
- requirements.txt
- .env
- README.md

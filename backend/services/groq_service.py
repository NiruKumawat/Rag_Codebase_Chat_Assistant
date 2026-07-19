import logging

from backend.core.settings import settings


logger = logging.getLogger("rag_app.groq")

GROQ_API_KEY = settings.groq_api_key
MODEL_NAME = settings.groq_model_name
_client = None


def get_groq_client():
    global _client

    if _client is None:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not configured in .env")

        from groq import Groq

        logger.info("Creating Groq client for model: %s", MODEL_NAME)
        _client = Groq(api_key=GROQ_API_KEY)

    return _client


def build_prompt(question: str, retrieved_chunks: list[dict[str, object]]) -> list[dict[str, str]]:
    context_lines: list[str] = []
    max_chunk_characters = 1500

    for index, chunk in enumerate(retrieved_chunks, start=1):
        chunk_text = str(chunk["text"])
        clipped_text = chunk_text[:max_chunk_characters]
        context_lines.append(
            f"Chunk {index} | score={chunk['score']:.4f} | source={', '.join(chunk['source_files'])}\n{clipped_text}"
        )

    context_block = "\n\n".join(context_lines) if context_lines else "No relevant context was retrieved."

    return [
        {
            "role": "system",
            "content": (
                "You are a precise RAG assistant. Answer only from the provided context when possible. "
                "If the context is insufficient, say that the documents do not contain enough information. "
                "Do not invent facts. Keep the answer clear and concise."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question:\n{question}\n\n"
                f"Retrieved context:\n{context_block}\n\n"
                "Answer the question using the retrieved context."
            ),
        },
    ]


def generate_answer(question: str, retrieved_chunks: list[dict[str, object]]) -> str:
    client = get_groq_client()
    messages = build_prompt(question, retrieved_chunks)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.2,
    )

    return response.choices[0].message.content or ""
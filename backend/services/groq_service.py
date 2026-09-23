import logging
from backend.core.settings import settings

logger = logging.getLogger("rag_app.groq")
_client = None

CANDIDATE_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "llama3-8b-8192",
]


def get_groq_client():
    global _client
    api_key = settings.groq_api_key.strip()

    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured in .env")

    if _client is None or getattr(_client, "_custom_api_key", None) != api_key:
        from groq import Groq

        logger.info("Creating Groq client...")
        _client = Groq(api_key=api_key)
        _client._custom_api_key = api_key

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

    # Models to try: configured model first, then known working candidate models
    configured_model = settings.groq_model_name
    models_to_try = [configured_model] + [m for m in CANDIDATE_MODELS if m != configured_model]

    last_exc = None
    for model_name in models_to_try:
        try:
            logger.info("Sending request to Groq model: %s", model_name)
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=settings.groq_temperature,
                top_p=settings.groq_top_p,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            err_msg = str(exc)
            logger.warning("Groq model %s failed: %s", model_name, err_msg)
            last_exc = exc
            if "invalid_api_key" in err_msg.lower() or "401" in err_msg:
                raise ValueError(
                    "Invalid Groq API Key. Please get a free API key from https://console.groq.com/keys and update GROQ_API_KEY in your .env file."
                ) from exc
            if "model_not_found" in err_msg.lower() or "404" in err_msg:
                continue
            raise

    if last_exc:
        raise last_exc

    return ""
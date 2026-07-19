from dataclasses import dataclass, field
from functools import lru_cache
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]


def _load_dotenv_file(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv_file(BASE_DIR / ".env")

DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000,http://127.0.0.1:3000,"
    "http://localhost:5173,http://127.0.0.1:5173"
)


def _csv_env(name: str, default: str) -> tuple[str, ...]:
    value = os.getenv(name, default)
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _resolve_path(name: str, default: str) -> Path:
    candidate = Path(os.getenv(name, default))
    return candidate if candidate.is_absolute() else (BASE_DIR / candidate).resolve()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "RAG Document Chatbot API")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model_name: str = os.getenv("MODEL_NAME", "llama-3.1-8b-instant")
    embedding_model_name: str = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2",
    )
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: _csv_env("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    )
    upload_dir: Path = field(default_factory=lambda: _resolve_path("UPLOAD_DIR", "backend/uploads"))
    faiss_dir: Path = field(default_factory=lambda: _resolve_path("FAISS_INDEX_PATH", "backend/faiss_index"))
    log_file: Path = field(default_factory=lambda: _resolve_path("LOG_FILE", "backend/logs/app.log"))
    max_upload_files: int = int(os.getenv("MAX_UPLOAD_FILES", "10"))
    max_pdf_size_mb: int = int(os.getenv("MAX_PDF_SIZE_MB", "25"))
    retrieval_top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "3"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def max_pdf_bytes(self) -> int:
        return self.max_pdf_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def ensure_directories() -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.faiss_dir.mkdir(parents=True, exist_ok=True)
    settings.log_file.parent.mkdir(parents=True, exist_ok=True)
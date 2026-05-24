"""Application settings loaded from environment / .env."""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root = parent of backend/
REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    courtlistener_api_token: str = Field(default="", alias="COURTLISTENER_API_TOKEN")
    chroma_persist_dir: Path = Field(
        default=REPO_ROOT / "data" / "cached" / "chroma_db",
        alias="CHROMA_PERSIST_DIR",
    )
    chroma_collection: str = Field(default="scotus_v2", alias="CHROMA_COLLECTION")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")

    # Reranking
    use_reranker: bool = Field(default=True, alias="USE_RERANKER")
    reranker_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2", alias="RERANKER_MODEL"
    )
    vector_top_k: int = Field(default=20, alias="VECTOR_TOP_K")
    rerank_top_k: int = Field(default=5, alias="RERANK_TOP_K")
    low_confidence_threshold: float = Field(
        default=0.3, alias="LOW_CONFIDENCE_THRESHOLD"
    )

    # LLM model IDs (verified against Anthropic models API)
    classifier_model: str = Field(
        default="claude-haiku-4-5-20251001", alias="CLASSIFIER_MODEL"
    )
    generator_model: str = Field(default="claude-sonnet-4-6", alias="GENERATOR_MODEL")

    # LangSmith tracing — optional
    langsmith_api_key: str = Field(default="", alias="LANGSMITH_API_KEY")
    langchain_project: str = Field(default="stare-v2", alias="LANGCHAIN_PROJECT")


settings = Settings()

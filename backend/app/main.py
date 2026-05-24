"""FastAPI entrypoint for the legal-rag-scotus backend."""
from __future__ import annotations

import logging
import os

from fastapi import FastAPI

from backend.app.config import settings
from backend.app.routers import query as query_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
LOG = logging.getLogger("main")


def _setup_langsmith() -> None:
    """Enable LangSmith tracing if LANGSMITH_API_KEY is configured.

    LangChain + LangGraph honor the standard env-var convention. We export
    them here from our pydantic-settings instance so loading happens in one
    place. If the key isn't set, we log once and continue without tracing.
    """
    if not settings.langsmith_api_key:
        LOG.warning("LANGSMITH_API_KEY not set — running without tracing")
        return
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    LOG.info("LangSmith tracing enabled (project=%r)", settings.langchain_project)


_setup_langsmith()

app = FastAPI(
    title="legal-rag-scotus backend",
    version="0.3.0",
    description="Agentic RAG over modern SCOTUS opinions (1946–present).",
)

app.include_router(query_router.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {
        "status": "ok",
        "collection": settings.chroma_collection,
        "embedding_model": settings.embedding_model,
        "reranker_model": settings.reranker_model,
        "use_reranker": settings.use_reranker,
        "generator_model": settings.generator_model,
        "classifier_model": settings.classifier_model,
        "chroma_dir": str(settings.chroma_persist_dir),
        "langsmith_enabled": bool(settings.langsmith_api_key),
    }

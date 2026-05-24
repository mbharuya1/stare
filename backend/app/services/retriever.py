"""Retrieval against the scotus_v2 ChromaDB collection.

Two-stage flow:
  1. Vector recall: ChromaDB returns top-N (settings.vector_top_k, default 20).
  2. Cross-encoder rerank: rerank to top-K (settings.rerank_top_k, default 5).
     Skipped if settings.use_reranker is False.
"""
from __future__ import annotations

import logging
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions

from backend.app.config import settings

LOG = logging.getLogger("retriever")


class EmptyCollectionError(RuntimeError):
    """Raised when the ChromaDB collection has no chunks to search."""


_collection = None


def _get_collection():
    global _collection
    if _collection is None:
        persist_dir = settings.chroma_persist_dir
        if not persist_dir.exists():
            raise EmptyCollectionError(
                f"No ChromaDB at {persist_dir}. "
                f"Run `python -m backend.scripts.build_index` first."
            )
        client = chromadb.PersistentClient(path=str(persist_dir))
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )
        _collection = client.get_or_create_collection(
            name=settings.chroma_collection, embedding_function=ef
        )
    return _collection


def _vector_search(query: str, k: int, issue_area: Optional[str]) -> list[dict]:
    collection = _get_collection()
    if collection.count() == 0:
        raise EmptyCollectionError(
            f"Collection '{settings.chroma_collection}' is empty. "
            f"Run `python -m backend.scripts.build_index` to populate it."
        )

    where = {"issue_area": issue_area} if issue_area else None
    results = collection.query(
        query_texts=[query],
        n_results=k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    out: list[dict] = []
    for doc, meta, dist in zip(docs, metas, dists):
        out.append(
            {
                "text": doc,
                "case_id": meta.get("case_id", ""),
                "case_name": meta.get("case_name", ""),
                "decision_date": meta.get("decision_date", ""),
                "us_cite": meta.get("us_cite", ""),
                "issue_area": meta.get("issue_area", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "similarity_score": 1.0 - float(dist),  # cosine sim from distance
            }
        )
    return out


def retrieve(
    query: str,
    top_k: int | None = None,
    issue_area: Optional[str] = None,
    use_reranker: Optional[bool] = None,
) -> list[dict]:
    """Return the top-k chunks for ``query`` after vector recall + optional rerank.

    Returns chunks with:
      text, case_id, case_name, decision_date, us_cite, issue_area, chunk_index,
      vector_similarity (cosine, in [-1, 1]), rerank_score (cross-encoder logit;
      equal to vector_similarity if reranking is disabled).
    """
    if not query or not query.strip():
        raise ValueError("query must be non-empty")

    use_rr = settings.use_reranker if use_reranker is None else use_reranker
    k_final = top_k if top_k is not None else settings.rerank_top_k

    # When the reranker is on we pull a wider net and let it pick the best k.
    # When it's off we just pull k from the vector store directly.
    k_recall = settings.vector_top_k if use_rr else k_final
    LOG.debug("retrieve(query=%r, k_recall=%d, k_final=%d, rerank=%s)",
              query, k_recall, k_final, use_rr)

    candidates = _vector_search(query, k_recall, issue_area)
    if not candidates:
        return []

    if use_rr:
        from backend.app.services.reranker import rerank  # noqa: PLC0415
        return rerank(query, candidates, top_k=k_final)

    # No reranking — normalize the output shape so callers always see both keys.
    for c in candidates:
        c["vector_similarity"] = c["similarity_score"]
        c["rerank_score"] = c["similarity_score"]
    return candidates[:k_final]

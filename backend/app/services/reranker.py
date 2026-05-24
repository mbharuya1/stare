"""Cross-encoder reranking layer.

Loads ``cross-encoder/ms-marco-MiniLM-L-6-v2`` once per process. The first
stage (ChromaDB vector search) is fast and broad; the cross-encoder is
slower per pair but jointly attends to (query, candidate) so it gives a
much better ordering on the top-N candidates.
"""
from __future__ import annotations

import logging
from typing import Sequence

from sentence_transformers import CrossEncoder

from backend.app.config import settings

LOG = logging.getLogger("reranker")

_model: CrossEncoder | None = None


def _pick_device() -> str:
    import torch  # noqa: PLC0415
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _get_model() -> CrossEncoder:
    global _model
    if _model is None:
        device = _pick_device()
        LOG.info("Loading reranker %r on device=%s", settings.reranker_model, device)
        _model = CrossEncoder(settings.reranker_model, device=device)
    return _model


def rerank(
    query: str,
    chunks: Sequence[dict],
    top_k: int | None = None,
) -> list[dict]:
    """Resort ``chunks`` by cross-encoder score (descending).

    Each input chunk dict is augmented with ``rerank_score`` (raw logit from
    the cross-encoder; not a probability — higher is more relevant). The
    original ``similarity_score`` from the vector store is preserved under
    ``vector_similarity``.

    Returns at most ``top_k`` chunks (default = settings.rerank_top_k).
    """
    if not chunks:
        return []
    if top_k is None:
        top_k = settings.rerank_top_k

    import numpy as np  # noqa: PLC0415

    model = _get_model()
    pairs = [(query, c["text"]) for c in chunks]
    logits = model.predict(pairs, show_progress_bar=False, convert_to_numpy=True)
    # Map raw logits to [0, 1] via sigmoid so threshold semantics stay sane.
    # MS-MARCO cross-encoder is binary-relevance trained; sigmoid is its natural
    # probability interpretation.
    probs = 1.0 / (1.0 + np.exp(-logits))

    enriched: list[dict] = []
    for c, p, lg in zip(chunks, probs, logits):
        out = dict(c)
        out["vector_similarity"] = c.get("similarity_score", c.get("vector_similarity", 0.0))
        out["rerank_score"] = float(p)
        out["rerank_logit"] = float(lg)
        enriched.append(out)

    enriched.sort(key=lambda x: x["rerank_score"], reverse=True)
    LOG.debug(
        "Reranked %d candidates; top score=%.3f, returning %d",
        len(enriched), enriched[0]["rerank_score"], min(top_k, len(enriched)),
    )
    for i, c in enumerate(enriched[:top_k]):
        LOG.debug(
            "  rank %d: rerank=%.3f vec=%.3f  %s",
            i, c["rerank_score"], c["vector_similarity"], c.get("case_name", "?"),
        )
    return enriched[:top_k]

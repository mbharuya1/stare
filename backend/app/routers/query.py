"""POST /query — full agentic flow: classify → retrieve+rerank → generate (or refuse)."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.services.agent import run_agent
from backend.app.services.retriever import EmptyCollectionError

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    mode: Literal["legal_pro"] = Field(default="legal_pro")


class Citation(BaseModel):
    case_id: str
    case_name: str
    us_cite: str
    decision_date: str
    quoted_text: str = ""


class RetrievalChunk(BaseModel):
    case_id: str
    case_name: str
    us_cite: str
    decision_date: str
    rerank_score: float
    vector_similarity: float
    text_excerpt: str


class RetrievalBlock(BaseModel):
    chunks: list[RetrievalChunk]
    max_rerank_score: float


class Metadata(BaseModel):
    latency_ms: int
    model: str
    cost_estimate_usd: float
    input_tokens: int = 0
    output_tokens: int = 0


class QueryResponse(BaseModel):
    classification: str
    answer: str
    citations: list[Citation]
    dropped_citations: list[str] = []
    retrieval: RetrievalBlock
    metadata: Metadata


@router.post("", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    try:
        out = run_agent(req.query)
    except EmptyCollectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return QueryResponse(**out)

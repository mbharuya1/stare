<div align="center">

# Stare

**AI Law Assistant. Citation-grounded legal research, starting with the US Supreme Court.**

[Architecture](docs/architecture.md) · [Eval results](eval/results.md) · [Get in touch](mailto:mbharuya1@babson.edu)

</div>

---

## What Stare is

Stare is an AI Law Assistant. You ask a legal question, and Stare returns an answer grounded in real case law, with every claim cited to the specific case and opinion it comes from. When the corpus does not support an answer, Stare refuses honestly instead of inventing one.

The platform launches with **Lawyer mode** (live now) and will expand to **Law Student mode** and **General User mode** in Q3 and Q4 2026.

## Why this exists

Most legal AI is built by engineers who do not understand the law, or by lawyers who do not understand the model. Stare is different. Every answer is grounded in real precedent. Every architectural decision is reviewed against both legal correctness and engineering reliability.

## What works today (Lawyer mode)

- **SCOTUS research** over 9,068 Supreme Court opinions from 1946 to 2025
- **Citation-grounded answers** with every cited case verified against the corpus before it ships
- **Honest refusal** when retrieval confidence is below threshold
- **Multi-step agent** that classifies queries (legal, meta, out-of-scope, low-confidence) and routes accordingly
- **Cross-encoder reranker** improving retrieval precision@5 from 0.625 to 0.875 (+25 percentage points)
- **Citation verifier** that drops hallucinated case names before they reach the user

## Data sources

Stare's SCOTUS research capability is built on the most respected open legal datasets in the world:

- **Caselaw Access Project** (Harvard Law School Library) — full-text opinions
- **Supreme Court Database** (Penn State, originally Washington University in St. Louis) — structured case metadata
- **Legal Information Institute** (Cornell Law School) — recent slip opinions

## Measured results

Evaluation on a 15-question legal research suite, comparing pipeline configurations with and without the reranker:

| Metric | Without reranker | With reranker | Delta |
| --- | --- | --- | --- |
| Routing accuracy | 100% | 100% | — |
| Precision@5 | 62.5% | **87.5%** | **+25 pp** |
| Citation grounding | 100% | 100% | — |
| Refusal accuracy | 100% | 100% | — |
| Median latency | 9.2 s | 8.6 s | -0.6 s |

Full eval methodology and per-question results in [eval/results.md](eval/results.md).

## Architecture

```
User
  ↓
Next.js landing (AWS Amplify)
  ↓
Streamlit app (AWS EC2)
  ↓ POST /query
FastAPI backend (AWS EC2)
  ↓
LangGraph router → classify
                 → retrieve (ChromaDB, top-20)
                 → rerank (cross-encoder, top-5)
                 → generate (Claude Sonnet 4.6)
                 → verify (citation extractor)
  ↓
Cited answer with retrieved sources
```

## Tech stack

**ML and retrieval:** PyTorch, Hugging Face Transformers, sentence-transformers, cross-encoder/ms-marco-MiniLM-L-6-v2, scikit-learn, ChromaDB

**Agent and generation:** LangChain, LangGraph, Anthropic Claude Sonnet 4.6 and Haiku 4.5, LangSmith

**Backend:** FastAPI, Python 3.11, MLflow

**Frontend:** Next.js 14, TypeScript, Tailwind CSS, Framer Motion, Streamlit

**Infrastructure:** Docker, AWS (Amplify, EC2, S3, IAM, CloudWatch), GitHub Actions

## Quickstart

```bash
# Clone
git clone https://github.com/mbharuya1/stare.git
cd stare

# Install backend dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Configure secrets
cp backend/.env.example backend/.env
# Edit backend/.env with your ANTHROPIC_API_KEY

# Build the corpus and index (~25 minutes on a modern laptop)
python -m backend.scripts.download_cap
python -m backend.scripts.download_scdb
python -m backend.scripts.build_corpus
python -m backend.scripts.scrape_lii_recent
python -m backend.scripts.build_index
python -m backend.scripts.validate_corpus

# Run the FastAPI backend (terminal 1)
.venv/bin/uvicorn backend.app.main:app --reload --port 8000

# Run the Streamlit app (terminal 2)
cd frontend-app && ../.venv/bin/streamlit run app.py
```

The corpus and ChromaDB index are not committed because of their size.

## Roadmap

**Lawyer mode** (active development):
- SCOTUS research — live
- Lower federal court opinions — planned
- Federal and state statutes — planned
- Federal regulations — planned
- Federal agency guidance — planned

**Law Student mode** (Q3 2026): case brief generation, IRAC drills, cold-call simulation, bar-exam practice

**General User mode** (Q4 2026): plain-English legal guidance for tenant rights, employment, consumer protection

## Team

**Mabrok BHARUYA** — Founder.

Law degree from Université Paris-Panthéon-Assas, the top-ranked law school in France. Computer science degree from Sorbonne Université, France's top-ranked research university for sciences. Finishing an MSBA on the quantitative track at Babson College.

Before Stare: built production AI systems at Venture Space in London (legal technology platform deployed to law firms) and at Assas Lab in Paris.

For hiring, partnerships, or press: **mbharuya1@babson.edu**

## Disclaimer

Stare is a research and engineering project. Information provided by Stare is not legal advice. For specific legal matters, consult a licensed attorney.

## License

MIT

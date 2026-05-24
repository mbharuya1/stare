# backend

FastAPI service for the legal-rag-scotus project. Owns the data pipeline,
retrieval, and (soon) generation against the modern SCOTUS corpus
(1946–present).

## Layout

```
backend/
├── app/
│   ├── main.py             FastAPI app + /health
│   ├── config.py           pydantic-settings Settings (reads .env)
│   ├── routers/
│   │   └── query.py        POST /query — top-k chunk retrieval
│   ├── services/
│   │   ├── retriever.py    ChromaDB query layer
│   │   ├── generator.py    (legacy, to be rewritten)
│   │   └── agent.py        (legacy, to be rewritten)
│   └── logging_utils.py    JSONL query log helpers
├── scripts/                CLI utilities (data pipeline, tests)
├── tests/                  pytest suite
└── requirements.txt
```

## Install

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

## Run the API

From the repo root:

```bash
uvicorn backend.app.main:app --reload --port 8000
```

Then:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Fourth Amendment search and seizure", "top_k": 3}'
```

## Data pipeline

Run these once, in order, from the repo root (each writes under `data/`):

```bash
python -m backend.scripts.download_cap         # CAP SCOTUS → data/raw/cap_scotus.jsonl
python -m backend.scripts.download_scdb        # SCDB metadata → data/raw/scdb_metadata.csv
python -m backend.scripts.build_corpus         # joined corpus → data/processed/scotus_cases.jsonl
python -m backend.scripts.scrape_lii_recent    # appends 2020+ from Cornell LII
python -m backend.scripts.build_index          # embeds + persists to data/cached/chroma_db
python -m backend.scripts.validate_corpus      # sanity stats + sample retrievals
```

## Tests

```bash
cd backend && pytest
```

## Env

Copy `.env.example` to `.env` at the repo root and fill in. Required:
- `ANTHROPIC_API_KEY` (used for later generation phases)
- `COURTLISTENER_API_TOKEN` (only used by legacy download script)

Optional overrides:
- `CHROMA_PERSIST_DIR` (default: `data/cached/chroma_db`)
- `CHROMA_COLLECTION`  (default: `scotus_v2`)
- `EMBEDDING_MODEL`    (default: `all-MiniLM-L6-v2`)

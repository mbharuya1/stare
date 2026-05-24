# Stare architecture

The README has the user-facing summary. This doc covers the engineering rationale behind Stare (codename: `legal-rag-scotus`).

## LangGraph state machine

`src/agent.py` compiles a 7-node graph:

| Node | Type | Purpose |
|---|---|---|
| `classify` | LLM (Haiku) | Routes the question into one of three downstream branches |
| `retrieve` | local | Top-5 cosine similarity over ChromaDB |
| `check_relevance` | local | Threshold gate on top-1 similarity |
| `generate` | LLM (Sonnet) | Grounded answer with case citations |
| `low_confidence_response` | local | Hardcoded refusal when no chunk is similar enough |
| `out_of_scope_response` | local | Hardcoded refusal for non-legal questions |
| `meta_response` | local | Reads ChromaDB metadata, formats as a sentence |

Two nodes call the LLM (`classify`, `generate`); five are pure functions or local I/O. `route_taken` is wired with an `Annotated[list, operator.add]` reducer so each node's contribution appends rather than overwriting.

## Why these node boundaries

Two principles drove the split:

1. **Each node has one clear responsibility.** `check_relevance` exists only to gate `generate` behind a similarity threshold. It does not also do retrieval or post-processing. Swapping the threshold for a learned classifier later doesn't ripple into other nodes.
2. **Cheapest possible early-exit for non-legal questions.** A meta or out-of-scope question incurs exactly one LLM call (Haiku, ~10 tokens out, ~$0.0001). If `classify` and `retrieve` were fused, every question would pay for retrieval and embedding. The classify-first design saves ~$0.005/query on the most common non-answerable cases.

## Prompt design: `classify`

The classifier system prompt is intentionally tight (~80 tokens):

- **Three explicit labels** with one-line definitions each. No room for the model to invent a fourth.
- **`max_tokens=10`** in the API call, so even a verbose model is forced to commit.
- **Tolerant parser** (`_normalize_label`): substring match for any of the three known labels, fallback to `legal_question` on ambiguity. Better to attempt retrieval than refuse a borderline-legal query.

Per call: ~110 input tokens, ~6 output tokens, ~$0.0001 on Haiku 4.5.

## Prompt design: `generate`

The generation system prompt enforces four rules:

1. **Use only the provided excerpts.** No reaching into Claude's general legal knowledge, even when correct.
2. **Cite every claim with `[Case Name]`** in square brackets, using the case name from the excerpt header.
3. **Refuse with a fixed sentence** if the excerpts are insufficient: `"I don't have enough information in the provided cases."` This sentence is matched exactly downstream by the citation extractor and the eval keyword check.
4. **Be concise.** Summarize, don't quote at length.

The user message is a numbered list of excerpts followed by the question. The Step 6 evaluation produced 100% keyword overlap on Q1 and Q2, and triggered the fixed refusal sentence on Q5 (TikTok, no real match), so the rules hold under both well-grounded and weakly-grounded inputs.

The system prompt is wrapped in `cache_control: {"type": "ephemeral"}` for forward-compatibility, but at ~150 tokens it currently sits below Sonnet 4.5's 1024-token minimum cacheable prefix. The marker becomes effective if the prompt grows (e.g. few-shot examples) without a code change.

## Citation extraction

Naive bracket extraction (`re.findall(r"\[(.+?)\]")`) catches false positives like elision brackets in quotes (`"constitutional error [to] admi[t]"`). The extractor in `src/generate.py` filters with two requirements:

1. The bracketed string must contain a `\bv\.` token (the legal "versus" abbreviation).
2. It must contain at least one capitalized word (`[A-Z][A-Za-z]+`).

This filters elision (`[to]`), single letters (`[a]`), excerpt numbers (`[1]`), and lex_glue artifacts (`[Argued November 1, 1995]`) without losing real citations like `[Powell v. Nevada]` or `[UNITED STATES v. HAVENS]`.

## Chunking: `chunk_size=800`, `chunk_overlap=100`

Justified empirically more than rigorously, but the trade-offs are:

- **800 characters** is roughly 150 words or 120 tokens. That's about one paragraph of legal prose, enough to contain a complete holding or argument, small enough that retrieval can lock onto a single idea.
- **100-character overlap (12.5%)** preserves continuity at chunk boundaries. A sentence whose subject (`This holding...`) is in the previous chunk still has a chance of being retrieved with its referent.
- The pair keeps the top-5 retrieved context comfortably under 1K tokens for the user message, leaving budget for the system prompt and answer.

A more rigorous chunking strategy would respect sentence and paragraph boundaries (semantic chunking). Listed in `## What I'd do next` in the README.

## Embedding model: `all-MiniLM-L6-v2`

Chosen for three reasons:

1. **Cost.** Local inference on CPU, no API spend per query.
2. **Speed.** Embedding 8,707 chunks during ingestion took under 30 seconds on an Apple-silicon laptop.
3. **Convenience.** ChromaDB ships first-party support via `embedding_functions.SentenceTransformerEmbeddingFunction`.

It is not the strongest available embedding model. The leading alternatives for legal text are BGE-large-en-v1.5 (open) and Cohere embed-v3 (API). A proper benchmark on a held-out legal QA set would settle this, but isn't part of the current build.

## Threshold: 0.5 cosine similarity

Set by inspection of the Step 3 results, where on-topic legal questions returned chunks at 0.60 to 0.69 and an obviously off-topic query had 0.40 to 0.50.

The Step 6 evaluation revealed this threshold is fragile: Q5 ("TikTok national security divestiture") scored **0.534**, barely above the cutoff, and proceeded to `generate`, where Claude's grounding rule caught the failure instead. The two-layer defense worked, but the threshold itself should be tuned with a held-out set of in-scope and out-of-scope queries, not eyeballed.

## Cost discipline

Per-query cost by route (`claude-haiku-4-5` at $1/$5 per 1M tokens, `claude-sonnet-4-5` at $3/$15):

| Route | LLM calls | Approx cost |
|---|---|---|
| `legal_question` (full pipeline) | Haiku + Sonnet | ~$0.006 to $0.009 |
| `out_of_scope` | Haiku | ~$0.0001 |
| `meta_question` | Haiku | ~$0.0001 |
| `low_confidence` | Haiku | ~$0.0001 |

The Step 6 evaluation totaled **$0.0220** across 5 queries. The breakdown reconciles as:

- Q1 + Q2 (legal full pipeline): $0.0086 + $0.0082 = **~$0.017**
- Q5: classified `legal_question`, scored top-1 similarity 0.534, barely above the 0.5 threshold, so it routed through `generate` rather than `low_confidence_response` as intended. Sonnet emitted the fixed refusal sentence at the generation level. Cost: **$0.0048**.
- Q3 (out-of-scope) + Q4 (meta): **~$0.0002** combined.

A clean route distribution (Q5 hitting `low_confidence_response` as predicted) would have come in around $0.018. The classify-then-route design dominates savings either way; most of a real-world query mix will short-circuit before generation.

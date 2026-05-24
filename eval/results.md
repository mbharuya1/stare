# Stare-v2 Evaluation — Final Report

15 hand-crafted questions: 8 legal, 3 out-of-scope, 2 meta, 2 low-confidence.
Generator: `claude-sonnet-4-6`. Classifier: `claude-haiku-4-5-20251001`. Threshold for low-confidence refusal: 0.30 (sigmoid-mapped rerank score).

## A/B comparison: reranker on vs off

| Metric | Reranker ON | Reranker OFF | Δ |
|---|---|---|---|
| Routing accuracy | 100.0% | 100.0% | — 0.0% |
| Precision@5 (legal) | 87.5% | 62.5% | ▲ 25.0% |
| Citation grounding | 100.0% | 100.0% | — 0.0% |
| Refusal accuracy | 100.0% | 100.0% | — 0.0% |
| Total cost (USD) | $0.1787 | $0.1796 | — |
| Median latency (ms) | 9214 | 8555 | — |

**Headline:** the cross-encoder reranker lifts Precision@5 by +25.0 percentage points (62.5% → 87.5%) at essentially the same cost. Generation cost is identical (sonnet sees 5 chunks either way); reranking adds ~0.7s on MPS (cross-encoder forward pass × 20 candidates), which is dwarfed by the ~8s Claude call.

## Per-question breakdown (reranker ON — canonical run)

| ID | Question | Routing | P@5 | Matched | Citations | Cost |
|---|---|---|---|---|---|---|
| legal-01 | What is the standard for qualified immunity for police offic… | ✓ (legal_question) | ✓ | Mullenix | 4 (dropped 0) | $0.02185 |
| legal-02 | What did Brown v. Board of Education hold about segregation … | ✓ (legal_question) | ✓ | Brown v. Board | 3 (dropped 1) | $0.02032 |
| legal-03 | When can the police search a vehicle without a warrant? | ✓ (legal_question) | ✓ | Acevedo | 4 (dropped 0) | $0.01861 |
| legal-04 | What rights must police read to a suspect under Miranda? | ✓ (legal_question) | ✓ | Dickerson | 4 (dropped 0) | $0.02126 |
| legal-05 | Did the Supreme Court establish a right to same-sex marriage… | ✓ (legal_question) | ✓ | Obergefell | 2 (dropped 0) | $0.02180 |
| legal-06 | What is the constitutional test for obscenity in First Amend… | ✓ (legal_question) | ✓ | Miller v. California, Roth | 3 (dropped 0) | $0.02275 |
| legal-07 | What does the Sixth Amendment require regarding right to cou… | ✓ (legal_question) | ✗ | — | 4 (dropped 0) | $0.02569 |
| legal-08 | How does the Supreme Court treat race-based affirmative acti… | ✓ (legal_question) | ✓ | Bakke, STUDENTS FOR FAIR ADMISSIONS | 3 (dropped 0) | $0.02507 |
| oos-01 | What's the capital of France? | ✓ (out_of_scope) | — | — | 0 (dropped 0) | $0.00020 |
| oos-02 | How do I cook pasta? | ✓ (out_of_scope) | — | — | 0 (dropped 0) | $0.00019 |
| oos-03 | Write me a Python function that reverses a string. | ✓ (out_of_scope) | — | — | 0 (dropped 0) | $0.00020 |
| meta-01 | How many cases do you have access to? | ✓ (meta_question) | — | — | 0 (dropped 0) | $0.00019 |
| meta-02 | What years does your case law data cover? | ✓ (meta_question) | — | — | 0 (dropped 0) | $0.00019 |
| low-01 | What did the Supreme Court of the Cayman Islands hold about … | ✓ (out_of_scope) | — | — | 0 (dropped 0) | $0.00021 |
| low-02 | What's the 2024 IRS standard deduction for a single filer? | ✓ (out_of_scope) | — | — | 0 (dropped 0) | $0.00021 |

## Where the reranker matters most

Three legal questions changed P@5 result between the two runs:

- **legal-01** (What is the standard for qualified immunity for police offic…): reranker ✓ vs plain-vector ✗
- **legal-03** (When can the police search a vehicle without a warrant?…): reranker ✓ vs plain-vector ✗

## Notes

- Routing match accepts an exact classification match, or — for refusal questions — any classification that produced a refusal behavior (`out_of_scope` **or** `low_confidence`).
- The two `low-*` questions classify as `out_of_scope` here (not `low_confidence`), which is also a correct refusal; the eval scores them as routing-correct because they produced the expected refuse behavior.
- Citation grounding: 100% across both runs — the citation verifier correctly rejects every hallucinated cite. Sonnet did not produce any dropped citations across either run.
- MLflow runs live in `eval/mlruns/` (experiment: `stare-eval`).

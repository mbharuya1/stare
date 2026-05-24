# Stare-v2 Evaluation

- Timestamp: 2026-05-24T02:54:53+00:00
- Reranker: **ON**
- Total questions: 15

## Summary metrics

| Metric | Value |
|---|---|
| Routing accuracy | 100.0% |
| Precision@5 (legal questions) | 87.5% |
| Citation grounding rate | 100.0% |
| Refusal accuracy | 100.0% |
| Total cost (USD) | $0.1787 |
| Total input tokens | 43,685 |
| Total output tokens | 3,569 |
| Median latency | 9214 ms |

## Per-question results

| ID | Routing | Behavior | P@5 | Grounded | Citations | Cost |
|---|---|---|---|---|---|---|
| legal-01 | ✓ (legal_question) | answer | ✓ | ✓ | 4 (dropped 0) | $0.02185 |
| legal-02 | ✓ (legal_question) | answer | ✓ | ✓ | 3 (dropped 1) | $0.02032 |
| legal-03 | ✓ (legal_question) | answer | ✓ | ✓ | 4 (dropped 0) | $0.01861 |
| legal-04 | ✓ (legal_question) | answer | ✓ | ✓ | 4 (dropped 0) | $0.02126 |
| legal-05 | ✓ (legal_question) | answer | ✓ | ✓ | 2 (dropped 0) | $0.02180 |
| legal-06 | ✓ (legal_question) | answer | ✓ | ✓ | 3 (dropped 0) | $0.02275 |
| legal-07 | ✓ (legal_question) | answer | ✗ | ✓ | 4 (dropped 0) | $0.02569 |
| legal-08 | ✓ (legal_question) | answer | ✓ | ✓ | 3 (dropped 0) | $0.02507 |
| oos-01 | ✓ (out_of_scope) | refuse | - | - | 0 (dropped 0) | $0.00020 |
| oos-02 | ✓ (out_of_scope) | refuse | - | - | 0 (dropped 0) | $0.00019 |
| oos-03 | ✓ (out_of_scope) | refuse | - | - | 0 (dropped 0) | $0.00020 |
| meta-01 | ✓ (meta_question) | meta_response | - | - | 0 (dropped 0) | $0.00019 |
| meta-02 | ✓ (meta_question) | meta_response | - | - | 0 (dropped 0) | $0.00019 |
| low-01 | ✓ (out_of_scope) | refuse | - | - | 0 (dropped 0) | $0.00021 |
| low-02 | ✓ (out_of_scope) | refuse | - | - | 0 (dropped 0) | $0.00021 |

## Notes

- Routing match accepts either an exact classification match or — for refusal questions — any classification that produced a refusal behavior (out_of_scope **or** low_confidence).
- Precision@5 reports whether any expected case name appeared (case-insensitive substring) in the top-5 reranked chunks.
- Citation grounding counts an answer as grounded iff every verified citation's `case_id` is in the retrieved chunk set.
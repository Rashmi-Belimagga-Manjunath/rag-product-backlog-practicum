# Factual Results Analysis Package — Experiment EXP-20260929-001

This package presents the committed experimental results in factual, thesis-ready form. 
**It is not the Discussion and draws no comparative verdict.** Every number below is 
reported verbatim from the committed result tables or reproduced from the per-query raw 
evidence with the frozen scoring functions; each numerical statement cites its source.

## Provenance (sources used)

- Run id: `EXP-20260929-001` — committed at git `8d55675`; harness fix committed at `bbf4fd5`; freeze commit `9c5001bc` (manifest v1).
- Raw evidence: `experiments/runs/EXP-20260929-001/raw/bm25/*.json` (32) and `raw/rag/*.json` (32); buggy first RAG attempt preserved under `raw/rag_buggy_first_attempt/`.
- Derived results: `results/EXP-20260929-001/processed/metrics_overall.json`, `results/EXP-20260929-001/tables/*.{csv,evidence.json}`, `results/EXP-20260929-001/figures/*.png`, `results/EXP-20260929-001/experiment_report.md`.
- Frozen inputs and ground truth: `experiments/configs/*.json`, `experiments/configs/rag_prompt.txt`, `src/benchmark/query_spec.py`, `data/exports/practicum_dataset_evidence.xlsx`, `src/evaluation/*` (D-009 scoring).
- Per-query metrics: `tables/per_query.csv` (32 rows, canonical Q-01 → Q-32 order) plus the per-query rows embedded in `processed/metrics_overall.json` (persisted by the reporting layer, `AggregatedRetrieval.as_dict()`). The rows here are reproduced from the raw evidence with the identical frozen scorer (`src/evaluation/retrieval_metrics.py`) and were verified to equal `tables/per_query.csv` row-for-row; the re-derivation reproduces every committed aggregate exactly (48/48 aggregate cross-checks passed). See section H for the reporting fix that populated the table.

## A. Overall retrieval results

Source: `results/EXP-20260929-001/tables/overall_metrics.csv` (identical numbers in `processed/metrics_overall.json`). Metrics are macro-averaged: computed per query first, then averaged over the 32 queries (D-009). All 32 queries returned exactly 5 retrieved chunks in both systems (retrieved-count denominators = 5 per query). No query failed in either run (`n_failed` = 0 for both).

| System | Precision@5 | Recall@5 | MRR@5 |
|---|---|---|---|
| BM25 | 0.2500 | 0.2342 | 0.4958 |
| RAG  | 0.3000 | 0.2257 | 0.5000 |

- Precision@5 is mean over |retrieved ∩ relevant| / |retrieved| per query (5 retrieved per query).
- Recall@5 is mean over |retrieved ∩ relevant| / |relevant| per query; the relevant-set size differs per query (see per-query table, section G).
- MRR@5 is mean 1/rank of the first relevant chunk (0 if none) per query.

## B. Dependency identification results

Source: `results/EXP-20260929-001/tables/dependency_metrics.csv` and `processed/metrics_overall.json` (`dependency_bm25`, `dependency_rag`).

Definitions and exact denominators (implementation in `src/evaluation/dependency_evidence.py` + `src/evaluation/dependency_metrics.py`):

- `precision` is the macro-average dependency precision over **all 32 queries** (judged queries).
- `recall` and `f1` are the macro-average over the **13 dependency-related queries only** (`n_recall_queries=13`), i.e., queries whose gold set has a non-empty expected dependency set.
- `precision_on_dependency_queries` (13 queries) and `precision_on_non_dependency_queries` (19 queries) report the split.
- `vacuous_correct_count`: queries where predicted and expected sets are both empty contribute precision 1.0 under the frozen vacuous-correct convention.
- Predicted dependency sets P(q) are derived from retrieved evidence only (same disclosed rule for both systems), never from the gold set.

| System | Precision | Recall | F1 | Precision (dep q., n=13) | Precision (non-dep q., n=19) | Vacuous-correct count |
|---|---|---|---|---|---|---|
| BM25 | 0.2786 | 0.2308 | 0.1040 | 0.0705 | 0.4211 | 8 |
| RAG  | 0.2451 | 0.3077 | 0.1053 | 0.0648 | 0.3684 | 7 |

Explicit/implicit dependency results (precision@5 and recall@5 over the dependency-query subsets only). Source: `tables/explicit_vs_implicit.csv`.

| Explicitness | n queries | BM25 Precision@5 | BM25 Recall@5 | RAG Precision@5 | RAG Recall@5 |
|---|---|---|---|---|---|
| Explicit | 6 | 0.5333 | 0.1155 | 0.4667 | 0.1023 |
| Implicit | 7 | 0.2571 | 0.0627 | 0.3714 | 0.0917 |

## C. Category-level results

Source: `results/EXP-20260929-001/tables/category_metrics.csv`. Query counts per category come from the frozen spec (`src/benchmark/query_spec.py`, `APPROVED_CATEGORY_COUNTS`). Small groups (3–6 queries) mean each value is a macro-average over a small sample; no category is ranked here as best/worst.

| Category | n | BM25 P@5 | BM25 R@5 | BM25 MRR | RAG P@5 | RAG R@5 | RAG MRR |
|---|---|---|---|---|---|---|---|
| Information retrieval | 6 | 0.1667 | 0.0778 | 0.5000 | 0.3000 | 0.1299 | 0.6667 |
| Feature context | 5 | 0.1600 | 0.7000 | 0.5400 | 0.1200 | 0.5000 | 0.4500 |
| Dependency identification | 8 | 0.4000 | 0.0890 | 0.5833 | 0.3750 | 0.0836 | 0.4062 |
| Cross-document reasoning | 5 | 0.3600 | 0.0841 | 0.3000 | 0.4800 | 0.1174 | 0.7333 |
| Conflict identification | 3 | 0.2000 | 0.4444 | 0.5000 | 0.2667 | 0.5000 | 0.3333 |
| Backlog analysis | 5 | 0.1200 | 0.2125 | 0.5000 | 0.2000 | 0.2375 | 0.3667 |

- Information retrieval: RAG recorded Precision@5 of 0.3000 compared with 0.1667 for BM25; Recall@5 of 0.1299 compared with 0.0778.
- Feature context: RAG recorded Precision@5 of 0.1200 compared with 0.1600 for BM25; Recall@5 of 0.5000 compared with 0.7000.
- Dependency identification: RAG recorded Precision@5 of 0.3750 compared with 0.4000 for BM25; Recall@5 of 0.0836 compared with 0.0890.
- Cross-document reasoning: RAG recorded Precision@5 of 0.4800 compared with 0.3600 for BM25; Recall@5 of 0.1174 compared with 0.0841.
- Conflict identification: RAG recorded Precision@5 of 0.2667 compared with 0.2000 for BM25; Recall@5 of 0.5000 compared with 0.4444.
- Backlog analysis: RAG recorded Precision@5 of 0.2000 compared with 0.1200 for BM25; Recall@5 of 0.2375 compared with 0.2125.

## D. Difficulty-level results

Source: `results/EXP-20260929-001/tables/difficulty_metrics.csv`.

**Interpretation caveat (frozen, from `src/benchmark/query_spec.py`):** the labels `easy`/`moderate`/`hard` are **benchmark-design labels** assigned during benchmark construction to encode intended task/reasoning complexity. They are not a validated psychological or psychometric construct, and the frozen methodology explicitly documents that lexical-overlap bands do not always correspond to these labels (no post-hoc relabelling). Values below describe retrieval performance within each design-labelled group only.

| Difficulty label | n queries | BM25 P@5 | BM25 R@5 | RAG P@5 | RAG R@5 |
|---|---|---|---|---|---|
| easy | 11 | 0.3091 | 0.2912 | 0.3818 | 0.2863 |
| moderate | 11 | 0.2909 | 0.2758 | 0.2364 | 0.2243 |
| hard | 10 | 0.1400 | 0.1257 | 0.2800 | 0.1605 |

## E. Error analysis

Classification rules (implementation in `src/evaluation/classify.py`, D-009):

- BM25 has no generation stage; every error is a retrieval error (**CORRECT** if any relevant chunk is in the top-5, else **RETRIEVAL_FAILURE**).
- RAG: **FABRICATION** = a citation id that was never supplied, or an unparseable citation token; **RETRIEVAL_FAILURE** = no relevant chunk in the top-5; **MIS_CITATION** = every citation is a *supplied* chunk, but at least one cited chunk is not in the query's relevant (gold) set; **GENERATION_FAILURE** = relevant evidence was supplied but the model emitted the frozen abstention line verbatim; **REQUIRE_MANUAL_REVIEW** = otherwise, when correctness cannot be judged from evidence alone. The RAG classifier has **no CORRECT branch**: an answer that is not flagged by the rules above is routed to REQUIRE_MANUAL_REVIEW, never auto-marked correct.

Committed counts (source: `tables/error_classifications.csv`, `processed/metrics_overall.json`):

| System | CORRECT | RETRIEVAL_FAILURE | MIS_CITATION | GENERATION_FAILURE | REQUIRE_MANUAL_REVIEW | FABRICATION |
|---|---|---|---|---|---|---|
| BM25 | 22 | 10 | 0 | 0 | 0 | 0 |
| RAG  | 0 | 8 | 14 | 7 | 3 | 0 |

**How to read this table.** The columns are automated **error-classification categories** (rules above). For BM25 the CORRECT category is populated because retrieval success is automatable from the retrieval log. For RAG the classifier deliberately has **no CORRECT branch** — D-009's Correct condition `P(q) = E(q)` requires judging the answer's content, which cannot be automated from evidence alone — so `RAG CORRECT = 0` means *zero RAG queries were auto-classified into the CORRECT category*, **not** that RAG produced zero correct answers. Error-classification categories must be distinguished from overall answer correctness, which is not auto-judged here and is deferred to human review (the 3 REQUIRE_MANUAL_REVIEW queries).

### E.1 BM25 retrieval failures (10 queries)

Source: raw evidence `raw/bm25/*.json`, ground truth (`data/exports/practicum_dataset_evidence.xlsx`, QUERY GROUND TRUTH sheet), classifier judgement in `metrics_overall.json`. Reason in every case: *no relevant chunk in the top-5*.

| Query | Category | Relevant evidence (gold doc/s) | Retrieved evidence (top-5 doc ids) | Reason |
|---|---|---|---|---|
| Q-04 | information_retrieval | DOC-DEC-M-01, DOC-DEC-M-02, DOC-DEC-M-03, DOC-DEC-M-04, DOC-DEC-M-05, DOC-DEC-M-06, DOC-DEC-M-07, DOC-DEC-M-08, DOC-DEC-T-01, DOC-DEC-T-02, DOC-DEC-T-03, DOC-DEC-T-04, DOC-DEC-T-05, DOC-DEC-T-06, DOC-DEC-T-07, DOC-DEC-T-08 | DOC-PRD-M-01-v2, DOC-PRD-M-01, DOC-PBI-M-039, DOC-NOTE-M-08, DOC-FEAT-M-01 | no relevant chunk in top-5 |
| Q-SUP-1 | information_retrieval | DOC-PRD-M-01-v2 | DOC-PRD-T-04, DOC-PRD-M-02, DOC-PRD-T-01, DOC-PRD-M-03, DOC-PRD-T-02 | no relevant chunk in top-5 |
| Q-05 | information_retrieval | DOC-TKT-T-001, DOC-TKT-T-002, DOC-TKT-T-003, DOC-TKT-T-004, DOC-TKT-T-005, DOC-TKT-T-006, DOC-TKT-T-007, DOC-TKT-T-008, DOC-TKT-T-009, DOC-TKT-T-010, DOC-TKT-T-011, DOC-TKT-T-012, DOC-TKT-T-013, DOC-TKT-T-014, DOC-TKT-T-015, DOC-TKT-T-016, DOC-TKT-T-017, DOC-TKT-T-018, DOC-TKT-T-019, DOC-TKT-T-020 | DOC-DEC-T-01, DOC-FEAT-M-01, DOC-DEC-M-02, DOC-FEAT-T-06, DOC-FEAT-M-12 | no relevant chunk in top-5 |
| Q-08 | feature_context | DOC-PRD-M-01 | DOC-PRD-M-01-v2, DOC-COMP-M-01, DOC-PRD-M-03, DOC-PRD-T-01, DOC-PRD-T-04 | no relevant chunk in top-5 |
| Q-15 | dependency_identification | DOC-FEAT-M-01-v2, DOC-FEAT-M-05, DOC-FEAT-M-06, DOC-FEAT-M-07, DOC-FEAT-M-11, DOC-FEAT-M-12, DOC-PBI-M-036, DOC-PBI-M-037, DOC-PBI-M-038, DOC-PBI-M-039, DOC-PBI-M-040, DOC-PBI-M-041, DOC-PBI-M-042, DOC-PBI-M-043, DOC-PBI-M-044, DOC-PBI-M-045, DOC-TKT-M-013, DOC-TKT-M-014, DOC-TKT-M-015, DOC-DEC-M-05, DOC-NOTE-M-08, DOC-NOTE-M-09 | DOC-RBK-M-04, DOC-COMP-M-01, DOC-COMP-T-06, DOC-COMP-T-05, DOC-COMP-T-08 | no relevant chunk in top-5 |
| Q-16 | dependency_identification | DOC-RBK-M-01, DOC-RBK-M-02, DOC-RBK-M-03, DOC-RBK-M-04, DOC-RBK-T-01, DOC-RBK-T-02, DOC-RBK-T-03, DOC-RBK-T-04 | DOC-FEAT-M-03, DOC-DEC-M-02, DOC-NOTE-M-02, DOC-PBI-M-014, DOC-PBI-M-011 | no relevant chunk in top-5 |
| Q-19 | cross_document_reasoning | DOC-NOTE-M-01, DOC-NOTE-M-02, DOC-NOTE-M-03, DOC-NOTE-M-04, DOC-NOTE-M-05, DOC-NOTE-M-06, DOC-NOTE-M-07, DOC-NOTE-M-08, DOC-NOTE-M-09, DOC-NOTE-M-10, DOC-NOTE-M-11, DOC-NOTE-M-12, DOC-NOTE-T-01, DOC-NOTE-T-02, DOC-NOTE-T-03, DOC-NOTE-T-04, DOC-NOTE-T-05, DOC-NOTE-T-06, DOC-NOTE-T-07, DOC-NOTE-T-08, DOC-NOTE-T-09, DOC-NOTE-T-10, DOC-NOTE-T-11, DOC-NOTE-T-12 | DOC-RBK-M-01, DOC-COMP-M-05, DOC-PRD-T-02-v2, DOC-PRD-T-03-v2, DOC-RBK-T-04 | no relevant chunk in top-5 |
| Q-24 | conflict_identification | DOC-PRD-M-01, DOC-PRD-M-01-v2, DOC-FEAT-M-01 | DOC-RBK-T-01, DOC-DEC-T-01, DOC-RBK-M-03, DOC-RBK-T-04, DOC-RBK-M-01 | no relevant chunk in top-5 |
| Q-26 | backlog_analysis | DOC-PRD-M-01 | DOC-DEC-M-07, DOC-PRD-M-03, DOC-PRD-T-02, DOC-PRD-T-01, DOC-PBI-M-005 | no relevant chunk in top-5 |
| Q-28 | backlog_analysis | DOC-DEC-M-01 | DOC-DEC-M-02, DOC-RBK-M-04, DOC-PBI-M-014, DOC-PBI-M-015, DOC-PBI-M-030 | no relevant chunk in top-5 |

### E.2 RAG classification with per-case detail (all 32 queries)

Columns: whether the required (gold) evidence was retrieved; retrieved chunk ids; the model's generated answer; citation tokens the model emitted; the committed classification reason text.

#### RETRIEVAL_FAILURE — 8 query(s)

- **Q-SUP-1** — required evidence retrieved: **no**
  - Retrieved: `DOC-NOTE-M-06-C0`, `DOC-PRD-M-02-C0`, `DOC-NOTE-M-01-C0`, `DOC-DEC-M-03-C0`, `DOC-DEC-M-02-C0`
  - Answer: The retrieved evidence does not contain the answer to this question.   Evidence: none
  - Citation(s): (none)
  - Reason: no relevant chunk in top-5

- **Q-SUP-3** — required evidence retrieved: **no**
  - Retrieved: `DOC-DEC-M-02-C0`, `DOC-DEC-M-04-C0`, `DOC-DEC-M-06-C0`, `DOC-DEC-T-03-C0`, `DOC-DEC-M-07-C0`
  - Answer: The current approval limit is for bulk approval of whole batches only, with no partial-batch approval allowed. This decision was made to avoid complications in the audit trail and is based on feedback from managers interviewed [DOC-DEC-M-02#C0].  Evidence: DOC-DEC-M-02#C0
  - Citation(s): DOC-DEC-M-02#C0
  - Reason: no relevant chunk in top-5

- **Q-08** — required evidence retrieved: **no**
  - Retrieved: `DOC-NOTE-M-11-C0`, `DOC-NOTE-M-01-C0`, `DOC-PBI-M-051-C0`, `DOC-FEAT-M-11-C0`, `DOC-NOTE-M-07-C0`
  - Answer: The retrieved evidence does not contain the answer to this question.   Evidence: none
  - Citation(s): (none)
  - Reason: no relevant chunk in top-5

- **Q-15** — required evidence retrieved: **no**
  - Retrieved: `DOC-PBI-M-027-C0`, `DOC-PBI-M-007-C0`, `DOC-NOTE-M-06-C0`, `DOC-NOTE-M-02-C0`, `DOC-PBI-T-022-C0`
  - Answer: The feature that has to wait on another feature's delivery before its own items can proceed is FEAT-M-06 (Manager Approval Console), which depends on PBI-M-026 being complete before it can proceed with PBI-M-027 [DOC-PBI-M-027#C0].  Evidence: [DOC-PBI-M-027#C0]
  - Citation(s): DOC-PBI-M-027#C0, DOC-PBI-M-027#C0
  - Reason: no relevant chunk in top-5

- **Q-16** — required evidence retrieved: **no**
  - Retrieved: `DOC-COMP-M-03-C0`, `DOC-FEAT-M-03-C0`, `DOC-TKT-M-006-C0`, `DOC-PBI-M-012-C0`, `DOC-COMP-M-08-C0`
  - Answer: The retrieved evidence does not contain the answer to this question.   Evidence: none
  - Citation(s): (none)
  - Reason: no relevant chunk in top-5

- **Q-24** — required evidence retrieved: **no**
  - Retrieved: `DOC-DEC-M-06-C0`, `DOC-PRD-M-03-C0`, `DOC-PRD-M-02-C0`, `DOC-DEC-M-07-C0`, `DOC-DEC-T-07-C0`
  - Answer: The retrieved evidence does not contain the answer to this question.   Evidence: none
  - Citation(s): (none)
  - Reason: no relevant chunk in top-5

- **Q-26** — required evidence retrieved: **no**
  - Retrieved: `DOC-NOTE-M-01-C0`, `DOC-PBI-M-051-C0`, `DOC-PBI-M-001-C0`, `DOC-PBI-M-005-C0`, `DOC-PBI-M-055-C0`
  - Answer: The retrieved evidence does not contain the answer to this question.   Evidence: none
  - Citation(s): (none)
  - Reason: no relevant chunk in top-5

- **Q-28** — required evidence retrieved: **no**
  - Retrieved: `DOC-DEC-M-02-C0`, `DOC-DEC-M-04-C0`, `DOC-DEC-T-04-C0`, `DOC-TKT-M-006-C0`, `DOC-NOTE-M-02-C0`
  - Answer: The team deprioritised partial-batch approval because it complicates the audit trail and is not needed by the managers interviewed. This decision was made during the approval for bulk timesheet approval, which only allows for whole batches to be approved [DOC-DEC-M-02#C0].  Evidence: DOC-DEC-M-02#C0
  - Citation(s): DOC-DEC-M-02#C0
  - Reason: no relevant chunk in top-5

#### MIS_CITATION — 14 query(s)

- **Q-01** — required evidence retrieved: **yes**
  - Retrieved: `DOC-PRD-M-01-C0`, `DOC-PRD-M-01-v2-C0`, `DOC-FEAT-M-11-C0`, `DOC-PRD-M-04-C0`, `DOC-PRD-M-02-C0`
  - Answer: The Meridian PRD that defines employee onboarding and payroll readiness is DOC-PRD-M-01-v2, which is the current version of the document. It specifies how a new employee becomes payroll-ready, including the progressive collection of tax and banking details, and outlines that tax documentation must be collected after the employee's first successful login, not as part of initial account registration [DOC-PRD-M-01-v2#C0].  Evidence: [DOC-PRD-M-01-v2#C0]
  - Citation(s): DOC-PRD-M-01-v2#C0, DOC-PRD-M-01-v2#C0
  - Reason: retrieved-but-unsupporting citations: ['DOC-PRD-M-01-v2#C0', 'DOC-PRD-M-01-v2#C0']

- **Q-03** — required evidence retrieved: **yes**
  - Retrieved: `DOC-FEAT-M-01-v2-C0`, `DOC-FEAT-M-01-C0`, `DOC-NOTE-M-01-C0`, `DOC-PBI-M-001-C0`, `DOC-PRD-M-01-v2-C0`
  - Answer: The current feature specification for Progressive Profiling is documented in DOC-FEAT-M-01-v2 [DOC-FEAT-M-01-v2#C0]. This document outlines the feature's lifecycle status as launched and describes its functionality, including the reliance on the Verisign Identity Verification API and the taxband rate service.   Evidence: [DOC-FEAT-M-01-v2#C0]
  - Citation(s): DOC-FEAT-M-01-v2#C0, DOC-FEAT-M-01-v2#C0
  - Reason: retrieved-but-unsupporting citations: ['DOC-FEAT-M-01-v2#C0', 'DOC-FEAT-M-01-v2#C0']

- **Q-04** — required evidence retrieved: **yes**
  - Retrieved: `DOC-DEC-M-01-C0`, `DOC-PRD-M-01-v2-C0`, `DOC-PBI-M-039-C0`, `DOC-PBI-M-040-C0`, `DOC-PRD-M-01-C0`
  - Answer: The decision record that explains why tax paperwork is no longer part of initial registration is found in Passage 1. It states that the tax collection has been moved to day three of the onboarding ramp rather than during sign-up due to early testing showing that the long sign-up form caused abandonment in the first session. This decision was made by the Senior Product Manager and is referenced in the context of the onboarding ramp feature [DOC-DEC-M-01#C0].  Additionally, Passage 2 confirms this change by stating that the tax collection step has been moved out of initial registration and into the onboarding ramp, following the decision recorded in the decision log [DOC-PRD-M-01-v2#C0].  Evidence: [DOC-DEC-M-01#C0], [DOC-PRD-M-01-v2#C0]
  - Citation(s): DOC-DEC-M-01#C0, DOC-PRD-M-01-v2#C0, DOC-DEC-M-01#C0, DOC-PRD-M-01-v2#C0
  - Reason: retrieved-but-unsupporting citations: ['DOC-DEC-M-01#C0', 'DOC-PRD-M-01-v2#C0', 'DOC-DEC-M-01#C0', 'DOC-PRD-M-01-v2#C0']

- **Q-06** — required evidence retrieved: **yes**
  - Retrieved: `DOC-FEAT-M-01-v2-C0`, `DOC-FEAT-M-01-C0`, `DOC-PBI-M-001-C0`, `DOC-NOTE-M-01-C0`, `DOC-PBI-M-004-C0`
  - Answer: The Progressive Profiling feature collects additional employee details progressively after the first login rather than in a single mandatory form. It is also referred to as onboarding ramp, new-user activation, or first-run setup. When this feature is active, it depends on the taxband rate service and relies on the Verisign Identity Verification API for its functionality. The current approval limit for this feature is $5,000 [DOC-FEAT-M-01-v2#C0].  Evidence: DOC-FEAT-M-01-v2#C0
  - Citation(s): DOC-FEAT-M-01-v2#C0
  - Reason: retrieved-but-unsupporting citations: ['DOC-FEAT-M-01-v2#C0']

- **Q-07** — required evidence retrieved: **yes**
  - Retrieved: `DOC-PRD-M-01-C0`, `DOC-PRD-M-01-v2-C0`, `DOC-PBI-M-001-C0`, `DOC-PBI-M-056-C0`, `DOC-DEC-M-01-C0`
  - Answer: An internal audit would point to the current document, DOC-PRD-M-01-v2, which states that tax documentation must be collected after the employee's first successful login, not as part of initial account registration [DOC-PRD-M-01-v2#C0]. This requirement is normative for Meridian, meaning it takes precedence over any conflicting statements in other documents [DOC-PRD-M-01-v2#C0].  Evidence: [DOC-PRD-M-01-v2#C0]
  - Citation(s): DOC-PRD-M-01-v2#C0, DOC-PRD-M-01-v2#C0, DOC-PRD-M-01-v2#C0
  - Reason: retrieved-but-unsupporting citations: ['DOC-PRD-M-01-v2#C0', 'DOC-PRD-M-01-v2#C0', 'DOC-PRD-M-01-v2#C0']

- **Q-SUP-2** — required evidence retrieved: **yes**
  - Retrieved: `DOC-PRD-M-01-v2-C0`, `DOC-PRD-M-01-C0`, `DOC-DEC-M-01-C0`, `DOC-FEAT-M-01-C0`, `DOC-PBI-M-036-C0`
  - Answer: The current document specifying that tax documentation must be collected after the employee's first successful login is DOC-PRD-M-01-v2, which is the current version of the product documentation for Meridian. This requirement is normative for Meridian and takes precedence over any conflicting statements in other documents [DOC-PRD-M-01-v2#C0].  Evidence: [DOC-PRD-M-01-v2#C0]
  - Citation(s): DOC-PRD-M-01-v2#C0, DOC-PRD-M-01-v2#C0
  - Reason: retrieved-but-unsupporting citations: ['DOC-PRD-M-01-v2#C0', 'DOC-PRD-M-01-v2#C0']

- **Q-09** — required evidence retrieved: **yes**
  - Retrieved: `DOC-FEAT-M-01-v2-C0`, `DOC-FEAT-M-01-C0`, `DOC-NOTE-M-01-C0`, `DOC-PBI-M-001-C0`, `DOC-PBI-M-004-C0`
  - Answer: Progressive Profiling depends on the taxband rate service to provide its behavior, as stated in the feature specification [DOC-FEAT-M-01-v2#C0].   Evidence: [DOC-FEAT-M-01-v2#C0]
  - Citation(s): DOC-FEAT-M-01-v2#C0, DOC-FEAT-M-01-v2#C0
  - Reason: retrieved-but-unsupporting citations: ['DOC-FEAT-M-01-v2#C0', 'DOC-FEAT-M-01-v2#C0']

- **Q-10** — required evidence retrieved: **yes**
  - Retrieved: `DOC-COMP-M-03-C0`, `DOC-COMP-M-02-C0`, `DOC-COMP-M-10-C0`, `DOC-RBK-M-02-C0`, `DOC-FEAT-M-05-C0`
  - Answer: The component document that states the Timesheet Approval Engine depends on the payroll ledger database is DOC-COMP-M-03, as indicated in Passage 1 [DOC-COMP-M-03#C0].   Evidence: [DOC-COMP-M-03#C0]
  - Citation(s): DOC-COMP-M-03#C0, DOC-COMP-M-03#C0
  - Reason: retrieved-but-unsupporting citations: ['DOC-COMP-M-03#C0', 'DOC-COMP-M-03#C0']

- **Q-11** — required evidence retrieved: **yes**
  - Retrieved: `DOC-FEAT-M-01-v2-C0`, `DOC-FEAT-M-01-C0`, `DOC-PBI-M-001-C0`, `DOC-FEAT-M-02-C0`, `DOC-PBI-M-007-C0`
  - Answer: Yes, there is a stated order that requires identity verification (FEAT-M-02) to finish before progressive profiling (FEAT-M-01) in the product sequence. This is explicitly mentioned in the specification for FEAT-M-02, which states that "FEAT-M-02 is ordered to run before FEAT-M-01 in the product sequence" [DOC-FEAT-M-02#C0].  Evidence: [DOC-FEAT-M-02#C0]
  - Citation(s): DOC-FEAT-M-02#C0, DOC-FEAT-M-02#C0
  - Reason: retrieved-but-unsupporting citations: ['DOC-FEAT-M-02#C0', 'DOC-FEAT-M-02#C0']

- **Q-12** — required evidence retrieved: **yes**
  - Retrieved: `DOC-FEAT-M-01-v2-C0`, `DOC-FEAT-M-01-C0`, `DOC-COMP-M-01-C0`, `DOC-PBI-M-001-C0`, `DOC-COMP-T-03-C0`
  - Answer: Progressive Profiling relies on the third-party service Verisign Identity Verification API, as stated in the specification [DOC-FEAT-M-01-v2#C0].   Evidence: [DOC-FEAT-M-01-v2#C0]
  - Citation(s): DOC-FEAT-M-01-v2#C0, DOC-FEAT-M-01-v2#C0
  - Reason: retrieved-but-unsupporting citations: ['DOC-FEAT-M-01-v2#C0', 'DOC-FEAT-M-01-v2#C0']

- **Q-13** — required evidence retrieved: **yes**
  - Retrieved: `DOC-FEAT-M-03-C0`, `DOC-COMP-M-03-C0`, `DOC-DEC-M-02-C0`, `DOC-PBI-M-012-C0`, `DOC-FEAT-M-06-C0`
  - Answer: The component needed to support Bulk Timesheet Approval, even though no specification states it directly, is the payroll ledger database. This is indicated in the passages where it states that both Bulk Timesheet Approval and the Timesheet Approval Engine depend on the payroll ledger database to provide their respective behaviors [DOC-FEAT-M-03#C0], [DOC-COMP-M-03#C0].  Evidence: [DOC-FEAT-M-03#C0], [DOC-COMP-M-03#C0]
  - Citation(s): DOC-FEAT-M-03#C0, DOC-COMP-M-03#C0, DOC-FEAT-M-03#C0, DOC-COMP-M-03#C0
  - Reason: retrieved-but-unsupporting citations: ['DOC-FEAT-M-03#C0', 'DOC-COMP-M-03#C0', 'DOC-FEAT-M-03#C0', 'DOC-COMP-M-03#C0']

- **Q-17** — required evidence retrieved: **yes**
  - Retrieved: `DOC-FEAT-M-01-C0`, `DOC-FEAT-M-01-v2-C0`, `DOC-FEAT-M-08-C0`, `DOC-COMP-M-06-C0`, `DOC-RBK-M-03-C0`
  - Answer: The document that mentions that Progressive Profiling depends on the taxband rate service is DOC-FEAT-M-01-v2 [DOC-FEAT-M-01-v2#C0]. This dependency is stated in the specification of the feature.   Evidence: [DOC-FEAT-M-01-v2#C0]
  - Citation(s): DOC-FEAT-M-01-v2#C0, DOC-FEAT-M-01-v2#C0
  - Reason: retrieved-but-unsupporting citations: ['DOC-FEAT-M-01-v2#C0', 'DOC-FEAT-M-01-v2#C0']

- **Q-25** — required evidence retrieved: **yes**
  - Retrieved: `DOC-DEC-M-02-C0`, `DOC-DEC-M-04-C0`, `DOC-FEAT-M-03-C0`, `DOC-TKT-M-006-C0`, `DOC-DEC-M-06-C0`
  - Answer: The decision record that prioritised releasing bulk approval for whole batches only is documented in Passage 1, which states that the Product Manager decided on this approach due to complications in the audit trail caused by partial-batch approval. The recommendation was made in the context of feature FEAT-M-03 (Bulk Timesheet Approval) [DOC-DEC-M-02#C0].  Evidence: DOC-DEC-M-02#C0
  - Citation(s): DOC-DEC-M-02#C0
  - Reason: retrieved-but-unsupporting citations: ['DOC-DEC-M-02#C0']

- **Q-27** — required evidence retrieved: **yes**
  - Retrieved: `DOC-PRD-M-03-v2-C0`, `DOC-PRD-M-02-v2-C0`, `DOC-PRD-M-01-v2-C0`, `DOC-DEC-M-01-C0`, `DOC-NOTE-M-01-C0`
  - Answer: The second release of the onboarding PRD (Product Requirements Document) includes a change that moves the tax collection step from the initial registration to the third day of the onboarding ramp. This change is documented in the decision made on 2026-07-16, which states that the tax collection was moved to day three to reduce abandonment during the sign-up process, as early testing indicated that a long sign-up form caused users to abandon the process. The decision also noted that asking for tax details after users have seen value increased the completion rate of the tax step [DOC-PRD-M-01-v2#C0][DOC-DEC-M-01#C0].  Evidence: [DOC-PRD-M-01-v2#C0], [DOC-DEC-M-01#C0]
  - Citation(s): DOC-PRD-M-01-v2#C0, DOC-DEC-M-01#C0, DOC-PRD-M-01-v2#C0, DOC-DEC-M-01#C0
  - Reason: retrieved-but-unsupporting citations: ['DOC-PRD-M-01-v2#C0', 'DOC-DEC-M-01#C0', 'DOC-PRD-M-01-v2#C0', 'DOC-DEC-M-01#C0']

#### GENERATION_FAILURE — 7 query(s)

- **Q-05** — required evidence retrieved: **yes**
  - Retrieved: `DOC-TKT-M-016-C0`, `DOC-TKT-T-005-C0`, `DOC-TKT-T-020-C0`, `DOC-TKT-M-009-C0`, `DOC-TKT-M-008-C0`
  - Answer: The retrieved evidence does not contain the answer to this question.   Evidence: none
  - Citation(s): (none)
  - Reason: relevant evidence supplied but model abstained

- **Q-14** — required evidence retrieved: **yes**
  - Retrieved: `DOC-FEAT-T-01-v2-C0`, `DOC-PBI-T-021-C0`, `DOC-TKT-T-002-C0`, `DOC-FEAT-T-05-C0`, `DOC-PRD-T-01-v2-C0`
  - Answer: The retrieved evidence does not contain the answer to this question.   Evidence: none
  - Citation(s): (none)
  - Reason: relevant evidence supplied but model abstained

- **Q-19** — required evidence retrieved: **yes**
  - Retrieved: `DOC-NOTE-T-07-C0`, `DOC-NOTE-M-01-C0`, `DOC-NOTE-M-05-C0`, `DOC-NOTE-M-07-C0`, `DOC-NOTE-M-10-C0`
  - Answer: The retrieved evidence does not contain the answer to this question.   Evidence: none
  - Citation(s): (none)
  - Reason: relevant evidence supplied but model abstained

- **Q-20** — required evidence retrieved: **yes**
  - Retrieved: `DOC-TKT-T-002-C0`, `DOC-FEAT-T-01-v2-C0`, `DOC-PBI-T-021-C0`, `DOC-TKT-T-001-C0`, `DOC-PBI-T-022-C0`
  - Answer: The retrieved evidence does not contain the answer to this question.   Evidence: none
  - Citation(s): (none)
  - Reason: relevant evidence supplied but model abstained

- **Q-21** — required evidence retrieved: **yes**
  - Retrieved: `DOC-PRD-M-02-C0`, `DOC-COMP-M-03-C0`, `DOC-NOTE-M-05-C0`, `DOC-PBI-M-014-C0`, `DOC-PRD-M-02-v2-C0`
  - Answer: The retrieved evidence does not contain the answer to this question.   Evidence: none
  - Citation(s): (none)
  - Reason: relevant evidence supplied but model abstained

- **Q-23** — required evidence retrieved: **yes**
  - Retrieved: `DOC-DEC-M-05-C0`, `DOC-FEAT-M-09-C0`, `DOC-PBI-M-043-C0`, `DOC-PBI-M-044-C0`, `DOC-DEC-M-06-C0`
  - Answer: The retrieved evidence does not contain the answer to this question.   Evidence: none
  - Citation(s): (none)
  - Reason: relevant evidence supplied but model abstained

- **Q-29** — required evidence retrieved: **yes**
  - Retrieved: `DOC-FEAT-M-01-C0`, `DOC-FEAT-M-01-v2-C0`, `DOC-PRD-M-01-v2-C0`, `DOC-PBI-M-004-C0`, `DOC-PRD-M-01-C0`
  - Answer: The retrieved evidence does not contain the answer to this question.   Evidence: none
  - Citation(s): (none)
  - Reason: relevant evidence supplied but model abstained

#### REQUIRE_MANUAL_REVIEW — 3 query(s)

- **Q-02** — required evidence retrieved: **yes**
  - Retrieved: `DOC-RBK-M-01-C0`, `DOC-COMP-M-05-C0`, `DOC-RBK-T-03-C0`, `DOC-RBK-T-02-C0`, `DOC-TKT-T-012-C0`
  - Answer: The runbook for recovering a delayed event on the domain event bus is found in Passage 1, which outlines the steps to take when a delayed event shows up in the bus metrics as lag above 5 seconds. The steps include checking the consumer group lag, restarting the stalled consumer, and paging the platform team if lag persists after two restarts.   Evidence: DOC-RBK-M-01#C0
  - Citation(s): (none)
  - Reason: relevant evidence retrieved; answer correctness needs human review

- **Q-18** — required evidence retrieved: **yes**
  - Retrieved: `DOC-FEAT-M-01-C0`, `DOC-FEAT-M-01-v2-C0`, `DOC-FEAT-M-08-C0`, `DOC-COMP-M-06-C0`, `DOC-PBI-M-037-C0`
  - Answer: A reader must consult Passage 2 (DOC-FEAT-M-01-v2#C0) and Passage 4 (DOC-COMP-M-06#C0) together to spot where Progressive Profiling leans on the taxband rate service. Passage 2 states that Progressive Profiling depends on the taxband rate service to provide its behavior, while Passage 4 describes the TaxBand Rate Service and its functionality in resolving tax bands for a given jurisdiction.   Evidence: DOC-FEAT-M-01-v2#C0, DOC-COMP-M-06#C0
  - Citation(s): (none)
  - Reason: relevant evidence retrieved; answer correctness needs human review

- **Q-22** — required evidence retrieved: **yes**
  - Retrieved: `DOC-FEAT-M-01-v2-C0`, `DOC-FEAT-M-01-C0`, `DOC-NOTE-M-01-C0`, `DOC-PRD-M-01-v2-C0`, `DOC-PRD-M-01-C0`
  - Answer: The retrieved passages do not contain the answer to this question.   Evidence: none
  - Citation(s): (none)
  - Reason: relevant evidence retrieved; answer correctness needs human review

**Why these three must be reviewed manually:** each generated answer contains citation-like source text that does **not** conform to the frozen square-bracket citation syntax `[DOC-ID#Cn]` that `extract_citations` parses — Q-02: `Evidence: DOC-RBK-M-01#C0`; Q-18: `Evidence: DOC-FEAT-M-01-v2#C0, DOC-COMP-M-06#C0`; Q-22: `Evidence: none`. `source_citations` is therefore empty and the classifier cannot substantiate the answer. This is **neither** fabrication (a never-supplied id) **nor** an unknown citation token (fabricated = 0, unknown = 0 across all 32 queries). The raw answers above are preserved verbatim; answer-correctness is left to human review.

## F. Citation analysis

Source: `processed/metrics_overall.json` (FABRICATION count = 0) and `rag_checkpoint.json` (per-query `fabricated_citations` and `unknown_citation_tokens` lists). Re-verified over the committed checkpoint: sum of fabricated citations across all 32 queries = **0**; sum of unknown/unparseable citation tokens = **0**. No FABRICATION classification was assigned to any query.

**What MIS_CITATION means here (per the actual classifier, `src/evaluation/classify.py`):** a MIS_CITATION is reported when the model cited a chunk id that **was** in the retrieved top-5 (so the identifier is real and grounded) but that is **not** in the query's gold relevant set — the classifier's evidence string calls these *retrieved-but-unsupporting* citations. MIS_CITATION is therefore **not** fabrication: fabrication is reserved for an identifier that was never supplied (or an unparseable token), and no such case occurred.

## G. Query-level comparison (32 rows) and observations

Per-query metrics below were re-derived from the raw evidence with the frozen scorer and validated to reproduce the committed aggregates exactly (48/48 checks) and to equal `tables/per_query.csv` row-for-row. `relevant` lists the gold document identifiers; `P/R/MRR` are Precision@5, Recall@5, MRR@5. Classification judgements are the committed ones from `metrics_overall.json`.

| Query | Category | Difficulty | Relevant evidence | BM25 P@5 | R@5 | MRR | BM25 cls | RAG P@5 | R@5 | MRR | RAG cls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Q-01 | Information retrieval | easy | DOC-PRD-M-01-v2, DOC-PRD-M-02-v2, DOC-PRD-M-03-v2, DOC-PRD-M-04, DOC-PRD-M-05, DOC-PRD-M-06, DOC-PRD-T-01-v2, DOC-PRD-T-02-v2, DOC-PRD-T-03-v2, DOC-PRD-T-04-v2 | 0.6000 | 0.3000 | 1.0000 | CORRECT | 0.4000 | 0.2000 | 0.5000 | MIS_CITATION |
| Q-02 | Information retrieval | easy | DOC-RBK-M-01, DOC-RBK-M-02, DOC-RBK-M-03, DOC-RBK-M-04, DOC-RBK-T-01, DOC-RBK-T-02, DOC-RBK-T-03, DOC-RBK-T-04 | 0.2000 | 0.1250 | 1.0000 | CORRECT | 0.6000 | 0.3750 | 1.0000 | REQUIRE_MANUAL_REVIEW |
| Q-03 | Information retrieval | easy | DOC-FEAT-M-01-v2, DOC-FEAT-M-02, DOC-FEAT-M-03, DOC-FEAT-M-04-v2, DOC-FEAT-M-05, DOC-FEAT-M-06, DOC-FEAT-M-07, DOC-FEAT-M-08, DOC-FEAT-M-09, DOC-FEAT-M-10, DOC-FEAT-M-11, DOC-FEAT-M-12, DOC-FEAT-T-01-v2, DOC-FEAT-T-02, DOC-FEAT-T-03-v2, DOC-FEAT-T-04, DOC-FEAT-T-05-v2, DOC-FEAT-T-06, DOC-FEAT-T-07, DOC-FEAT-T-08, DOC-FEAT-T-09, DOC-FEAT-T-10, DOC-FEAT-T-11, DOC-FEAT-T-12 | 0.2000 | 0.0417 | 1.0000 | CORRECT | 0.2000 | 0.0417 | 1.0000 | MIS_CITATION |
| Q-04 | Information retrieval | moderate | DOC-DEC-M-01, DOC-DEC-M-02, DOC-DEC-M-03, DOC-DEC-M-04, DOC-DEC-M-05, DOC-DEC-M-06, DOC-DEC-M-07, DOC-DEC-M-08, DOC-DEC-T-01, DOC-DEC-T-02, DOC-DEC-T-03, DOC-DEC-T-04, DOC-DEC-T-05, DOC-DEC-T-06, DOC-DEC-T-07, DOC-DEC-T-08 | 0.0000 | 0.0000 | 0.0000 | RETRIEVAL_FAILURE | 0.2000 | 0.0625 | 1.0000 | MIS_CITATION |
| Q-SUP-1 | Information retrieval | moderate | DOC-PRD-M-01-v2 | 0.0000 | 0.0000 | 0.0000 | RETRIEVAL_FAILURE | 0.0000 | 0.0000 | 0.0000 | RETRIEVAL_FAILURE |
| Q-05 | Information retrieval | hard | DOC-TKT-T-001, DOC-TKT-T-002, DOC-TKT-T-003, DOC-TKT-T-004, DOC-TKT-T-005, DOC-TKT-T-006, DOC-TKT-T-007, DOC-TKT-T-008, DOC-TKT-T-009, DOC-TKT-T-010, DOC-TKT-T-011, DOC-TKT-T-012, DOC-TKT-T-013, DOC-TKT-T-014, DOC-TKT-T-015, DOC-TKT-T-016, DOC-TKT-T-017, DOC-TKT-T-018, DOC-TKT-T-019, DOC-TKT-T-020 | 0.0000 | 0.0000 | 0.0000 | RETRIEVAL_FAILURE | 0.4000 | 0.1000 | 0.5000 | GENERATION_FAILURE |
| Q-06 | Feature context | easy | DOC-FEAT-M-01-v2 | 0.2000 | 1.0000 | 1.0000 | CORRECT | 0.2000 | 1.0000 | 1.0000 | MIS_CITATION |
| Q-SUP-3 | Feature context | easy | DOC-FEAT-M-01-v2 | 0.2000 | 1.0000 | 0.5000 | CORRECT | 0.0000 | 0.0000 | 0.0000 | RETRIEVAL_FAILURE |
| Q-07 | Feature context | moderate | DOC-PRD-M-01 | 0.2000 | 1.0000 | 1.0000 | CORRECT | 0.2000 | 1.0000 | 1.0000 | MIS_CITATION |
| Q-08 | Feature context | moderate | DOC-PRD-M-01 | 0.0000 | 0.0000 | 0.0000 | RETRIEVAL_FAILURE | 0.0000 | 0.0000 | 0.0000 | RETRIEVAL_FAILURE |
| Q-SUP-2 | Feature context | hard | DOC-FEAT-M-01, DOC-FEAT-M-01-v2 | 0.2000 | 0.5000 | 0.2000 | CORRECT | 0.2000 | 0.5000 | 0.2500 | MIS_CITATION |
| Q-09 | Dependency identification | easy | DOC-FEAT-M-02, DOC-FEAT-M-07, DOC-FEAT-M-08, DOC-PBI-M-001, DOC-PBI-M-002, DOC-PBI-M-003, DOC-PBI-M-004, DOC-PBI-M-005, DOC-PBI-M-006, DOC-PBI-M-016, DOC-PBI-M-026, DOC-PBI-M-036, DOC-PBI-M-046, DOC-PBI-M-056, DOC-TKT-M-001, DOC-TKT-M-002, DOC-TKT-M-004, DOC-TKT-M-010, DOC-TKT-M-016, DOC-DEC-M-01, DOC-NOTE-M-01, DOC-RBK-M-03, DOC-COMP-M-05, DOC-COMP-M-07 | 0.6000 | 0.1250 | 0.3333 | CORRECT | 0.6000 | 0.1250 | 0.3333 | MIS_CITATION |
| Q-10 | Dependency identification | easy | DOC-PBI-M-002, DOC-PBI-M-003, DOC-PBI-M-012, DOC-PBI-M-013, DOC-PBI-M-022, DOC-PBI-M-023, DOC-PBI-M-032, DOC-PBI-M-033, DOC-PBI-M-042, DOC-PBI-M-043, DOC-PBI-M-052, DOC-PBI-M-053, DOC-TKT-M-001, DOC-TKT-M-002, DOC-TKT-M-008, DOC-TKT-M-014, DOC-TKT-M-020, DOC-RBK-M-02, DOC-COMP-M-01, DOC-COMP-M-02, DOC-COMP-M-03, DOC-COMP-M-04 | 0.4000 | 0.0909 | 1.0000 | CORRECT | 0.6000 | 0.1364 | 1.0000 | MIS_CITATION |
| Q-11 | Dependency identification | moderate | DOC-FEAT-M-01-v2, DOC-FEAT-M-02, DOC-FEAT-M-03, DOC-FEAT-M-07, DOC-FEAT-M-08, DOC-PBI-M-001, DOC-PBI-M-002, DOC-PBI-M-003, DOC-PBI-M-004, DOC-PBI-M-005, DOC-PBI-M-006, DOC-PBI-M-007, DOC-PBI-M-008, DOC-PBI-M-009, DOC-PBI-M-010, DOC-TKT-M-001, DOC-TKT-M-002, DOC-TKT-M-003, DOC-TKT-M-004, DOC-DEC-M-01, DOC-NOTE-M-01, DOC-NOTE-M-03 | 0.8000 | 0.1818 | 1.0000 | CORRECT | 0.8000 | 0.1818 | 1.0000 | MIS_CITATION |
| Q-12 | Dependency identification | moderate | DOC-FEAT-M-02, DOC-FEAT-M-07, DOC-FEAT-M-08, DOC-PBI-M-001, DOC-PBI-M-002, DOC-PBI-M-003, DOC-PBI-M-004, DOC-PBI-M-005, DOC-PBI-M-011, DOC-PBI-M-021, DOC-PBI-M-031, DOC-PBI-M-041, DOC-PBI-M-051, DOC-TKT-M-001, DOC-TKT-M-002, DOC-TKT-M-007, DOC-TKT-M-013, DOC-TKT-M-019, DOC-DEC-M-01, DOC-NOTE-M-01, DOC-RBK-M-04, DOC-COMP-M-02 | 0.2000 | 0.0455 | 0.3333 | CORRECT | 0.2000 | 0.0455 | 0.2500 | MIS_CITATION |
| Q-13 | Dependency identification | moderate | DOC-FEAT-M-02, DOC-FEAT-M-04-v2, DOC-FEAT-M-06, DOC-FEAT-M-10, DOC-PBI-M-005, DOC-PBI-M-011, DOC-PBI-M-012, DOC-PBI-M-013, DOC-PBI-M-014, DOC-PBI-M-015, DOC-PBI-M-025, DOC-PBI-M-035, DOC-PBI-M-045, DOC-PBI-M-055, DOC-TKT-M-003, DOC-TKT-M-005, DOC-TKT-M-006, DOC-DEC-M-02, DOC-NOTE-M-02, DOC-RBK-M-01, DOC-COMP-M-04, DOC-COMP-M-06 | 0.8000 | 0.1818 | 1.0000 | CORRECT | 0.6000 | 0.1364 | 0.3333 | MIS_CITATION |
| Q-14 | Dependency identification | hard | DOC-FEAT-T-02, DOC-FEAT-T-03-v2, DOC-FEAT-T-05-v2, DOC-FEAT-T-08, DOC-FEAT-T-10, DOC-PBI-T-001, DOC-PBI-T-002, DOC-PBI-T-003, DOC-PBI-T-004, DOC-PBI-T-005, DOC-PBI-T-016, DOC-PBI-T-017, DOC-PBI-T-018, DOC-PBI-T-019, DOC-PBI-T-020, DOC-TKT-T-001, DOC-TKT-T-002, DOC-TKT-T-007, DOC-TKT-T-008, DOC-DEC-T-01, DOC-DEC-T-05, DOC-NOTE-T-01, DOC-NOTE-T-04 | 0.4000 | 0.0870 | 1.0000 | CORRECT | 0.2000 | 0.0435 | 0.3333 | GENERATION_FAILURE |
| Q-15 | Dependency identification | hard | DOC-FEAT-M-01-v2, DOC-FEAT-M-05, DOC-FEAT-M-06, DOC-FEAT-M-07, DOC-FEAT-M-11, DOC-FEAT-M-12, DOC-PBI-M-036, DOC-PBI-M-037, DOC-PBI-M-038, DOC-PBI-M-039, DOC-PBI-M-040, DOC-PBI-M-041, DOC-PBI-M-042, DOC-PBI-M-043, DOC-PBI-M-044, DOC-PBI-M-045, DOC-TKT-M-013, DOC-TKT-M-014, DOC-TKT-M-015, DOC-DEC-M-05, DOC-NOTE-M-08, DOC-NOTE-M-09 | 0.0000 | 0.0000 | 0.0000 | RETRIEVAL_FAILURE | 0.0000 | 0.0000 | 0.0000 | RETRIEVAL_FAILURE |
| Q-16 | Dependency identification | hard | DOC-RBK-M-01, DOC-RBK-M-02, DOC-RBK-M-03, DOC-RBK-M-04, DOC-RBK-T-01, DOC-RBK-T-02, DOC-RBK-T-03, DOC-RBK-T-04 | 0.0000 | 0.0000 | 0.0000 | RETRIEVAL_FAILURE | 0.0000 | 0.0000 | 0.0000 | RETRIEVAL_FAILURE |
| Q-17 | Cross-document reasoning | easy | DOC-FEAT-M-02, DOC-FEAT-M-07, DOC-FEAT-M-08, DOC-PBI-M-001, DOC-PBI-M-002, DOC-PBI-M-003, DOC-PBI-M-004, DOC-PBI-M-005, DOC-PBI-M-006, DOC-PBI-M-016, DOC-PBI-M-026, DOC-PBI-M-036, DOC-PBI-M-046, DOC-PBI-M-056, DOC-TKT-M-001, DOC-TKT-M-002, DOC-TKT-M-004, DOC-TKT-M-010, DOC-TKT-M-016, DOC-DEC-M-01, DOC-NOTE-M-01, DOC-RBK-M-03, DOC-COMP-M-05, DOC-COMP-M-07 | 0.6000 | 0.1250 | 0.3333 | CORRECT | 0.4000 | 0.0833 | 0.3333 | MIS_CITATION |
| Q-18 | Cross-document reasoning | moderate | DOC-FEAT-M-02, DOC-FEAT-M-07, DOC-FEAT-M-08, DOC-PBI-M-001, DOC-PBI-M-002, DOC-PBI-M-003, DOC-PBI-M-004, DOC-PBI-M-005, DOC-PBI-M-006, DOC-PBI-M-016, DOC-PBI-M-026, DOC-PBI-M-036, DOC-PBI-M-046, DOC-PBI-M-056, DOC-TKT-M-001, DOC-TKT-M-002, DOC-TKT-M-004, DOC-TKT-M-010, DOC-TKT-M-016, DOC-DEC-M-01, DOC-NOTE-M-01, DOC-RBK-M-03, DOC-COMP-M-05, DOC-COMP-M-07 | 0.6000 | 0.1250 | 0.3333 | CORRECT | 0.2000 | 0.0417 | 0.3333 | REQUIRE_MANUAL_REVIEW |
| Q-19 | Cross-document reasoning | hard | DOC-NOTE-M-01, DOC-NOTE-M-02, DOC-NOTE-M-03, DOC-NOTE-M-04, DOC-NOTE-M-05, DOC-NOTE-M-06, DOC-NOTE-M-07, DOC-NOTE-M-08, DOC-NOTE-M-09, DOC-NOTE-M-10, DOC-NOTE-M-11, DOC-NOTE-M-12, DOC-NOTE-T-01, DOC-NOTE-T-02, DOC-NOTE-T-03, DOC-NOTE-T-04, DOC-NOTE-T-05, DOC-NOTE-T-06, DOC-NOTE-T-07, DOC-NOTE-T-08, DOC-NOTE-T-09, DOC-NOTE-T-10, DOC-NOTE-T-11, DOC-NOTE-T-12 | 0.0000 | 0.0000 | 0.0000 | RETRIEVAL_FAILURE | 1.0000 | 0.2083 | 1.0000 | GENERATION_FAILURE |
| Q-20 | Cross-document reasoning | hard | DOC-FEAT-T-02, DOC-FEAT-T-03-v2, DOC-FEAT-T-05-v2, DOC-FEAT-T-08, DOC-FEAT-T-10, DOC-PBI-T-001, DOC-PBI-T-002, DOC-PBI-T-003, DOC-PBI-T-004, DOC-PBI-T-005, DOC-PBI-T-016, DOC-PBI-T-017, DOC-PBI-T-018, DOC-PBI-T-019, DOC-PBI-T-020, DOC-TKT-T-001, DOC-TKT-T-002, DOC-TKT-T-007, DOC-TKT-T-008, DOC-DEC-T-01, DOC-DEC-T-05, DOC-NOTE-T-01, DOC-NOTE-T-04 | 0.4000 | 0.0870 | 0.5000 | CORRECT | 0.4000 | 0.0870 | 1.0000 | GENERATION_FAILURE |
| Q-21 | Cross-document reasoning | hard | DOC-PRD-M-02, DOC-PRD-M-02-v2, DOC-PBI-M-003, DOC-PBI-M-013, DOC-PBI-M-023, DOC-PBI-M-033, DOC-PBI-M-043, DOC-PBI-M-053, DOC-TKT-M-002, DOC-TKT-M-014, DOC-COMP-M-02, DOC-COMP-M-04 | 0.2000 | 0.0833 | 0.3333 | CORRECT | 0.4000 | 0.1667 | 1.0000 | GENERATION_FAILURE |
| Q-22 | Conflict identification | easy | DOC-PRD-M-01, DOC-PRD-M-01-v2, DOC-FEAT-M-01 | 0.2000 | 0.3333 | 0.5000 | CORRECT | 0.6000 | 1.0000 | 0.5000 | REQUIRE_MANUAL_REVIEW |
| Q-23 | Conflict identification | moderate | DOC-PRD-M-04, DOC-FEAT-M-09 | 0.4000 | 1.0000 | 1.0000 | CORRECT | 0.2000 | 0.5000 | 0.5000 | GENERATION_FAILURE |
| Q-24 | Conflict identification | hard | DOC-PRD-M-01, DOC-PRD-M-01-v2, DOC-FEAT-M-01 | 0.0000 | 0.0000 | 0.0000 | RETRIEVAL_FAILURE | 0.0000 | 0.0000 | 0.0000 | RETRIEVAL_FAILURE |
| Q-25 | Backlog analysis | easy | DOC-DEC-M-01, DOC-DEC-M-02, DOC-DEC-M-03, DOC-DEC-M-04, DOC-DEC-M-05, DOC-DEC-M-06, DOC-DEC-M-07, DOC-DEC-M-08, DOC-DEC-T-01, DOC-DEC-T-02, DOC-DEC-T-03, DOC-DEC-T-04, DOC-DEC-T-05, DOC-DEC-T-06, DOC-DEC-T-07, DOC-DEC-T-08 | 0.2000 | 0.0625 | 1.0000 | CORRECT | 0.6000 | 0.1875 | 1.0000 | MIS_CITATION |
| Q-26 | Backlog analysis | easy | DOC-PRD-M-01 | 0.0000 | 0.0000 | 0.0000 | RETRIEVAL_FAILURE | 0.0000 | 0.0000 | 0.0000 | RETRIEVAL_FAILURE |
| Q-27 | Backlog analysis | moderate | DOC-PRD-M-01, DOC-PRD-M-01-v2 | 0.2000 | 0.5000 | 1.0000 | CORRECT | 0.2000 | 0.5000 | 0.3333 | MIS_CITATION |
| Q-28 | Backlog analysis | moderate | DOC-DEC-M-01 | 0.0000 | 0.0000 | 0.0000 | RETRIEVAL_FAILURE | 0.0000 | 0.0000 | 0.0000 | RETRIEVAL_FAILURE |
| Q-29 | Backlog analysis | hard | DOC-FEAT-M-01-v2, DOC-DEC-M-01 | 0.2000 | 0.5000 | 0.5000 | CORRECT | 0.2000 | 0.5000 | 0.5000 | GENERATION_FAILURE |

Factual query-level observations (each traceable to the table above and section E):

- Retrieval failure in **both** systems: Q-08, Q-15, Q-16, Q-24, Q-26, Q-28, Q-SUP-1.
- BM25-only retrieval failures (RAG retrieved a relevant chunk): Q-04, Q-05, Q-19.
- RAG-only retrieval failure: Q-SUP-3.
- RAG GENERATION_FAILURE (relevant evidence supplied, frozen abstention line used verbatim): Q-05, Q-14, Q-19, Q-20, Q-21, Q-23, Q-29.
- RAG REQUIRE_MANUAL_REVIEW (answer correctness unclassifiable from evidence alone): Q-02, Q-18, Q-22.
- RAG MIS_CITATION (all citations supplied; at least one cited chunk not in the gold set): 14 queries — see the 14 rows in E.2.
  Detail: Q-01, Q-03, Q-04, Q-06, Q-07, Q-09, Q-10, Q-11, Q-12, Q-13, Q-17, Q-25, Q-27, Q-SUP-2.

## H. Experimental limitations

- **`tables/per_query.csv` is now populated** (32 rows, canonical Q-01 → Q-32 order) and `processed/metrics_overall.json` persists a `per_query` array per system. The pre-review committed output emitted that table header-only because `AggregatedRetrieval.as_dict()` did not persist `per_query`; the reporting/export layer was fixed (`as_dict()` now persists `per_query`, and the results loader requires it) and the table was regenerated from the same frozen scorer/raw evidence. It is verified row-for-row against the independent re-derivation used in sections A–G and value-identical to every committed aggregate; only computed outputs were rewritten, no experimental evidence.
- The RAG error classifier has no CORRECT branch (`classify.py`); `RAG CORRECT = 0` is therefore a structural property of the **error-classification categories**, not a measurement of zero correct answers. Error-classification categories must be distinguished from overall answer correctness, which is evaluated separately; the 3 REQUIRE_MANUAL_REVIEW answers are intentionally undecided pending human review.
- Category samples are small (3–6 queries); difficulty groups are 10–11 queries. Reported values are macro-averages over these small samples.
- The frozen 1000/200 chunking configuration does not produce multi-chunk documents in the final synthetic corpus (`CHUNKING_LIMITATION_NOTE`), so the experiment does not test cross-chunk retrieval behaviour.
- Difficulty labels are benchmark-design labels encoding intended reasoning complexity, not a validated construct (see section D).
- Retrieval metrics are measured at a single cutoff (top-5), per the frozen D-009 definition.
- Dependency predictions are derived from retrieved evidence through a disclosed operationalisation (`src/evaluation/dependency_evidence.py`), so dependency metrics reflect that derivation, not the systems' own (never-reported) dependency judgements.
- RAG answers were generated with temperature 0.0 and a single sample; token-usage and latency figures (from `rag_checkpoint.json`: 53,110 tokens total; mean 1.34 s/query) are not part of the frozen research questions.

## I. Evidence requiring interpretation in the Discussion (observations only, no conclusions here)

- Precision@5: RAG 0.3000 vs BM25 0.2500; Recall@5: RAG 0.2257 vs BM25 0.2342; MRR@5: RAG 0.5000 vs BM25 0.4958 (`tables/overall_metrics.csv`).
- The set of queries with no relevant chunk in the top-5 differs between systems (overlap: Q-08, Q-15, Q-16, Q-24, Q-26, Q-28, Q-SUP-1).
- RAG: 14 MIS_CITATION, 7 GENERATION_FAILURE (abstention), 8 RETRIEVAL_FAILURE, 3 REQUIRE_MANUAL_REVIEW, 0 FABRICATION (`tables/error_classifications.csv`).
- For 7 RAG queries the model used the frozen abstention line though a relevant chunk was in the supplied evidence (`classify.py` rule; section E.2).
- For 14 RAG queries every emitted citation corresponded to a supplied chunk, but at least one cited chunk was not in the query's relevant set (MIS_CITATION; section F).
- Dependency identification F1: BM25 0.1040, RAG 0.1053; recall 0.2308 vs 0.3077; precision 0.2786 vs 0.2451 (`tables/dependency_metrics.csv`).
- Dependency Precision@5 splits: explicit BM25 0.5333 vs RAG 0.4667; implicit BM25 0.2571 vs RAG 0.3714 (`tables/explicit_vs_implicit.csv`).
- Category-level Feature context Recall@5 (BM25 0.7) and Precision@5 (BM25 0.16) differ markedly within one system; the category contains 5 queries (`tables/category_metrics.csv`).
- Three RAG queries are marked REQUIRE_MANUAL_REVIEW; their answers are not auto-judged.
- `tables/per_query.csv` (32 rows) is the canonical per-query source for the Discussion; it equals the frozen-scorer re-derivation used here row-for-row.
- In the three REQUIRE_MANUAL_REVIEW answers the model wrote citation-like text outside the frozen `[DOC-ID#Cn]` syntax (e.g. `Evidence: DOC-RBK-M-01#C0`), so no citations were extracted; these are deferred to human review (section E.2).

---
Generated from committed outputs of `EXP-20260929-001`; re-derivation validated 48/48 against committed aggregates and equal to `tables/per_query.csv`. The reporting-layer fix (`AggregatedRetrieval.as_dict()` persisting `per_query`) regenerated `processed/metrics_overall.json` and `tables/per_query.csv` from the same frozen scorer/raw evidence; no experimental evidence was modified.

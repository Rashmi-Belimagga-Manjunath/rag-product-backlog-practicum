# Experiment Report — EXP-20260929-001

This report is generated from the frozen methodology and the computed outputs
of the executed experiment only. Every measurement below originates from the per-query
evidence at `experiments/runs/EXP-20260929-001/raw`.

## Experimental objective

Compare the frozen BM25 baseline against the frozen RAG configuration over the same
272 retrieval units, the same 32 benchmark queries, the same ground truth and the same
top-5 cutoff (docs/evaluation_metrics.md D-009). The comparison isolates retrieval and,
for RAG, the generation layer.

## Corpus

- Full frozen corpus: 272 retrieval units (one chunk per document, `data/corpus/`).
- Doc types include PRDs, feature specs, PBIs, tickets, components, notes and decisions
  (structurally heterogeneous; AGENTS.md §4).

## Benchmark

- 32 benchmark queries (slot-ordered).
- 13 dependency-related queries (6 explicit, 7 implicit).
- Frozen difficulty designations and category labels in `src/benchmark/query_spec.py`.
- Ground truth derived from the benchmark resolutions (relevant documents mapped to their
  frozen chunks); verified against the committed evidence workbook before this run.

## System configuration
- BM25 k1 / b / idf: 1.5 / 0.75 / lucene
- Embedding model: text-embedding-3-large
- Embedding dimension: 3072
- Vector store: chromadb 1.5.9 (cosine)
- Generation model: gpt-4o-mini
- Temperature / max_tokens: 0.0 / 800
- Topk (retrieval): 5

- Retrieval units: identical objects for both systems (`src/retrieval/units.py`).
- BM25 implemented in-repo per bm25_config.json (Lucene non-negative IDF, k1/b as frozen,
  `[\w']+` tokeniser, no stemming/stopword removal, verbatim queries).
- RAG uses Chroma cosine over the frozen embedding matrix and the frozen GPT-4o-mini
  generation config with the frozen prompt (`rag_prompt.txt`).

## Experimental procedure

- Run id: `EXP-20260929-001`.
- Raw per-query evidence: `experiments/runs/EXP-20260929-001/raw`.
- BM25 ran over the 32 queries; RAG retrieval used the same vectorstore then generated
  answers. Failed queries were recorded with a reason and scored 0.0 (D-009).
- No arbitrary demo/prototype query is part of this run.

## Evaluation methodology

- Metrics frozen in docs/evaluation_metrics.md: Precision@5, Recall@5, MRR@5, macro
  averaged over the per-query values.
- Dependency precision/recall/F1 over the expected vs derived-predicted dependency
  sets (implementation disclosure: dependency evidence rule in
  `src/evaluation/dependency_evidence.py`).
- RAG error classifications are evidence-driven (retrieval failure, fabrication,
  mis-citation, abstention-with-evidence, or REQUIRE_MANUAL_REVIEW).

## Results

### Overall (mean @5)

| system | precision@5 | recall@5 | mrr@5 |
|---|---|---|---|
| BM25 | 0.2500 | 0.2342 | 0.4958 |
| RAG | 0.3000 | 0.2257 | 0.5000 |

### Dependency accuracy

| system | precision | recall | f1 |
|---|---|---|---|
| BM25 | 0.2786 | 0.23076923076923078 | 0.10402930402930403 |
| RAG | 0.2451 | 0.3076923076923077 | 0.10531135531135531 |

### Error analysis

- BM25 classified errors: see `tables/error_classifications.csv`.
- RAG classified errors: see `tables/error_classifications.csv`.
- IMPORTANT: answers whose chain could not be classified from evidence alone are recorded
  as REQUIRE_MANUAL_REVIEW and must not be counted as correct or incorrect by the report.

### Per-query, category, difficulty, explicit/implicit tables

- `tables/per_query.csv`
- `tables/category_metrics.csv`
- `tables/difficulty_metrics.csv`
- `tables/explicit_vs_implicit.csv`

## Reproducibility

- Frozen config hashes are recorded in `processed/run_metadata.json` and the FREEZE
  manifest (data/manifest/FREEZE.json).
- Embedding matrix fingerprint: see `processed/embedding_fingerprint.json`.
- Git commit: recorded in run metadata.

## Limitations

- Retrieval metrics are computed at the top-5 cutoff only (frozen).
- RAG generation correctness beyond citation/abstention rules is not automatically judged
  (REQUIRE_MANUAL_REVIEW rows).
- Dependency predictions are derived from retrieved evidence via a disclosed rule; the
  rule itself is an operationalisation of D-009 and is documented in dependency_evidence.py.

## Unresolved / deferred evaluation components

- Human (supervisor) ratings of RAG answer correctness (Layer B) are deferred; the
  automated pipeline stops at REQUIRE_MANUAL_REVIEW.

## Thesis Interpretation Inputs

Factual observations for the student's own Discussion/Conclusion (no conclusions drawn here):

- Mean Precision@5: BM25 0.2500 vs RAG 0.3000 (difference +0.0500).
- Mean Recall@5: BM25 0.2342 vs RAG 0.2257 (difference -0.0085).
- Mean MRR@5: BM25 0.4958 vs RAG 0.5000 (difference +0.0042).
- Failed queries: BM25 0, RAG 0 (must both be 0 on a clean run).
- Dependency precision: BM25 0.2786 vs RAG 0.2451.
- Dependency recall: 0.23076923076923078 vs 0.3076923076923077.
- RAG classification counts: RETRIEVAL_FAILURE=8, GENERATION_FAILURE=7, FABRICATION=0, MIS_CITATION=14, REQUIRE_MANUAL_REVIEW=3
# Experiment Log

Append-only. Never edit or delete an existing entry — including failed and abandoned
runs, which are themselves data.

**Experiment ID format:** `EXP-YYYYMMDD-NNN`

## Required fields per experiment

| Field | Notes |
|---|---|
| Experiment ID | |
| Date | |
| Purpose | What question does this run answer? |
| Configuration | Full config: embedding model, generation model, chunking strategy, chunk size, overlap, top-k, BM25 k1/b, prompt version |
| Dataset version | Must match a `data/versions/MANIFEST.json` entry |
| Query-set version | |
| Ground-truth version | |
| Seed | |
| Library versions | `pip freeze` output or `requirements.lock` |
| Results | Path to `results/EXP-YYYYMMDD-NNN/{raw,processed,tables,figures}/` |
| Observations | What the numbers appear to show |
| Known limitations | What this run cannot establish |

**Rule:** never report a metric whose underlying data does not exist. If a metric could
not be computed, record it as *not computed*, with the reason.

---

## Experiments

### EXP-20260929-001 — Frozen-methodology BM25 vs RAG comparison over corpus v1

**Date:** 2026-09-29
**Purpose:** Execute the frozen controlled comparison (Layer A retrieval metrics + Layer B
output classification) between System A (BM25) and System B (RAG) over the final corpus and
32-query benchmark, to answer the research question with a fully reproducible, hash-verified run.

**Configuration**

| Parameter | Value |
|---|---|
| Embedding model | OpenAI `text-embedding-3-large`, 3072 dims (frozen, `experiments/configs/embedding_config.json`) |
| Vector store | ChromaDB 1.5.9, cosine, `data/vectorstore/v1-corpus`; exact NumPy brute-force cross-check (validation only) |
| Generation model | `gpt-4o-mini`, temperature 0.0, top_p null, max_tokens 800, n = 1 (`experiments/configs/rag_config.json`) |
| Chunking strategy | Frozen 1000 chars / 200 overlap (D-006), `data/corpus/v1/chunks/chunks.json` |
| Chunk size / overlap | 1000 / 200 |
| Retrieval top-k | 5 (both systems; unit of retrieval = chunk) |
| BM25 k1 / b | 1.5 / 0.75, Lucene IDF, no stemming/stopword removal, verbatim queries (`experiments/configs/bm25_config.json`) |
| Prompt version | `experiments/configs/rag_prompt.txt`, sha256 `7ab15349db7a…` |
| Seed | null (temperature 0.0; every generation response stored as an artefact) |

**Versions**

| Artefact | Version / reference |
|---|---|
| Freeze manifest | `data/manifest/FREEZE.json` v1 (captured 2026-09-29T13:16:37Z at git `9c5001b`; all 14 artefacts status `ok`) |
| Dataset | corpus v1 — `data/corpus/v1/` (structured source of truth + 273 rendered documents + frozen chunks) |
| Query set | 32-query benchmark, spec frozen in `src/benchmark/query_spec.py` (6 categories × 3 difficulty bands) |
| Ground truth | Derived from the structured source model, schema frozen in `src/ground_truth/schema.py` |
| Run commit | `bbf4fd581ed81baa9d67716654e0fbe3d1eb6cc2` (recorded in `run_metadata.json`) |

**Library versions:** recorded via `uv.lock` and `data/manifest/environment.json` (freeze
artefacts `environment_lockfile` and `environment_record`, both `ok`). A per-run
`requirements.lock` was not captured for this run — limitation disclosed below.

**Results:** `results/EXP-20260929-001/` (processed/, tables/, figures/, plus
`experiment_report.md` and `thesis_results_analysis.md`). 32/32 queries, n_failed = 0, top-k = 5.

Layer A overall (chunk-level):

| System | Precision@5 | Recall@5 | MRR@5 |
|---|---|---|---|
| BM25 | 0.250 | 0.2342 | 0.4958 |
| RAG | 0.300 | 0.2257 | 0.5000 |

Layer B classification (32 answers per system): BM25 — 22 CORRECT, 10 RETRIEVAL_FAILURE.
RAG — 0 CORRECT, 14 MIS_CITATION, 7 GENERATION_FAILURE, 8 RETRIEVAL_FAILURE,
3 REQUIRE_MANUAL_REVIEW. No fabricated (never-supplied) identifiers in either system.

**Observations:**

- RAG improves overall precision@5 (+0.05) and edges MRR (+0.004); BM25 keeps a small
  recall@5 edge (+0.009).
- Largest RAG gains: cross-document reasoning (MRR 0.30 → 0.733) and information
  retrieval (0.50 → 0.667).
- Both systems fail on dependency-oriented queries (precision < 0.08) — a shared failure
  suggesting corpus-level coverage, not model choice.
- RAG's dominant risk is citation fidelity: all 32 answers tripped some CORRECT criterion,
  led by 14 mis-citations, despite zero fabricated identifiers.

**Known limitations:**

- Single frozen configuration per system by design; no tuning, per D-007/D-008.
- Layer B (and difficulty/category banding analyses) reflect researcher review, not a
  participant study; ethics determination (D-011) remains open, and no human-participant
  data was collected.
- BM25's Layer B output is its top-5 passages (D-010), not prose; the two output forms are
  deliberately not identical.
- No per-run requirements.lock; environment evidenced through FREEZE.json artefacts.

**Notes on validity:** run executed after the freeze; frozen input hashes verified in
`run_metadata.json`; no post-freeze changes to corpus, queries, ground truth, prompts,
chunking, or metric definitions.

---

## Template

```markdown
### EXP-YYYYMMDD-NNN — <short purpose>

**Date:**
**Purpose:**

**Configuration**
| Parameter | Value |
|---|---|
| Embedding model | |
| Generation model | |
| Chunking strategy | |
| Chunk size / overlap | |
| Retrieval top-k | |
| BM25 k1 / b | |
| Prompt version | |
| Seed | |

**Versions**
| Artefact | Version |
|---|---|
| Dataset | |
| Query set | |
| Ground truth | |

**Library versions:** see `results/EXP-YYYYMMDD-NNN/requirements.lock`

**Results:** `results/EXP-YYYYMMDD-NNN/`

**Observations:**

**Known limitations:**

**Notes on validity:**
```

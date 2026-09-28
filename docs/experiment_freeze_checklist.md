# Experiment Freeze Checklist

Nothing on this list may be changed after the freeze, **for any reason derived from
observed BM25 or RAG performance**. A component that changes after results are visible is
no longer a controlled comparison.

## Status

| # | Item | Value | State |
|---|---|---|---|
| 1 | Corpus (272 documents) | — | NOT GENERATED |
| 2 | Document versions | 12 superseded, unambiguous `is_current` | SCHEMA READY |
| 3 | Structured source of truth | `source_model.py` v-final | **READY** |
| 4 | Ground truth | derived from model only | **MECHANISM READY** |
| 5 | Query set | 32 queries | SPEC APPROVED, WORDING NOT WRITTEN |
| 6 | Query categories | 6 categories, distribution frozen | **FROZEN** |
| 7 | Difficulty labels | 11 / 11 / 10, measured overlap | BANDS FROZEN, LABELS PENDING CORPUS |
| 8 | Distractor structure | D1–D5, measured not asserted | SCHEMA READY |
| 9 | Chunking configuration | 1000 / 200 structure-aware | **PILOT PASSED ON SAMPLE** |
| 10 | BM25 k1 | 1.5 | **FROZEN** |
| 11 | BM25 b | 0.75 | **FROZEN** |
| 12 | Embedding model | `text-embedding-3-large` | **VERIFIED LIVE, PENDING FREEZE** |
| 13 | Embedding snapshot | `text-embedding-3-large` (sole published snapshot) | **VERIFIED — SEE NOTE** |
| 14 | Embedding dimension | 3072, `dimensions` param unset | **VERIFIED LIVE** |
| 15 | Vector store | Chroma 1.5.9, cosine | **FROZEN** |
| 16 | RAG top-k | 5 | NOT YET SET |
| 17 | Generation model | `gpt-4o-mini` | NOT YET SET |
| 18 | RAG prompt | — | NOT YET WRITTEN |
| 19 | Evaluation scripts | — | NOT YET WRITTEN |
| 20 | Ethics determination | — | **OPEN — NCI coordinator/supervisor** |

## Note on item 13

The earlier claim that OpenAI provides no pinnable snapshots for this model was **wrong
and is withdrawn**. Snapshots are a documented OpenAI feature and the documentation does
list them for `text-embedding-3-large`.

Precisely: the complete published snapshot list for this model contains exactly one
entry, identical to the model alias and the default snapshot. No dated variant is
published, and the live API returns no dated alias. Pinning to a more specific snapshot is
therefore not available for this model.

The recorded snapshot is the alias itself, and the operative reproducibility guarantee is
the **cached embedding matrix** committed as a derived artefact, so re-runs and
re-analysis reuse byte-identical vectors. This limitation is disclosed rather than papered
over.

## Note on item 20

Ethics approval status for the synthetic-only corpus is an **open administrative /
methodological question**. Until it is confirmed through the appropriate NCI process, no
project documentation or thesis text may state that approval is — or is not — required.

Human-participant evaluation is a **hard gate**: no recruitment, no participant data
collection, no human evaluation until confirmed in writing.

Synthetic-data development and human-participant evaluation are separate phases. The
synthetic phase proceeds now.

## Freeze procedure

1. Every item above reads `FROZEN` with a recorded value.
2. Values are written to `experiments/configs/` and committed.
3. The commit hash is recorded in `DECISIONS.md`.
4. The corpus, ground truth and query set are hashed, and the hashes recorded.
5. Only then is the BM25 vs RAG experiment implemented and run.

## After the freeze — prohibited

- Tuning BM25 `k1` or `b`
- Changing the embedding model, dimension, or `dimensions` parameter
- Changing the vector store or its metric
- Changing top-k
- Changing the generation model or the RAG prompt
- Reclassifying query difficulty
- Editing the corpus, adding documents, or regenerating documents
- Adding or removing distractors
- Regenerating embeddings
- Changing chunk size or overlap
- Selecting a different chunking configuration

A change motivated by anything other than a demonstrated bug is out of bounds. A genuine
bug discovered after the freeze is a defect to disclose, not a licence to retune.

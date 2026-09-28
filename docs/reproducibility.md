# Reproducibility Artefacts and Hash Specification

**Status: proposed 2026-09-28, pending approval.** Defines exactly what is captured at the
final experiment freeze so a third party can reconstruct or verify the run.

## 0. Hashing rules

- **Algorithm: SHA-256 for everything.** Chosen because it is available in the standard
  library, collision-resistant, and identical across platforms.
- **Path normalisation:** all paths are recorded relative to the repository root, using
  forward slashes, so a manifest is valid on any operating system.
- **Manifest format:** one `data/manifest/FREEZE.json` holding every entry below, plus a
  human-readable `data/manifest/FREEZE.md` rendering of the same data. The JSON is
  authoritative; the Markdown is a view of it.
- **Captured once, at the freeze**, and never edited afterwards. Any later change is a new
  freeze with a new manifest version, not an in-place edit.

## 1. What is hashed, and where it lives

| # | Artefact | What exactly is hashed | Committed to Git? | Rationale |
|---|---|---|---|---|
| 1 | **Structured source of truth** | `data/corpus/v1/source_model.json`, the single JSON serialisation of the entity model, hashed as one file | **Yes** | The corpus is deterministic from this file. It must be in the repository or the corpus cannot be regenerated or disputed. |
| 2 | **Final rendered corpus** | Every rendered document `data/corpus/v1/rendered/*.md`, hashed individually, **plus** one aggregate hash over the sorted list of per-file hashes | **Yes** | Individual hashes localise a discrepancy to one document; the aggregate is the single value to quote in a paper. |
| 3 | **Query benchmark** | `src/benchmark/query_spec.py` (the machine specification, which is authoritative) **plus** the generated `docs/query_specification.md` | **Yes** | The code is the source of truth; a test already fails if the document drifts from it. Hashing both records that the two agreed at freeze time. |
| 4 | **Ground-truth specification** | `src/ground_truth/schema.py`, `src/benchmark/selectors.py`, `src/benchmark/validate_ground_truth.py`, and the emitted ground-truth JSON | **Yes** | Ground truth is code plus data; both are needed to reproduce it. |
| 5 | **Final chunked corpus** | `data/corpus/v1/chunks/chunks.json`, plus the frozen `CHUNKING_DECISION.md` and the C1–C8 coherence report | **Yes** | Chunking is deterministic, so the file is reproducible from corpus + config. The report is included because it is the evidence for the frozen configuration. |
| 6 | **Embedding matrix + metadata** | `data/embeddings/v1-corpus/embeddings.npy` (raw bytes of the array) and `embeddings.meta.json` (model, dimension, `chunk_id_order`, token usage) | **Yes**, if size permits | This is the **operative** reproducibility guarantee: no dated snapshot of `text-embedding-3-large` is published, so the cached matrix is what makes the run repeatable. `chunk_id_order` must be hashed because the matrix is positional. |
| 7 | **Experiment configuration** | `experiments/configs/embedding_config.json`, `rag_config.json`, `bm25_config.json`, `rag_prompt.txt` | **Yes** | Already frozen; these files *are* the configuration of record. The prompt is hashed separately because it is prose and is edited most often. |
| 8 | **Source-code Git commit** | The full 40-character commit SHA, recorded as a string, **not** as a Git object hash of the tree | n/a — recorded, not committed | A commit SHA is already content-addressed. The manifest also records the branch and whether the working tree was clean at freeze; **a dirty working tree invalidates the freeze.** |
| 9 | **Dependency/environment lockfile** | `uv.lock` if present, else `requirements.txt`, plus the resolved output of `python -m pip freeze` | **Yes** | A lockfile pins declared ranges; a full freeze additionally captures transitive versions, which is what actually determines behaviour. |
| 10 | **Validation reports** | `data/manifest/validation/` — the C1–C8 coherence report, the ground-truth validation report, and the spec-sync check result | **Yes** | These are the evidence that the freeze gate actually passed, not merely that it was written. |
| 11 | **Run outputs** | Per-system retrieval logs and generated responses, `experiments/runs/<run_id>/` | **Yes** | Retrieval is logged independently of generation. Both must be retained; a response without its retrieval log cannot be audited. |
| 12 | **Environment record** | Python version, OS, package versions of `openai`, `chromadb`, `numpy`, plus the exact `gpt-4o-mini` model string returned by the API | **Yes** | The `gpt-4o-mini` snapshot string matters for the generation step, as no dated snapshot is published for it either. |

## 2. When each hash is captured

| Phase | Captured |
|---|---|
| **Mechanism-sample development** | Nothing. Artefacts 1–5 are unstable while the model is still changing. |
| **Pre-freeze dry run** | Artefacts 10 only, to prove the gate passes. |
| **Final experiment freeze** | Artefacts 1–12, all at once, into `data/manifest/FREEZE.json` with `manifest_version: 1`. |
| **After any BM25 or RAG run** | Artefact 11 for that run only, under a new `run_id`. **Artefacts 1–10 are not re-captured** — if a frozen input changed, that is a protocol deviation, not a re-freeze. |

## 3. Manifest entry shape

```json
{
  "artefact": "final_rendered_corpus",
  "path": "data/corpus/v1/rendered/",
  "algorithm": "sha256",
  "scope": "aggregate over sorted per-file sha256 digests",
  "captured_at": "<ISO-8601 UTC>",
  "manifest_version": 1,
  "git_commit": "<40-char SHA>",
  "working_tree_clean": true,
  "value": "<hex digest>",
  "file_count": 272
}
```

## 4. Rules that make the manifest meaningful

1. **A dirty working tree invalidates the freeze.** Recorded explicitly; a freeze taken with
   uncommitted changes cannot be reproduced from the recorded commit.
2. **The corpus aggregate is computed over sorted per-file digests**, so directory iteration
   order cannot change the value.
3. **The embedding matrix is hashed as raw array bytes**, and `chunk_id_order` is hashed
   separately and stored alongside it. A matrix without its row order is meaningless.
4. **A frozen artefact is never edited.** A changed artefact means a new manifest version
   and a recorded protocol deviation.
5. **Artefact 8 must match the pushed commit.** If the local commit is not pushed, the freeze
   is incomplete.
6. **The manifest is verified, not trusted.** `python3 -m src.manifest.verify` recomputes
   every digest and fails on the first mismatch, so a silent later edit to a frozen artefact
   is caught rather than discovered during write-up.

## 5. What is deliberately NOT hashed

- **API responses that are not part of a run** — exploratory calls during development are
  not reproducibility artefacts.
- **Local `.env`** — contains a secret, is gitignored, and must never be hashed into a
  committed manifest, since a hash of a file path reveals nothing useful while the file
  itself is a credential.
- **Transient caches** — Chroma and `__pycache__` contents are reproducible from committed
  inputs and are not hashed.

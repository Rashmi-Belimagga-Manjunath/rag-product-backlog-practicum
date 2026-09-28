# EXPERIMENT FREEZE CHECKLIST

Nothing on this list may change after the freeze, **for any reason derived from observed
BM25 or RAG performance**. A component changed after results are visible is no longer a
controlled comparison; the change must instead be reported as a protocol deviation.

Reproduce the gate with:

```
python3 -m src.data_generation.build_v1_sample_run   # corpus + C1-C5
python3 -m src.chunking.run_comparison                # C1-C8
python3 -m src.benchmark.validate_ground_truth        # query + ground truth
```

---

## Status

| # | Item | Value | State |
|---|---|---|---|
| 1 | Corpus (272 documents) | — | **NOT GENERATED — by design** |
| 2 | Document versions | 12 superseded, explicit `is_current` | SCHEMA READY |
| 3 | Structured source of truth | `source_model.py` | **READY** (34-doc mechanism sample) |
| 4 | Ground truth | derived from model only | SCHEMA READY; 25/32 slots resolve on sample |
| 5 | Query set | 32 slots | **MACHINE SPEC VALID** |
| 6 | Query categories | 6 categories, distribution frozen | **FROZEN** |
| 7 | Difficulty labels | 11 / 11 / 10 by lexical overlap | BANDS FROZEN, LABELS PENDING CORPUS |
| 8 | Distractor structure | D1–D5, measured not asserted | SCHEMA READY |
| 9 | Chunking configuration | — | **PENDING — see `CHUNKING_DECISION.md`** |
| 10 | C6 duplicate-chunk measure | — | **PENDING APPROVAL** |
| 11 | BM25 k1 | 1.5 | **PROPOSED** |
| 12 | BM25 b | 0.75 | **PROPOSED** |
| 13 | BM25 tokenisation / no stemming | documented | **PROPOSED** |
| 14 | Embedding model | `text-embedding-3-large` | **VERIFIED LIVE** |
| 15 | Embedding snapshot | `text-embedding-3-large` (sole published) | **VERIFIED — no dated alias exists** |
| 16 | Embedding dimension | 3072, `dimensions` unset | **VERIFIED LIVE** |
| 17 | Vector store | Chroma 1.5.9, cosine | **PROPOSED** |
| 18 | NumPy exact cross-check | validation only, never used to alter results | **PROPOSED** |
| 19 | RAG top-k | 5 | **PROPOSED** |
| 20 | Generation model | `gpt-4o-mini` | **PROPOSED** |
| 21 | Generation config | temp 0, max_tokens 800, n=1 | **PROPOSED** |
| 22 | RAG system prompt | — | **NOT YET WRITTEN** |
| 23 | Citation format | `[DOC-ID#Cn]` | **PROPOSED** |
| 24 | Evaluation metrics | 8 metrics, formulas fixed | **DEFINED, SCRIPTS PENDING** |
| 25 | BM25 answer presentation | — | **OPEN DECISION — see metrics §8.1** |
| 26 | Reproducibility artefacts | corpus hash, embedding hash, prompt hash, model snapshot | PENDING FREEZE |
| 27 | Ethics determination | — | **OPEN — NCI coordinator/supervisor** |

Nothing in this table is FROZEN. **State: NOT FROZEN.**

---

## A. Approvals required before the freeze

These are the only open decisions. Each needs an explicit answer.

1. **C6 measure revision** — replace type-bag containment with same-document 8-gram
   containment > 0.5, threshold <2% of chunks. Evidence: same-document 8-gram overlap is
   0.0% for every chunk in both configurations, so the current measure has ~100% false
   positives. See `CHUNKING_DECISION.md` §3.
2. **Chunking configuration** — C1–C8 pass for both A (1000/200) and B (600/100) once C6 is
   repaired, so the criteria cannot rank them. Recommended tie-break: keep the already-
   approved A. See `CHUNKING_DECISION.md` §4.
3. **BM25 answer presentation** — BM25 returns passages, not prose, so usefulness, clarity
   and trust are not comparable unless BM25 is given a user-facing artefact. Recommended:
   present the top-5 passages as the BM25 response and disclose the confound. See
   `docs/evaluation_metrics.md` §8.1.

## B. Corpus requirements before generation

Generation is blocked until the source model guarantees all of these. The 34-document
mechanism sample deliberately does **not** contain them, so `validate_ground_truth` reports
7 unmet slots. Those 7 are **corpus requirements, not defects**.

| Slot | Requirement |
|---|---|
| Q-05 | An informal/colloquial ticket; lowest lexical overlap in the benchmark |
| Q-SUP-3 | A feature spec whose approval limit **value changed** between v1 and v2 |
| Q-10 | An explicit component-to-component dependency |
| Q-11 | An explicit ordering dependency |
| Q-14 | An implicit ordering dependency |
| Q-20 | An implicit ordering dependency, expressed as a PRD sequence rather than in prose |
| Q-21 | An implicit dependency whose evidence sits in a superseded document |

`python3 -m src.benchmark.validate_ground_truth --against-final` makes any unmet slot a
**hard stop** at freeze time (exit 1). Without the flag, unmet slots are reported as corpus
requirements and the gate exits 2, so the two cases cannot be confused.

**No selector may resolve a slot via a fallback.** Q-20 was found substituting current PRDs
when no implicit ordering dependency existed, which made it look resolved against the
wrong evidence. `tests/test_benchmark_spec.py` now fails if any selector reintroduces a
fallback.

## C. Hard stops

- **C8 zero unassigned content.** If the final corpus loses any content to a boundary, the
  experiment does not run.
- **Any unresolved ground-truth reference** in the final corpus. No fallback, no fuzzy
  matching, no hand-authored labels.
- **C5 dependency coverage** must not be weakened to pass.
- **n = 32.** All queries are reported. A query that failed is reported as failed, with its
  denominator intact. No silent exclusions.

## D. Recorded as fixed components, not variables

- Embedding model and dimension, Chroma, and the chunker are **components of the RAG
  treatment**, not experimental variables. No result may be attributed to them.
- No generation-model comparison, embedding-model comparison, prompt variants, temperature
  sweep, or top-k sweep.

## E. Reproducibility artefacts to capture at freeze

- Corpus manifest hash, and per-document SHA-256.
- Chunker configuration and its C1–C8 report.
- Ground-truth JSON and its validation report.
- Query specification hash, including exact Q-SUP wording.
- Prompt file hash; BM25 configuration; RAG configuration.
- Exact `gpt-4o-mini` snapshot string (no dated snapshot is published for the embedding
  model, so `text-embedding-3-large` is recorded as the sole published snapshot).
- Cached embedding matrix plus its metadata.
- Every retrieval log and every generated response, logged **independently** — retrieval
  before generation.
- `uv.lock`, Python version, library versions.

## F. Integrity commitments

- No result is reported for a configuration that was tuned after results were seen.
- RAG performing worse than BM25 is a valid finding and will be reported as such.
- Limitations are reported before results: n=32 is descriptive only; no statistical
  generalisation; researcher-rated metrics are not participant data; the BM25 artefact
  confound is disclosed; the closed-domain templated corpus limits external validity.

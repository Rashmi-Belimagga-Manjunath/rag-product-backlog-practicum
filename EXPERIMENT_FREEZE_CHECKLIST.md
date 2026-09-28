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
| 9 | Chunking configuration | **1000 / 200** | ✅ **FROZEN 2026-09-28** |
| 10 | C6 duplicate-chunk measure | same-document 8-gram containment > 0.5, <2% of chunks | ✅ **FROZEN 2026-09-28** |
| 11 | BM25 k1 | 1.5 | ✅ **FROZEN 2026-09-28** |
| 12 | BM25 b | 0.75 | ✅ **FROZEN 2026-09-28** |
| 13 | BM25 tokenisation / no stemming / verbatim queries / ties on chunk ID | documented | ✅ **FROZEN 2026-09-28** |
| 14 | Embedding model | `text-embedding-3-large`, 3072, no dimensions override | ✅ **FROZEN 2026-09-28** — matrix creation config recorded |
| 15 | Embedding snapshot | `text-embedding-3-large` (sole published) | **VERIFIED — no dated alias exists** |
| 16 | Embedding dimension | 3072, `dimensions` unset | **VERIFIED LIVE** |
| 17 | Vector store | Chroma 1.5.9, cosine | ✅ **FROZEN 2026-09-28** (D3) |
| 18 | NumPy exact cross-check | validation only, never used to alter results | ✅ **FROZEN 2026-09-28** |
| 19 | RAG top-k | 5 | ✅ **FROZEN 2026-09-28** (D-007) |
| 20 | Generation model | `gpt-4o-mini` | ✅ **FROZEN 2026-09-28** (D-007) |
| 21 | Generation config | temp 0, max_tokens 800, n=1 | ✅ **FROZEN 2026-09-28** (D-007) |
| 22 | RAG system prompt | 7 requirements frozen; text written + hashed | ✅ **REQUIREMENTS FROZEN 2026-09-28** |
| 23 | Citation format | `[DOC-ID#Cn]` | ✅ **FROZEN 2026-09-28** (D-007) |
| 24 | Evaluation metrics | Layer A + Layer B, 8 metrics | ✅ **FROZEN 2026-09-28** (D-009) |
| 25 | BM25 answer presentation | top-5 passages; no prose answer fabricated | ✅ **SETTLED 2026-09-28** |
| 26 | Reproducibility artefacts | 12 artefacts, SHA-256, manifest + verifier | ✅ **FROZEN 2026-09-28** (D-012) |
| 27 | Ethics determination | — | **OPEN — NCI coordinator/supervisor** |
| 28 | Dependency vocabulary | `ordering` added for Q-11/Q-14/Q-20 (D-013) | ✅ **APPROVED 2026-09-28** — selectors + 32-query spec unchanged |
| 29 | Approval-limit field | `Feature.approval_limit` for Q-SUP-3 (D-013) | ✅ **APPROVED 2026-09-28** — mechanism sample carries none |

**State: PARTIALLY FROZEN.**

Frozen: chunking configuration (9), the C6 measure (10), BM25 scoring (11–13), the
embedding configuration (14), the vector store and cross-check (17–18), the whole RAG
configuration including the hashed prompt (19–23), the two-layer design and BM25 output
form (25), and the reproducibility artefact specification (26, D-012).

Everything the methodology freeze requires is now FROZEN, including the evaluation metric
definitions (24, D-009, approved 2026-09-28 with the explicit empty-prediction
convention). Validation reports (item 20 of the old list) are captured at freeze, not
before.
**No final corpus, BM25 run, RAG run, results or charts have been produced.**

**No final corpus, BM25 run, RAG run, results or charts have been produced.**

**Deliberately not started, by instruction:** the final 272-document corpus, the BM25 run,
the RAG run, and all results and charts.

---

## A. Approved on 2026-09-28

The following were settled by explicit student approval and are recorded **before any BM25
or RAG run**. No retrieval or generation result was used for any of them.

1. **C6 measure revision — APPROVED.** Original: same-document word-type-bag containment
   > 0.9, which flags 12 of 12 same-document pairs in the 1000/200 configuration including
   pairs sharing no repeated text, because a chunk here carries only 128 word types per 577
   words. Replacement: **same-document 8-word shingle containment > 0.5, fewer than 2% of
   chunks**. This is a **project-defined structural validation threshold**, not an
   externally validated constant, and **C6 is a corpus/chunk coherence check, not a
   retrieval-performance metric**. A positive control requires it to fail on a real verbatim
   duplicate and pass on identical text in two different documents. See
   `CHUNKING_DECISION.md` §3–4.
2. **Chunking configuration — FROZEN at 1000 / 200.** Once C6 discriminates, 1000/200 is the
   only candidate passing all eight criteria; 600/100 fails C6 at 6.3% against a 2% limit.
   A pre-experiment structural decision. Must not be re-tuned after results are observed, and
   must not be changed on anticipated retrieval performance. See `CHUNKING_DECISION.md` §5.
3. **Two-layer evaluation — APPROVED.** Layer A compares BM25 and RAG retrieval like-for-like
   (P@5, R@5, MRR, dependency accuracy) over the same corpus, queries, ground truth and
   `k=5`. Layer B rates each system's real user-facing output (usefulness, clarity, trust,
   task completion time). **BM25 presents its top-5 retrieved passages; RAG presents a
   generated grounded answer with `[DOC-ID#Cn]` citations. The two output forms are
   explicitly not identical and are not claimed to be, and no prose answer is fabricated for
   BM25.** Layer B is therefore not like-for-like, and that asymmetry is a documented
   characteristic of the systems, not a confound to be engineered away. See
   `docs/evaluation_metrics.md` §0 and §7.1.
4. **Error analysis — APPROVED.** BM25 has no generation stage, so **every BM25 error is a
   retrieval error** and is assessed directly. For RAG: required evidence absent from the
   top-5 is a **retrieval failure**; evidence retrieved but the answer incorrect, incomplete,
   unsupported, or failing to use it is a **generation/reasoning failure**. Classification is
   driven by the retrieval log, which is written before generation. See
   `docs/evaluation_metrics.md` §5.1.

### A.1 Correction recorded

An earlier draft of `CHUNKING_DECISION.md` and D-005/D-006 claimed same-document 8-gram
containment was 0.0% at every threshold. **That was a bug in the analysis script, not a
property of the corpus** — it grouped chunks by splitting the chunk ID on `"#"`, but chunk
IDs are `<document_id>-C<index>` and contain no `#`, so every same-document comparison set
was empty. The claim is withdrawn, the figures were recomputed, and the corrected numbers
strengthened the C6 revision and did not change the frozen configuration. See D-006a.

## A.2 Ethics — D-011 remains OPEN

No assumption is made that ethics approval exists, or that it is unnecessary. No
human-participant data is collected, and nothing begins until the NCI coordinator or the
appropriate ethics process has determined what is required. **The technical BM25/RAG
experiment is separable from any participant evaluation** and does not depend on one. If
participant evaluation is later approved, it must evaluate the **already-frozen** system;
changing the system during participant testing would invalidate both the technical
comparison and the participant data. Detail: `DECISIONS.md` D-011.

## B. Corpus requirements before generation

These seven are **explicit final-corpus gates**. They are intentionally unresolved until
the final corpus is generated, and **no artificial replacement may be invented merely to
satisfy the benchmark** — a fabricated document would make the benchmark satisfiable
without the corpus genuinely containing the phenomenon. The final corpus generation must
satisfy them, and the ground-truth selectors must then resolve against the resulting
authoritative corpus.

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

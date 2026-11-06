# Methodological Decision Log

Append-only record of decisions that affect research validity.

**Format:** each entry gets an ID (`D-000`, `D-001`, …), a date, the decision, the
rationale, the alternatives considered, and who decided. Superseded decisions are
marked, never deleted.

**Rule:** a decision made *after* seeing results is a different kind of decision from
one made before. Every entry states which it was.

---

## Decisions taken

### D-000 — Project scaffold and governance established

**Date:** 2026-09-27
**Phase:** Checkpoint 1 (pre-implementation)
**Decided before results:** Yes — no experiment has been run.
**Decided by:** Agent, ratified by student

**Decision.** Established the repository scaffold, `AGENTS.md`, this decision log,
`PROJECT_SPECIFICATION.md`, and `DATA_DESIGN.md`. No dataset generated, no retrieval
system implemented, no evaluation run.

**Deviation from the student's suggested structure, and why.** The suggested tree put
synthetic data in a single `data/synthetic/` folder. It was split into
`data/synthetic/source_model/` and `data/synthetic/documents/`, and a
`data/versions/` folder was added. Reason: ground-truth labels must be derived from the
structured model rather than by re-reading generated documents, and that separation has
to be enforced by the directory layout, not just by convention. If model and documents
share a folder, the derivation path becomes ambiguous and unverifiable after the fact.

**Also added:** `src/vectorstore/` and `results/EXP-YYYYMMDD-NNN/{raw,processed,tables,figures}/` for per-run output,
since results must never be overwritten.

**Status:** Recorded. No experiment run.

---

### D-001 — Implementation decisions ratified by the student

**Date:** 2026-09-27
**Phase:** Checkpoint 1 → 2 transition
**Decided before results:** Yes — no experiment has been run. **All of these were
settled before any retrieval system existed, which is the point.**
**Decided by:** Student, after re-reviewing CA2

#### D1 — Orchestration: native Python, not Flowise

**Decision.** Implement the RAG pipeline in native Python.

**Deviation from CA2.** CA2 §3.1/§3.4 proposed Flowise as the orchestration layer. This
is a **departure from the committed design** and is recorded as such.

**Student's stated rationale.** The core contribution is a controlled empirical
comparison. Python gives better control over reproducibility, retrieval logging,
experiment configuration, automated evaluation, and separation of retrieval from
generation.

**What is NOT changing.** The RAG *architecture* remains exactly as established in
CA2 and in `PROJECT_SPECIFICATION.md` §5:

```
documentation → preprocessing/chunking → OpenAI embeddings → vector database
              → top-k semantic retrieval → GPT-4o-mini → grounded response + sources
```

Flowise was an orchestration tool, not a research design element. The substitution
changes how the pipeline is built, not what is being tested.

**Consequence to disclose in the write-up.** CA2 named Flowise; the implementation uses
custom Python. This must be stated as an implementation deviation, with the reason.

#### D2 — Embeddings: OpenAI, unchanged

**Decision.** Use OpenAI embedding models, consistent with CA1/CA2. No switch to local
open-weights models.

**Must be recorded per run:** exact embedding model name, configuration, API/model
version or date where available, and all relevant settings.

**Binding constraint:** the embedding model must not be changed after seeing
experimental results.

#### D3 — Vector store: Chroma, approved

**Decision.** Use **Chroma** as the vector store for the Python RAG implementation.

**Binding constraints — the implementation must preserve:**

| Property | Why |
|---|---|
| Stable document IDs | A recorded result must be checkable against a later run |
| Stable chunk IDs | Ground truth attaches at chunk level by provenance; unstable IDs break it |
| Metadata | Needed to report by document type, product, version, supersession |
| Retrieval scores | Required for reproducible ranking inspection |
| Retrieval ranking | Required for MRR, and for separating retrieval from generation failure |
| Source-document traceability | Inline citations are a design-level interpretability measure |

**Exact-NumPy cross-check — approved as a validation test.** Cosine similarity is
computed directly in NumPy from the stored embedding matrix and compared against
Chroma's returned ordering: top-k *set* equality, ordering equality, and score
finiteness/consistency.

**Binding constraint on the cross-check.** It is a **validation mechanism only**. It must
not be used to alter, correct, adjust or tune experimental results. If it disagrees with
Chroma, that is a finding to report and investigate, not a discrepancy to resolve in
favour of whichever number looks better. A retrieval fault caused by the store is not a
result about RAG, and reporting it as one would be a false finding.

Full methodology in `PROJECT_SPECIFICATION.md` §11.1.


#### D4 / D5 — BM25: standard implementation, parameters fixed in advance

**Decision.** Use a standard BM25 implementation with **k1 = 1.5, b = 0.75**, fixed
**before** the comparison is run and recorded in the experiment configuration.

**Binding constraint:** these must not be tuned after seeing RAG results. Tuning the
baseline after the fact would amount to engineering a result.

#### D6 — Corpus scale: deferred until the source model exists

**Decision.** Do not pick a document count arbitrarily. Design the structured
source-of-truth model first, then propose a corpus size with a stated rationale.

**Stated requirements for the corpus:** large enough to create meaningful retrieval
challenges; small enough for reliable ground-truth validation; rich enough to contain
cross-document relationships; sufficient to support dependency-analysis queries;
realistic for product-management documentation analysis. Controlled relationships and
research validity take priority over document count.

#### D7 — Query set: deferred

**Decision.** Do not finalise query count or category distribution yet. Design the
source-of-truth model, understand the resulting corpus, then propose total queries,
categories, per-category counts, and the rationale — and **wait for approval** before
generating the final query set.

A working range of ~20–30 is acceptable for planning only. It is not the final number.

#### D8 — Application/UI: deprioritised

**Decision.** No UI work at this stage. Priority is the research pipeline:

```
corpus → BM25 → semantic retrieval → RAG → evaluation
```

A simple interface may be added after the experimental pipeline works.

#### D9 — Real artefacts: none. Fully synthetic corpus

**Decision.** No confidential or company artefacts. Use a controlled synthetic corpus.

**Consequence.** The final research documentation must clearly identify the corpus as
synthetic and discuss this as a **limitation / threat to external validity**. This is
not optional wording.

#### Q4 — Rendering: deterministic templates

**Decision.** Template-based deterministic rendering for the primary corpus. The
structured source of truth controls all content.

**Binding constraint.** An LLM must not be used to independently invent documents or
ground truth. Controlled terminology variation and realistic wording are permitted, but
**every factual relationship must remain traceable to the structured source of truth.**

Rendered documents should still resemble realistic product-management documentation:
PRDs, feature specifications, PBIs/user stories, and technical documentation where
appropriate.

#### Ethics

**Decision.** Do not assume whether ethics approval is required *for the synthetic
corpus* — that question is separate and remains open. The human evaluation must not
begin until the required ethics approval is confirmed. No participant recruitment and no
participant data collection during the current implementation phase.

**Status:** hard gate. No participant activity of any kind until approval is confirmed
in writing.

**Separation of phases — approved.** Synthetic-data development and human-participant
evaluation are treated as two distinct phases:

| Phase | Status | Gate |
|---|---|---|
| Synthetic-data development | **Active** | None. Proceeds now. |
| Human-participant evaluation | **Not started** | Blocked pending NCI coordinator/supervisor confirmation. |

No participant data collection, no recruitment, no human evaluation in the current phase.

**Binding constraint on documentation.** Until the NCI process has confirmed the
requirement, project documentation and the thesis must **not** state that ethics approval
is — or is not — required for the synthetic-only corpus. It must be recorded as an open
administrative/methodological question. The student will confirm with the NCI
coordinator/supervisor.

---

### D-002 — Evaluation design decisions approved by the student

**Date:** 2026-09-28
**Phase:** Checkpoint 2 (source model complete, pre-corpus)
**Decided before results:** Yes — no retrieval system has been built and no experiment
has been run. **D3, Q5, Q6 and Q7 were all settled before the corpus existed**, which is
the point: they are design commitments, not post-hoc adjustments.
**Decided by:** Student

#### Q5 — Stratify by explicit vs implicit dependencies: approved

**Decision.** The evaluation distinguishes two dependency types:

1. **Explicit** — the dependency is directly stated in the documentation.
2. **Implicit** — the dependency must be inferred from relationships across documents or
   from the structured source-of-truth model.

This distinction is recorded **as metadata on every dependency-related query**, and
results are later **stratified by explicit and implicit subsets**.

**Binding constraint on what "implicit" may mean.** An implicit dependency must **not**
require unsupported common-sense inference. The expected dependency must be explicitly
defined in the structured source-of-truth model, so ground truth remains reproducible.

**Why this is the most important stratification in the project.** It is the mechanism by
which the write-up can say *where* semantic retrieval actually helps. A dependency that a
document states outright may be findable by keyword search. A dependency that only
follows from the relationship between three documents is the specific case where
cross-document reasoning is doing work that lexical matching cannot.

#### Q6 — Distractor ratio: approved at approximately one-third

**Decision.** Approximately **one-third** of the retrieval candidates function as
controlled distractors, where applicable.

**Binding constraint — distractors must be realistic near-matches, not random
irrelevant documents.** Random off-topic documents are trivially rejected by both
systems and would inflate both scores while testing nothing. Approved distractor types:

| Type | Description |
|---|---|
| D1 | Documents sharing terminology but addressing a different feature |
| D2 | Related features carrying different requirements |
| D3 | Technically related components that are **not** the required dependency |
| D4 | Overlapping keywords without sufficient contextual relevance |
| D5 | Superseded versions of the correct document (see Q7) |

**How relevance and non-relevance are established.** By **construction, not by
judgement**. Each distractor is generated as a structured near-miss of a relevant
entity, and its non-relevance is asserted in the source-of-truth model by its differing
`feature_id`/`component_id`. Ground truth is therefore derivable, never subjective.

**Binding constraint.** The distractor ratio must be **fixed before the main experiment**
and must **not** be changed after seeing BM25 or RAG results.

#### Q7 — Superseded document versions: approved, in controlled manner

**Decision.** The corpus will contain superseded/older document versions to test whether
retrieval can distinguish current documentation from outdated but lexically similar
documentation.

**Required metadata on every versioned document:** `document_id`, `feature_id`,
`version`, `status`, created/modified date, `superseded_by`, and effective/current status.
The current version must be **unambiguous in the source-of-truth model**.

**Binding constraints:**
- Queries involving versions must have explicitly defined expected answers and relevant
  documents.
- **Ambiguity must not be manufactured for its own sake.** The purpose is to test
  current-versus-outdated discrimination, not to make the task arbitrarily hard. Where a
  query would be ambiguous, it is either rephrased or dropped.


---

## Open assumptions

Assumptions still unconfirmed. Each must be confirmed or replaced before it is relied
upon. See `PROJECT_SPECIFICATION.md` §12.

_Status refreshed 2026-10-28 following completion of EXP-20260929-001. Historical
entries below are untouched._

| ID | Assumption | Status |
|---|---|---|
| A1 | B2B SaaS / HRTech is an appropriate synthetic domain | **Resolved** — corpus v1 generated on this domain (D-004) |
| A2 | Fully synthetic documentation is acceptable in place of real artefacts | **Resolved by D9** — synthetic confirmed |
| A3 | A few hundred chunks is sufficient to observe a measurable difference | **Resolved** — corpus v1 built and frozen (272 chunks; FREEZE.json) |
| A4 | Chunk size 1000 / overlap 200 remains appropriate | **Resolved by D-006** — frozen at 1000/200 after the chunking pilot |
| A5 | Student intends to work ahead of the six-week schedule | Stated intention, not commitment |
| A6 | Ethics approval is not required for a fully synthetic corpus | **Unconfirmed — do not assume either way.** Being confirmed with the NCI coordinator/supervisor (D-011). Hard gate on human-participant activity |
| A7 | The exact OpenAI embedding model name | **Resolved** — `text-embedding-3-large` verified and frozen 2026-09-28 |

---

## Still open

_Status refreshed 2026-10-28. The items below were blockers for the run; the run is now
complete. Only the ethics determination remains externally open._

| ID | Decision | Status |
|---|---|---|
| D6 | Corpus scale and product count | **Closed** — corpus v1 generated (272 rendered documents) and frozen |
| D7 | Query count, category distribution, difficulty definition | **Closed** — 32-query benchmark built, frozen, and run |
| D8 | UI framework | **Closed for the practicum** — Streamlit prototype implemented (`prototype_app.py` / `app/`), presentation-layer only |
| A7 | Exact OpenAI embedding model | **Closed** — frozen 2026-09-28 (see above) |
| Ethics | Whether ethics approval covers a synthetic-only corpus / researcher-rated metrics | **OPEN (D-011)** — hard gate on human-participant evaluation; technical results unaffected |

**Approved and closed:** D1, D2, D3, D4, D5, D6, D7, D9, Q4, Q5, Q6, Q7.


---

### D-003 — D6 and D7 approved with conditions

**Date:** 2026-09-28
**Phase:** Checkpoint 2 → 3 transition
**Decided before results:** Yes. No corpus, no query set, no BM25, no RAG, no results.
**Decided by:** Student

Corpus scale, query count, and evaluation design approved as proposed in
`docs/proposal_corpus_and_queries.md`, **subject to conditions the student attached.**

#### Approved corpus targets — targets, not results

272 documents (260 current, 12 superseded) · 24 features (12/product) · 16 requirements
(8/product) · 18 components · ~208 dependencies · ~435 reference edges · 12 conflicts ·
~289 chunks.

**Binding constraint:** the ~208 dependencies, ~435 edges and ~289 chunks are **targets
estimated from the structured model, not results.** After generation the actual counts must
be calculated and reported: document count, chunk count, dependency count,
explicit/implicit split, reference count, conflict count, superseded/current split.

**These must not be modified after seeing retrieval results.**

#### Approved query set — 32 queries

**Binding constraint on reporting:** n=32 is **not** intended to support strong statistical
significance testing, and no statistical generalisability may be claimed from it. Results
are interpreted through descriptive statistics, direction and effect of differences,
category-level analysis, and error analysis. This limitation must be stated in the thesis.

**Binding constraint on difficulty:** lexical overlap is a **benchmark-construction
measure**, not a universal or validated psychological measure of task difficulty. Its
purpose is to create controlled variation in lexical alignment between a query and the
information that answers it. Classification is frozen before either system is evaluated.
A query not falling into its intended band is revised **before** the systems run, never
reclassified after seeing results.

**Binding constraint on distractors:** the ~1/3 ratio is **not** to be fabricated if the
generated corpus does not naturally produce it. Sequence: design model → generate → measure
actual distribution → report measured values → if materially inadequate, modify the source
model and **regenerate before either system is evaluated** → freeze. Distractors must never
be removed because BM25 performs well on them, nor added because RAG performs well.

**Binding constraint on the corpus scale:** ~289 chunks is accepted as a
semester-scale Master's prototype. The corpus must **not** be artificially enlarged to
inflate the number. The methodology must state that the corpus is synthetic,
semester-scale, and not intended to represent enterprise-scale retrieval, and that
external validity is therefore limited. Ambiguous or null results must **not** be
retro-fitted by enlarging or modifying the corpus after seeing which system performed
better. A larger follow-up may be proposed separately if genuinely justified.

**Binding constraint on supersession:** the 3 version queries are retained, and specifically
Q-SUP-2, where the superseded document is the correct answer. The purpose is contextual
and version awareness, not the ability to retrieve the newest document.

#### Chunking — initial configuration, pilot-gated

`chunk_size=1000`, `chunk_overlap=200` is permitted as the **initial** configuration, to be
validated as a **pre-system configuration pilot** and not as a result-tuned parameter.
Required before the main comparison: verify chunks are coherent; check that requirements
and dependencies are not split incorrectly; document the decision; freeze; use the identical
corpus and chunking policy for both systems. Chunking must not change after BM25/RAG
performance is seen.

#### Research-integrity sequence — binding

Corpus, query set, ground truth, distractor structure, difficulty labels, chunking
configuration and model configuration are all frozen **before** the main BM25 vs RAG
comparison:

```
SOURCE-OF-TRUTH DESIGN → CORPUS GENERATION → GROUND TRUTH → QUERY DESIGN
→ DIFFICULTY VALIDATION → CHUNKING PILOT → CONFIGURATION FREEZE
→ BM25 + RAG EXPERIMENT → RESULTS → ANALYSIS
```

No component may be tuned after seeing which system performs better.

#### Ethics — reaffirmed, still open

Synthetic-data development and human-participant evaluation are separate phases. No
participant data collection, no recruitment, no human evaluation. The requirement for the
synthetic-only corpus remains an open administrative/methodological question to be
confirmed with the NCI coordinator/supervisor, and documentation must not state a
determination either way until confirmed.

#### A7 — resolved, see D-004

A7 is closed by D-004 below. The model was approved and verified live on 2026-09-28.

---

## D-004 — Final schema, mechanism sample, and pre-experiment configuration

**Date:** 2026-09-28
**Status:** Accepted

### A7 closed — embedding model approved and verified

`text-embedding-3-large`, native 3072 dimensions, `dimensions` parameter unset, Chroma
cosine. Verified live: model available, 3072 dimensions returned, vectors finite and
unit-normalised (L2 norm 0.9999). `encoding_format` is `float`; `float32` returns HTTP 400.

**Two corrections recorded here, because both were previously wrong in writing:**

1. **Snapshots.** The earlier claim that OpenAI provides no version-pinning for embedding
   models was wrong and is withdrawn. Snapshots are a documented feature and are listed for
   this model. The complete published snapshot list contains exactly one entry, identical
   to the alias and the default; **no dated `text-embedding-3-large-*` variant is
   published**, and the live API returns no dated alias. Pinning to a more specific snapshot
   is therefore not available for this model. The cached embedding matrix is the operative
   reproducibility guarantee and must be committed as a derived artefact.

2. **Framing.** The embedding model is a **fixed component of the RAG treatment**, not an
   experimental variable. This study does not compare embedding models. The methodology must
   **not** describe the choice as "not handicapping RAG", "avoiding a weak embedder", or
   "weakening the RAG arm", nor as a bias favouring one arm. Those framings describe a
   different design.

### Final source-of-truth schema accepted

Applied in `src/data_generation/source_model.py`: version lineage with an unambiguous
`is_current`; a distinct `Prd` entity; `DocumentLink` as a first-class reference edge;
`Feature.confusable_with` for declared distractors; `adjacent_component_ids` on components;
PBI feature terminology de-duplicated; and provenance accessors that fail loudly rather than
guessing.

### Mechanism sample accepted as a mechanism demonstration

34 documents from 69 links, 3,046 words, 3 superseded, 2 products with deliberately
different registers, 5/5 explicit and implicit dependencies, 2 conflicts, and all eight
document types. All six link types are exercised. All structural checks pass; determinism
holds at model, render, and chunk level.

### Defects found and fixed during validation

These were found by validation and are recorded because each one silently corrupted data:

- **A document's subject was the wrong entity.** `_primary_id_of` searched fields by name
  order, and `Pbi`/`Ticket` *carry* a `feature_id` reference, so every PBI and ticket
  document claimed to be a feature document. PBI and ticket entities never appeared as the
  subject of any chunk, so provenance-based ground truth could not target them. Fixed by
  explicit type dispatch, which now fails loudly for an unmapped type.
- **Versioned lookups returned superseded content.** `get_feature`/`get_prd` took the first
  match, which is normally the superseded v1. Now resolved to the current version, and
  refuses to guess when zero or multiple current versions exist.
- **Chunks carried only their own subject.** Ground truth needs a PBI chunk that states a
  dependency on `COMP-06` to be *about* `COMP-06`. All referenced entity IDs are now
  propagated from the declared `DocumentLink` set, along with version, supersession, and
  document date.
- **Two coherence checks were wrong, not the data.** C1 used a punctuation heuristic and
  flagged chunks that correctly ended on a bullet or a metadata field; replaced with an
  exact contiguous-unit test. C2/C3 counted occurrences corpus-wide, so a requirement
  legitimately appearing in both a superseded and a current PRD was reported as "split";
  now scoped per document. Both changes fixed the tests, not the corpus.

### C5 recorded as a sample-scale artefact, threshold unchanged

C5 (`<3%` orphan chunks) fails at 35.3% on the sample. The cause is measured, not guessed:
the sample's component documents are 38–51 words against an approved full-corpus target of
300–550. The threshold was **not** loosened. A projection using the real packer at approved
length targets gives 272 documents, 292 chunks (approved target 289), and 0 orphans — which
explains the artefact without replacing the measurement. **C5 must be re-measured on the
generated corpus before the freeze.**

### Chunk configuration: primary carried forward, comparison still owed

Primary 1000/200 is carried forward. The sample **cannot** discriminate between 1000/200 and
600/100, because no sample document exceeds 239 words and both sizes yield one chunk per
document. The comparison must be repeated on the full corpus before the freeze. This is
recorded as an open obligation rather than a resolved choice.

### Still open

- RAG top-k, generation model, RAG prompt, and evaluation scripts are not yet set.
- Ethics determination remains open with the NCI coordinator/supervisor. No determination
  may be stated in either direction until confirmed. Human-participant evaluation is a hard
  gate.
- The API key used for live verification was exposed in conversation and must be
  revoked and rotated. It is gitignored and was never committed.

### D-005 — C6 replaced: type-bag containment is not a duplication measure (APPROVED)

**Status:** APPROVED by the student 2026-09-28 and FROZEN. Recorded before any BM25 or RAG
run. No retrieval or generation result was used.

The original C6 defined a duplicate chunk pair as two chunks in the same document whose
word-type-bag containment exceeded 0.9. Measured over all same-document pairs, that measure
flags **12 of 12 pairs (100%)** for the 1000/200 configuration and 29 of 53 (55%) for
600/100 — including pairs that share no repeated text at all.

The cause is saturation. A chunk in this closed-domain templated corpus carries only 128
distinct word types across 577 words (ratio 0.22), so two long chunks of the same document
necessarily contain nearly the same types whether or not anything was copied. A 0.9
threshold therefore measures corpus vocabulary size, not chunk duplication.

**Approved replacement:** a duplicate chunk pair is two chunks in the same document whose
8-word shingle containment exceeds 0.5, and fewer than 2% of chunks may be involved in such
a pair. Under the replacement, 1000/200 flags 0 pairs (0.0%) and 600/100 flags 4 pairs
(6.3%).

The threshold is **a project-defined structural validation threshold for this corpus**. It
is not an externally validated constant and must not be described as one. **C6 is a
corpus/chunk coherence check, not a retrieval-performance metric**, and no C6 result may be
cited as evidence about either system. A positive control in `tests/test_benchmark_spec.py`
requires the measure to fail on a genuine verbatim duplicate and to pass on identical text
in two different documents.

Full evidence, including a correction to an earlier faulty analysis, is in
`CHUNKING_DECISION.md`.

### D-006 — Chunking frozen at 1000/200 on C1–C8 grounds (APPROVED)

**Status:** APPROVED by the student 2026-09-28 and FROZEN. Recorded before any BM25 or RAG
run.

Once C6 was replaced with a measure that actually discriminates, **1000/200 is the only
candidate that satisfies all eight criteria**; 600/100 fails C6 at 6.3% against a 2% limit.
The four B failures are all short ragged remainder chunks that substantially restate the
preceding chunk, because B's 100-word overlap window accounts for most of a 109-word tail.

The frozen configuration was originally anticipated to require a non-performance tie-break
between two passing candidates. It does not: the corrected measurement shows a clean
structural discriminator. The outcome is the same, and the basis is still entirely
structural — C6 measures duplication introduced by the chunker and is computable without
running either retrieval system.

**Explicitly forbidden:** switching to 600/100 on anticipated or observed retrieval
performance; re-tuning chunk size or overlap after any BM25 or RAG result is seen; relaxing
the C6 threshold to admit a configuration. Finer granularity can favour embedding retrieval,
which is a reason to withhold the change, not to make it.

### D-006a — Correction: an earlier analysis in this record was wrong (2026-09-28)

An earlier draft of D-005/D-006 and of `CHUNKING_DECISION.md` reported that "maximum
same-document 8-gram containment is 0.0% at every threshold, for every chunk, in both
configurations", and used that figure to argue that C6 had no false positives.

**That figure was an artefact of a bug in the analysis script, not a property of the corpus.**
The script grouped chunks by splitting the chunk ID on `"#"`, but chunk IDs have the form
`<document_id>-C<index>` and contain no `#`. Every chunk formed its own group, the
same-document comparison set was always empty, and the reported maximum was necessarily 0.0.

The claim is withdrawn and the numbers recomputed with correct grouping by `document_id`.
The correction changed the reason 1000/200 was selected — from "tie-break between two
passing candidates" to "only candidate passing the structural checks" — and strengthened the
case for the C6 revision, but did not change the frozen outcome. Recorded here because a
research record must not contain evidence that later turns out to be wrong, even when the
conclusion survives.

### D-007 — RAG configuration (APPROVED AND FROZEN)

**Status:** APPROVED and FROZEN by the student 2026-09-28. Recorded before any BM25 or RAG
run. Machine-readable form: `experiments/configs/rag_config.json` (`"frozen": true`), prompt
at `experiments/configs/rag_prompt.txt`.

top-k 5 (matches the `@5` metric cutoff, ~1,700 token context, ~1.7% of the projected 289
chunks); `gpt-4o-mini` at temperature 0, max_tokens 800, n=1; machine-checkable
`[DOC-ID#Cn]` citations validated against the retrieval log. The system prompt must enforce
grounding, abstention, per-claim citation, no invented identifiers, superseded-version
awareness, advisory framing and no autonomous action. Prompt variants, temperature sweeps
and top-k sweeps are explicitly excluded, because selecting among them would turn this into
an optimisation exercise rather than a controlled comparison. Detail: `docs/rag_configuration.md`.

### D-008 — BM25 configuration (APPROVED AND FROZEN)

**Status:** APPROVED and FROZEN by the student 2026-09-28. Recorded before any RAG run.
Machine-readable form: `experiments/configs/bm25_config.json` (`"frozen": true`).

k1 1.5, b 0.75 (Robertson & Zaragoza 2009 defaults), Lucene non-negative IDF, chunk-level
retrieval, lowercase with Unicode word tokenisation, no stemming and no stopword removal
inside the retriever. Queries are used verbatim with no expansion or rewriting. Ties break
on ascending chunk ID. BM25 may not be tuned, re-ranked or query-expanded after results are
visible, since that would convert a traditional baseline into a fitted competitor. Detail:
`docs/bm25_configuration.md`.

### D-009 — Evaluation metrics (APPROVED AND FROZEN)

**Status:** APPROVED AND FROZEN 2026-09-28. The exact operational definitions in
`docs/evaluation_metrics.md` are frozen. The dependency precision empty-prediction
convention documented below supersedes the earlier "1.0 silence" convention; the
corrected definitions were formally approved on 2026-09-28. The two-layer design and the
BM25 output form (D-010) were already approved and are not reopened by this.

Each metric now specifies numerator and denominator, unit of analysis, aggregation, tie
treatment, zero-relevant-item queries, dependency-not-applicable queries, scale for
human-facing measures, missing-value handling, which system it applies to, and whether it
is retrieval-level or user-facing. Conventions are stated once in §1 and per metric in
§2–§7.

Points that required an explicit decision rather than a default:

- **Zero-relevant-item queries are a ground-truth defect, not a metric value.** Recall@5
  would have an undefined denominator, so the run is aborted and reported as invalid
  rather than scoring the query.
- **Dependency precision is defined over all 32 queries; recall and F1 over the 13
  dependency-related queries only.** On the other 19, `E(q) = ∅` makes recall `0/0` and
  undefined. Those queries still penalise a system that invents a dependency, via
  precision.
- **Empty-prediction convention for dependency precision (explicit, corrected 2026-09-28).**
  An empty prediction is not one rule but three:
  - `P(q) = ∅` and `E(q) = ∅` — **correct vacuous prediction**, precision 1.0 (the expected
    answer *is* "no dependencies"; this is desirable non-invention).
  - `P(q) = ∅` and `E(q) ≠ ∅` — **missed every dependency**, precision 0.0 and recall 0.0.
  - `P(q) ≠ ∅` — standard `TP/(TP+FP)`.
  A **failed run** contributes 0.0 to precision regardless of `E(q)` and is never counted
  as vacuous-correct. Consequence: an all-negative predictor scores precision `19/32 =
  0.594`, **not** 1.0, with recall 0.0 and F1 0.0; both are always reported together, and
  the vacuous-correct count is reportable. Implemented and tested in
  `src/evaluation/dependency_metrics.py` / `tests/test_dependency_metrics.py`. This
  supersedes the earlier convention under which an all-negative predictor scored 1.0.
- **A failed run is not a missing value.** It scores zero and stays in every denominator. A
  retriever that crashes on hard queries must not score better by dropping them.
- **A human rating never assigned is a missing value and is never imputed.** The denominator
  is printed with every mean, and above 10% missing, Layer B is reported as incomplete and
  not compared.
- **Ties are resolved at retrieval time**, by the frozen ascending-chunk-ID rule, so a
  metric is never computed over an order-ambiguous list.
- **MRR is defined and reported over all 32 queries.** Its numerator is problem-defined for
  the first ground-truth-relevant chunk in the ranked top-5 (else 0) and its denominator is
  1 per query, so no 13/32 ambiguity applies.

### D-010 — Two-layer evaluation; BM25 presents retrieved passages (APPROVED)

**Status:** APPROVED by the student 2026-09-28. Not frozen as code, but settled as design.

BM25 returns ranked passages and RAG returns a generated grounded answer. **The two output
forms are explicitly not identical and are not claimed to be**, and **no prose answer is
fabricated for BM25** to make the systems superficially symmetrical. The asymmetry is a
documented characteristic of the systems being compared.

Evaluation is therefore layered:

- **Layer A — retrieval comparison (like-for-like).** Precision@5, Recall@5, MRR and
  dependency retrieval accuracy, over the same corpus, the same 32 queries, the same ground
  truth and the same `k = 5`. Both systems return the same chunk objects, so this layer is a
  genuine like-for-like ranking comparison.
- **Layer B — user-facing decision support (not like-for-like).** Usefulness, clarity, trust
  and task completion time, rated on each system's real output: BM25's top-5 passages, RAG's
  generated answer with `[DOC-ID#Cn]` citations.

Layer B is explicitly not like-for-like, and a difference between layers is a difference in
**output capability**, not a like-for-like win. The confound this introduces — that BM25's
usefulness and clarity depend partly on the readability of the underlying documentation, and
that a user reconciling five passages unaided is a real cost of the keyword workflow — is
disclosed in the same sentence as the number, not removed. Detail: `docs/evaluation_metrics.md`
§0 and §7.1.

### D-011 — Ethics determination for human-rated metrics remains open (OPEN)

**Status:** OPEN. Reaffirmed 2026-09-28. No change to its substance.

**No assumption is made in either direction.** This decision does not record that ethics
approval exists, and it does not record that approval is unnecessary or that an exemption
applies. Both remain unestablished.

Consequences, all binding:

- **No human-participant data is collected.** No recruitment, no consent process, no
  participant responses, no participant-derived measurements of any kind.
- **Nothing begins until the NCI coordinator or the appropriate ethics process has
  determined what is required.** An unanswered determination is not a permission.
- **The technical BM25/RAG experiment must remain separable from any human-participant
  evaluation.** The technical experiment proceeds on its own terms and does not depend on,
  wait for, or share infrastructure with a participant study. If a participant study never
  happens, the technical results are unaffected.
- **If participant evaluation is later approved, it must evaluate the already-frozen
  technical system.** Changing the chunking configuration, the retrieval depth, the
  generation model, the prompt, the BM25 parameters or the metric definitions during
  participant testing would invalidate both the technical comparison and the participant
  data. Any such change is a new freeze with a new manifest version and a recorded protocol
  deviation.
- **Usefulness, clarity and trust are currently rated by the researcher** against the fixed
  5-point anchored scale in `docs/evaluation_metrics.md` §7, and that substitution is
  disclosed as a limitation. It is not presented as equivalent to participant evaluation,
  and it carries no claim of inter-rater reliability.

The Layer B user-facing metrics are therefore a **researcher-rating** result at this stage.
If participant evaluation is approved later, the two must be reported as distinct
evidences and never merged into a single score.

### D-012 — Reproducibility artefacts and hash specification (FROZEN)

**Status:** APPROVED AND FROZEN 2026-09-28. Specification: `docs/reproducibility.md`.
Implemented in `src/manifest/manifest.py` with `build`, `verify` and `status`.

Twelve artefacts, all SHA-256, all captured at the final experiment freeze into
`data/manifest/FREEZE.json` (authoritative) with a rendered `FREEZE.md`. For each: what is
hashed, the algorithm, when it is captured, where it is recorded, and whether it is
committed to Git or stored separately. Every one of the nine artefacts named by the
supervisor is covered; environment record, validation reports and run outputs are added.

Notable choices:

- **The embedding matrix is the operative reproducibility guarantee**, because no dated
  snapshot of `text-embedding-3-large` is published. Its positional `chunk_id_order` is
  hashed separately and stored alongside it, since a matrix without its row order is
  meaningless.
- **Tree digests are computed over sorted per-file digests**, so filesystem iteration order
  cannot change the value, and both the individual digests and an aggregate are recorded.
- **A dirty working tree invalidates a freeze** and is recorded as such in the manifest.
- **The manifest is verified, not trusted:** `python3 -m src.manifest.manifest --verify`
  recomputes every digest and fails on the first mismatch or if HEAD has moved, so a later
  silent edit to a frozen artefact is caught rather than discovered during write-up.
- **`.env` is never hashed into a committed manifest.** It holds a secret and is gitignored.
- Artefacts 1–10 are captured once at the freeze. Reaffirmed at approval: the embedding matrix hash is included; the matrix's positional `chunk_id_order` is hashed/recorded in the sidecar; the code commit is captured and a dirty working tree invalidates the freeze; dependency/environment information is captured via the lockfile and record; and `--verify` recomputes every hash rather than trusting stored values. `.env` and the actual API key are **never** included in any artefact or hash. A later run appends only its own run
  outputs under a new `run_id`; if a frozen input changes, that is a protocol deviation,
  not a re-freeze.

### D-013 — Final-corpus blockers found during freeze validation; two approved extensions (APPROVED 2026-09-28)

**Status:** APPROVED AND RECORDED. Amends the frozen `be92946` methodology by the two
changes the student approved after the final-corpus feasibility check surfaced them.

During pre-corpus validation, no corpus generation could satisfy three of the seven final
gates and one more gate had no rendering mechanism, entirely within the frozen definitions:

| Blocker | Gate | Root cause |
|---|---|---|
| Ordering cannot be expressed | Q-11 `explicit_dep_ordering` | Selectors match `"order" in dependency_type or "sequence" in dependency_type`; the closed `DependencyType` literal had no value containing either substring, so zero elements of the corpus's dependency set could ever satisfy the predicate. |
| Ordering cannot be expressed | Q-14 `implicit_dep_ordering` | same as above |
| Ordering cannot be expressed | Q-20 `cdr_prd_sequence` | same as above (matches on `"order"` specifically) |
| No approval-limit mechanism | Q-SUP-3 `current_spec_with_approval_limit` | The final corpus must contain a v1/v2 feature-spec pair whose stated approval limit differs. No schema field carried a limit and the renderer emitted no limit text, so the value could not be stated as a limit (the bare-number trap the selector explicitly rejects). |

**Approved changes (both in scope of the frozen experiment design; neither alters the
32-query spec, the dependency/distractor counts, or any configuration already frozen):**

1. **Dependency vocabulary extended:** `DependencyType` gains the value `ordering`
   (a stage/phase sequencing constraint). `source_model.py`, `DATA_DESIGN.md` §2.6.
   The existing selectors for Q-11/Q-14/Q-20 now have corpus content they can match on;
   selectors and query spec are unchanged. The mechanism sample is **unchanged** (it
   carries no ordering dependency), so the sample probe continues to report exactly the
   seven originally-recorded unmet corpus requirements.
2. **Feature specifications may state an approval limit:** `Feature` gains
   `approval_limit: str = ""`; `render_v1.py` renders a dedicated "Approval limit"
   section only when the field is set (current: "is"; superseded: "was"). The final
   corpus supplies a v1/v2 feature-spec pair with a changed value (Q-SUP-3). The
   mechanism sample sets no approval limit, so its rendered bytes are unchanged.

Neither change is a rerun or a tuning of any frozen number; both are data-model
extensions needed for the already-approved gate set to be satisfiable. Re-freeze is
recorded in a new commit that re-verifies the deterministic sample and the full suite
before final-corpus generation proceeds.

### D-014 — Frozen artefacts committed for the hosted prototype; manifest tracking correction (RECORDED 2026-11-06)

**Status:** RECORDED. No experimental or methodological change; no frozen configuration,
corpus, query, ground-truth or prompt content is altered. This entry exists so the
repository state change is traceable, per AGENTS.md §1 rule 15.

While preparing the Streamlit Community Cloud deployment of the interactive prototype
(no research change: deployment of the demonstration interface only), two traceability
gaps were discovered on the Desktop working copy:

1. `FREEZE.json` records the embedding matrix `data/embeddings/v1-corpus/embeddings.npy`
   (sha256 `cfdf5f13…`, status `ok`) with `committed_to_git: true`, but the file was in
   fact excluded from every commit by the gitignore rule `*.npy` — the manifest's claim
   was inconsistent with the repository for as long as that rule stood. The matrix is
   now committed (the `.gitignore` rule now carries an explicit exception); the recorded
   freeze hash is unaffected. Anyone replaying the freeze verification should re-verify
   hashes against their own checkout, as the manifest instructs.
2. The frozen Chroma persist directory `data/vectorstore/v1-corpus` (built from the
   frozen embedding matrix), designed "rebuildable", was not version-controlled. For the
   hosted prototype the exact store used by EXP-20260929-001 is preferable to a
   cloud-side rebuild (which would have re-embedded the corpus on Streamlit's
   infrastructure). The store is therefore committed (exception added to `.gitignore`).
   No frozen hash existed for this store in `FREEZE.json` (the frozen retrieval
   artefacts are the embedding matrix and its metadata sidecar); the committed copy is
   the on-disk store as used by the local prototype, whose embedded vectors are a copy
   of the frozen matrix.

The prototype code itself changed only in how it reads the API key (Streamlit Cloud
secrets vault first, local environment fallback) — retrieval, embedding, prompt,
generation and evaluation code paths are untouched.

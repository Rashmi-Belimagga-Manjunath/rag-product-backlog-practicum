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

| ID | Assumption | Status |
|---|---|---|
| A1 | B2B SaaS / HRTech is an appropriate synthetic domain | Unconfirmed |
| A2 | Fully synthetic documentation is acceptable in place of real artefacts | **Resolved by D9** — synthetic confirmed |
| A3 | A few hundred chunks is sufficient to observe a measurable difference | Unconfirmed — depends on D6 |
| A4 | Chunk size 1000 / overlap 200 remains appropriate | Unconfirmed — CA2 flags this as needing a pilot |
| A5 | Student intends to work ahead of the six-week schedule | Stated intention, not commitment |
| A6 | Ethics approval is not required for a fully synthetic corpus | **Unconfirmed — do not assume either way.** Being confirmed with the NCI coordinator/supervisor |
| A7 | The exact OpenAI embedding model name | Not yet selected. Must be frozen before the comparison runs |

---

## Still open

| ID | Decision | Blocks |
|---|---|---|
| D6 | Corpus scale and product count | Full corpus generation — **proposal presented, awaiting approval** |
| D7 | Query count, category distribution, difficulty definition | Query set — **proposal presented, awaiting approval** |
| D8 | UI framework (deprioritised, not decided) | App stage |
| A7 | Exact OpenAI embedding model | Experiment run — must be frozen before results |
| — | Whether ethics approval covers a synthetic-only corpus | Any statement about ethics in the write-up. Hard gate on all human-participant activity |

**Approved and closed:** D1, D2, D3, D4, D5, D9, Q4, Q5, Q6, Q7.


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

### D-005 — C6 as pre-specified cannot discriminate in a closed-domain corpus (PROPOSED)

**Status:** PROPOSED, requires approval. Not frozen.

The pilot comparison of 1000/200 and 600/100 on the long-document stress corpus passed
C1-C5, C7 and C8 for both configurations, and failed C6 for both. C6 as pre-specified uses
same-document word-type-bag containment > 0.9 to define a duplicate chunk.

Direct measurement shows the measure is unusable here. A ~1,000-token chunk drawn from a
closed-domain templated corpus contains only 143-169 distinct word types, so type-bag
containment approaches 1.0 by vocabulary saturation rather than by copying. Measured
maximum 8-gram containment of each chunk against every other chunk in the same document is
**0.0% at every threshold from 0.2 to 0.8, for every chunk, in both configurations.**

The criterion is therefore producing approximately 100% false positives and is
indistinguishable from the construct it was meant to measure. Proposed replacement:
same-document 8-gram containment > 0.5, fewer than 2% of chunks involved in such a pair.
Threshold derived from the construct-validity argument and the measured distribution, with
no retrieval or generation result involved. Under the proposal both configurations pass.

Full evidence and reasoning: `CHUNKING_DECISION.md`.

### D-006 — C1-C8 rank configurations; they do not select one (PROPOSED)

**Status:** PROPOSED, requires approval. Not frozen.

Once C6 is repaired, both 1000/200 and 600/100 pass all eight criteria. C1-C8 test that
chunking does not break documents; they are not designed to measure retrieval quality and
were never expected to separate two healthy configurations.

Selection therefore requires a tie-break that is **not** derived from BM25 or RAG
performance. Recommended: keep the already-approved 1000/200, since it introduces no new
parameter choice, yields 42 chunks rather than 63 (fewer vectors, lower cost, smaller
evaluation surface), and choosing the finer-grained configuration is a change that tends to
favour embedding retrieval.

### D-007 — RAG configuration proposals (PROPOSED, not frozen)

**Status:** PROPOSED, requires approval. Not frozen.

top-k 5 (matches the `@5` metric cutoff, ~1,700 token context, ~1.7% of the projected 289
chunks); `gpt-4o-mini` at temperature 0, max_tokens 800, n=1; machine-checkable
`[DOC-ID#Cn]` citations validated against the retrieval log. The system prompt must enforce
grounding, abstention, per-claim citation, no invented identifiers, superseded-version
awareness, advisory framing and no autonomous action. Prompt variants, temperature sweeps
and top-k sweeps are explicitly excluded, because selecting among them would turn this into
an optimisation exercise rather than a controlled comparison. Detail: `docs/rag_configuration.md`.

### D-008 — BM25 configuration (PROPOSED, not frozen)

**Status:** PROPOSED, requires approval. Not frozen.

k1 1.5, b 0.75 (Robertson & Zaragoza 2009 defaults), Lucene non-negative IDF, chunk-level
retrieval, lowercase with Unicode word tokenisation, no stemming and no stopword removal
inside the retriever. Queries are used verbatim with no expansion or rewriting. Ties break
on ascending chunk ID. BM25 may not be tuned, re-ranked or query-expanded after results are
visible, since that would convert a traditional baseline into a fitted competitor. Detail:
`docs/bm25_configuration.md`.

### D-009 — Evaluation metrics and the retrieval/generation error split (PROPOSED)

**Status:** PROPOSED, requires approval. Not frozen.

Precision@5, Recall@5, MRR, dependency accuracy (TP/FP/FN over dependency IDs, split by
explicitness), and task completion time (3 runs, median, A/B interleaved, warm-up
discarded, retrieval-only latency logged separately so RAG's generation cost is not hidden).

Every dependency error is classified as a **retrieval error** (relevant chunk was in the
top-5) or a **generation error** (it was not), by checking the retrieval log for that
query. Fabricated dependencies and fabricated citations are counted separately, since they
are worse than wrong inference.

Relevance is assigned by provenance from the source model, never by query-to-chunk text
similarity: a text-similarity label would be a second unstated retrieval model inside the
scoring and would favour the embedding system by construction. Detail:
`docs/evaluation_metrics.md`.

### D-010 — BM25 answer presentation is unresolved (OPEN)

**Status:** OPEN, requires a decision. Not frozen.

BM25 returns ranked passages, not prose, so usefulness, clarity and trust cannot be compared
across the two systems unless BM25 is given a user-facing artefact. Recommended: present the
top-5 passages as the BM25 response and disclose that this measures documentation
readability as well as system usefulness. The alternatives (RAG-only generation metrics, or
adding an extractive summariser to the baseline) are weaker in different ways and are set
out in `docs/evaluation_metrics.md` section 8.1.

### D-011 — Ethics determination for human-rated metrics remains open (OPEN)

**Status:** OPEN. No change.

Usefulness, clarity and trust are rated by the researcher against a fixed anchored rubric
and disclosed as a limitation. No participant data is collected. Whether a formal
determination is required from the NCI coordinator or supervisor is still unanswered, and
neither its answer nor its absence may be assumed.

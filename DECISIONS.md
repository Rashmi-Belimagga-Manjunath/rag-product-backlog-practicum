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


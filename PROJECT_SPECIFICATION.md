# Project Specification

**Project:** Retrieval-Augmented AI Assistants for Product Documentation Analysis:
Supporting Data-Driven Product Backlog Decisions

**Student:** Rashmi Belimagga Shetty Manjunath (24323870)
**Programme:** MSc in Artificial Intelligence for Business, National College of Ireland, 2026
**Module:** Practicum (Final) — MSCAIBUSJAN26I
**Supervisor:** Prof. Namita Agarwal
**Status:** Checkpoint 1 — specification and data design. No dataset generated, no experiment run.

---

## 1. Research question (fixed)

> **To what extent does a Retrieval-Augmented Generation (RAG) AI assistant improve the
> efficiency, relevance, and accuracy of product backlog analysis compared to
> traditional keyword-based documentation search systems?**

This question is carried forward from CA1 and was explicitly retained in its original
form following supervisor feedback on CA1. **It must not be changed** without explicit
instruction from the student.

---

## 2. Research context

Product managers work with large, fragmented volumes of product documentation:
Product Requirements Documents (PRDs), feature specifications, user stories /
Product Backlog Items (PBIs), and related technical and decision documentation.

This material accumulates across sprints, releases, and teams. Locating the specific
information needed for a prioritisation decision becomes progressively harder, and
keyword-based search — which underpins most enterprise documentation tools — matches
surface terms rather than meaning. A query about *"onboarding delays"* will not
retrieve a document discussing *"new-user activation friction"*, even though the two
describe the same problem. Product managers therefore fall back on manually reading
multiple sources: slow, and increasingly likely to miss a dependency, a prior decision,
or a conflicting requirement.

Retrieval-Augmented Generation (RAG) offers one technical response — retrieve
semantically relevant passages, then generate a response grounded in them rather than
in the model's parametric knowledge.

---

## 3. Research gaps (as established in CA1 — do not add to this list)

1. **Limited application of RAG in product-management contexts.** RAG research is
   concentrated in customer support, open-domain QA, and general knowledge management.
   Little has examined product documentation analysis or backlog decision support.

2. **Lack of decision-support focus.** Most RAG evaluation stops at retrieval metrics
   (Precision@k, Recall@k, MRR). Little evidence exists on whether AI-assisted
   retrieval supports higher-order tasks: backlog interpretation, dependency
   identification, prioritisation reasoning.

3. **Insufficient human-in-the-loop evaluation.** Most RAG systems are evaluated with
   automated benchmarks. There is little work on how practitioners actually engage with
   these systems, or whether they improve efficiency and perceived usefulness while
   preserving appropriate human oversight.

---

## 4. Research objectives

The evaluation investigates:

1. Retrieval relevance and coverage
2. Ranking quality
3. Dependency / context accuracy
4. Task completion efficiency
5. Perceived usefulness
6. Clarity
7. Trust

**Automated metrics:** Precision@5 · Recall@5 · Mean Reciprocal Rank (MRR) ·
Dependency accuracy

**Human-centred measures** (usefulness, clarity, trust) — **gated on ethics approval.**

---

## 5. Systems under comparison

Both systems operate over the **same corpus**, the **same query set**, and the **same
evaluation tasks**. This is the controlled comparison at the heart of the design.

### System A — Keyword baseline

```
documents → pre-processing → BM25 index → query → ranked results → top-k
```

- Standard BM25, with `k1` and `b` parameters recorded in the experiment log.
- **No LLM anywhere in this system.** Not for ranking, not for summarising, not for
  reranking.
- Must be independently runnable and independently evaluable.

*Parameter values for `k1`/`b` are an open decision — see §11.*

### System B — RAG assistant

```
documents → pre-processing → chunking → embeddings → vector store
          → query → semantic retrieval (top-k) → retrieved context
          → LLM → grounded answer + inline source citations
```

> **Implementation note (D-001).** The *architecture* above is unchanged from CA2. The
> *orchestration* is implemented in native Python rather than Flowise, as decided and
> approved by the student before any experiment was run. This is an implementation-level
> deviation, not a change to the research design, and must be disclosed as such in the
> write-up. See `DECISIONS.md` D-001.
>
> Native Python was chosen because the contribution is a controlled empirical
> comparison, which requires reproducible retrieval logging, versioned prompts,
> configurable experiments, and clean separation of retrieval from generation.

- Chunking: recursive text splitter, **chunk size 1000, overlap 200** (carried forward
  from CA1). Chunking strategy is treated as a *configurable parameter*, not a fixed
  design choice, and will be piloted against at least two strategies before being
  committed — motivated by the findings of Merola & Singh (2025) and Kreileder et al.
  (2026) discussed in CA2 §2.9.
- Retrieval: cosine similarity, **top-k = 5** (carried forward from CA1).
- Generation model: **GPT-4o-mini** (carried forward from CA1/CA2).
- Every generated claim carries an inline citation back to a specific source chunk.
- The system is **advisory**. It does not make, record, or autonomously alter backlog
  decisions. The product manager retains final authority.

### The one point where System B may answer and System A may not

To keep the comparison honest, the comparison operates at the **retrieval layer** as
the primary controlled comparison (P@5, R@5, MRR, dependency accuracy are all
retrieval-layer metrics). Generation quality and human-perception measures
(usefulness, clarity, trust) are reported **separately and explicitly labelled as
System-B-only**, because there is no System A counterpart. This asymmetry will be
stated in the write-up rather than glossed over.

---

## 6. Synthetic corpus

Confidential organisational documentation is not available for this research. A
**controlled synthetic product-management documentation corpus** will be used,
generated from a structured source-of-truth model rather than free-form.

Design is specified in `DATA_DESIGN.md`. Summary of the required properties:

- Generated from a structured product model, not written freely.
- Ground truth derived **from the model**, not from parsing generated prose.
- **Structurally heterogeneous** — long formal PRDs *and* short informal backlog items.
- **Deliberate lexical divergence** between query phrasing and document phrasing.
- Contains **distractors** — topically adjacent but non-relevant documents.
- Carries metadata (doc id, type, date, ticket ref, product, version) for traceability.

*Corpus scale, the number of products, and the balance between formal and informal
documentation are open decisions — see §11.*

---

## 7. Query set and ground truth

Queries represent realistic product-management documentation analysis tasks.
Categories under consideration:

- information retrieval
- feature / context understanding
- dependency identification
- cross-document reasoning
- conflict identification
- backlog-related analysis

Each query carries explicit ground truth where applicable:

```
query_id · query · query_type
relevant_document_ids · relevant_chunk_ids
expected_dependencies · expected_answer_elements
```

Ground truth is traceable to the structured synthetic source.

> **Query count, category distribution, and per-category allocation are NOT yet
> fixed.** An initial working range of roughly 20–30 queries is a starting point, not
> a commitment. The rationale and final distribution require the student's approval
> before the query set is built, because it materially affects methodology.

---

## 8. Evaluation methodology

Mixed-methods, **within-subject** comparison, counterbalanced order to control for
learning effects.

### Automated layer (both systems)

| Metric | Definition | Notes |
|---|---|---|
| Precision@5 | Proportion of top-5 retrieved items that are relevant | Manning et al. (2008) |
| Recall@5 | Proportion of all relevant items captured in top-5 | Manning et al. (2008) |
| MRR | Mean of the inverse rank of the first relevant result | Manning et al. (2008) |
| Dependency accuracy | Generated dependency claims checked against the known dependency map from the source model | Addresses hallucination risk (Ji et al., 2023) |

Retrieval and generation quality are reported as **separate outcomes**, never blended
into a single score.

### Task-completion time (separate experiment)

Requires the human task experiment. Participants complete identical backlog-analysis
tasks using each system, in counterbalanced order. **Not part of the automated run.**

### Human evaluation — gated

Usefulness, clarity, trust via a short adapted System-Usability-Style instrument plus
Likert items and brief semi-structured feedback.

**Blocked pending ethics approval.** No participant recruitment or session may proceed
before approval is granted. This is a hard gate in the plan.

---

## 9. Interpretation rules

- The evaluation must not assume RAG outperforms BM25. All four outcomes (§ below) are
  valid.
- A negative or null result is a legitimate and useful contribution — the literature
  currently offers no empirical basis either way for this specific application.
- Metric definitions must match the classical formulations in Manning et al. (2008) so
  results are comparable to the wider IR literature.
- Where corpus structure plausibly moderates the result, that will be reported
  explicitly rather than averaged away (see `DATA_DESIGN.md` §7).

---

## 10. Traceability

Every run records dataset version, query-set version, ground-truth version, embedding
model, generation model, chunking strategy / size / overlap, top-k, prompt version,
library versions, timestamp, random seeds, and full configuration.

Results are written to `results/<EXPERIMENT_ID>/` and are **never overwritten**.
`EXPERIMENT_LOG.md` is append-only. Methodological decisions are recorded in
`DECISIONS.md`.

---

## 11. Decision status

Decisions D1, D2, D4, D5, D8, D9 and the rendering question were **ratified by the
student on 2026-09-27**, before any experiment was run. See `DECISIONS.md` D-001.

| # | Decision | Status |
|---|---|---|
| D1 | Orchestration | ✅ **Native Python.** CA2 named Flowise; recorded as an implementation deviation to disclose. Architecture unchanged. |
| D2 | Embedding model | ✅ **OpenAI embeddings**, as in CA1/CA2. Must not change after seeing results. |
| D3 | Vector store | ⏸ **Recommendation prepared, awaiting sign-off** — see §11.1 |
| D4 | BM25 implementation | ✅ **Standard implementation.** |
| D5 | BM25 `k1` / `b` | ✅ **k1 = 1.5, b = 0.75**, fixed before the comparison. Must not be tuned after seeing RAG results. |
| D6 | Corpus scale | ⏸ Deferred until the source model exists. Proposal to follow. |
| D7 | Query count and distribution | ⏸ Deferred. Proposal to follow, then approval required. |
| D8 | App framework | ✅ **Deprioritised.** Pipeline first, UI later. |
| D9 | Real artefacts | ✅ **None.** Fully synthetic. Must be documented as a threat to external validity. |
| — | Ethics approval for synthetic corpus | ⏸ Open. Do not assume either way. |
| — | Human evaluation | 🔒 **Blocked** until ethics approval confirmed. No recruitment, no participant data. |

### 11.1 Vector store — Chroma (D3, approved)

**Decision: Chroma, with an exact-NumPy cross-check used as a validation test.**

Chroma was approved because it satisfies every requirement the logging design places on
the retrieval layer, runs locally, and matches the "vector database" committed in CA2
§3.4 without needing a further deviation.

#### Required properties, all of which the implementation must preserve

| Property | Why it matters for the research |
|---|---|
| Stable document IDs | A recorded result must be checkable against a later run |
| Stable chunk IDs | Ground truth is attached at chunk level by provenance; unstable IDs break that |
| Metadata | Needed to report by document type, product, version, and supersession status |
| Retrieval scores | Required for reproducible ranking inspection |
| Retrieval ranking | Required for MRR, and for distinguishing retrieval from generation failure |
| Source-document traceability | Inline citations are a design-level interpretability measure (Shneiderman 2020, cited in CA2 §2.7) |

#### The exact-NumPy cross-check

**Purpose: validation only.** It detects retrieval and indexing anomalies, so that a
vector-store implementation fault can be distinguished from genuine embedding or model
behaviour.

**Hard constraint:** the cross-check must **never** be used to alter, correct, adjust or
tune experimental results. It is a diagnostic, not a correction step. If it disagrees
with Chroma, that is a finding to be reported and investigated — not a discrepancy to
be silently resolved in favour of whichever number looks better.

**Method.** For the retrieval layer, compute cosine similarity directly in NumPy from
the stored embedding matrix and compare against Chroma's returned ordering:

1. A test asserts that the **set** of top-k chunk IDs returned by Chroma equals the set
   computed by exact NumPy cosine similarity for the same query embedding.
2. A test asserts that the **ordering** matches, where Chroma returns a distance that
   is a monotone function of cosine similarity.
3. A test asserts that every returned score is finite, and that scores are consistent
   with the embedding matrix (no stale or duplicated IDs).

**Why exact NumPy is a valid reference at this scale.** The corpus is small enough
(hundreds of chunks) that brute-force cosine similarity is exact and instantaneous.
There is no approximate-nearest-neighbour index in play, so "exact" genuinely means
exact. At a scale where ANN indexing was required, this reference would weaken — that
is a limitation to disclose, not a problem now.

**If the tests fail:** the run is invalid until the fault is understood. A retrieval
anomaly caused by the store is not a result about RAG, and reporting it as one would be
a false finding.

---

---

## 12. Assumptions currently in force

These are **assumptions, not facts.** They are unconfirmed and remain open.

- A1 — A B2B SaaS / HRTech domain is an appropriate synthetic scenario. Basis: CA2
  §3 discusses B2B SaaS / HRTech as a comparison domain. *Unconfirmed as the chosen
  scenario.*
- ~~A2 — Fully synthetic documentation is acceptable~~ → **Resolved by D9: confirmed
  synthetic, no real artefacts.** The corresponding obligation is to document the
  synthetic corpus as a threat to external validity.
- A3 — A corpus of a few hundred chunks is sufficient to observe a measurable
  difference between the two systems. *Unconfirmed; depends on D6.*
- A4 — Chunk size 1000 / overlap 200 remains appropriate. Carried forward from CA1 but
  flagged in CA2 as something to pilot rather than assume. *Unconfirmed.*
- A5 — The student intends to work ahead of the published six-week schedule. Stated as
  an intention, not a commitment.
- A6 — **Whether ethics approval is required for a fully synthetic corpus is unknown
  and must not be assumed in either direction.** The human evaluation is separately and
  unconditionally blocked until approval is confirmed.

Each of these must be either confirmed or replaced before the corpus is generated.


---

## 13. Scope exclusions

This project is **not** a Jira replacement, an autonomous product manager, an
autonomous prioritisation system, a new RAG algorithm, a production enterprise
deployment, or a general-purpose chatbot.

The contribution is primarily **empirical**: implement and evaluate a RAG-based
product-documentation assistant against a controlled keyword/BM25 baseline, and
establish where — if anywhere — it provides measurable benefit for product backlog
analysis.

Secondary contributions, as framed in CA1/CA2:

- a **reusable evaluation protocol** (labelled query set, ground-truth relevance
  judgments, dependency map, usability instrument) adaptable by later work;
- an explicit account of **threats to validity**, intended to make the limits of the
  empirical claim as clear as the claim itself.

---

## 14. Source documents this specification derives from

- `Practicum_CA1 submission.pdf` — research problem, gaps, question, objectives
- `Practicum CA2 Submission.docx` — literature review, methodology, architecture, evaluation design, risks, validity
- `architecture diagram.drawio.pdf` — system design diagram
- `From-Problem-to-Prototype.pptx` — progress deck, evaluation framework, roadmap
- `21 Sept-Practicum - Weekly Activity Report Template.docx` — week commencing 24 September 2026, supervisor feedback

No content in this specification has been invented. Where CA1/CA2 were silent, this
document records the gap as an open decision rather than filling it.

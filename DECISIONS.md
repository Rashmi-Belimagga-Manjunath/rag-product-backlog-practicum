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

#### D3 — Vector store: recommendation pending approval

See `PROJECT_SPECIFICATION.md` §11. Recommendation recorded, awaiting sign-off.

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
| A6 | Ethics approval is not required for a fully synthetic corpus | **Unconfirmed — do not assume either way** |

---

## Still open

| ID | Decision | Blocks |
|---|---|---|
| D3 | Vector store choice (recommendation prepared, needs sign-off) | Retrieval stage |
| D6 | Corpus scale and product count | Full corpus generation |
| D7 | Query count and category distribution | Query set — **requires approval** |
| D8 | UI framework (deprioritised, not decided) | App stage |
| — | Whether ethics approval covers a synthetic-only corpus | Any statement about ethics in the write-up |

# Retrieval-Augmented AI Assistants for Product Documentation Analysis

**Supporting Data-Driven Product Backlog Decisions**

An implementation and empirical evaluation of a Retrieval-Augmented Generation (RAG)
assistant for product documentation analysis, benchmarked against a traditional
BM25 keyword-search baseline over an identical corpus and query set.

MSc in Artificial Intelligence for Business · National College of Ireland · 2026
Module: Practicum (Final) · Supervisor: Prof. Namita Agarwal

**Local:** `~/Desktop/RAG-Practicum` (primary working copy)
**GitHub:** https://github.com/Rashmi-Belimagga-Manjunath/rag-product-backlog-practicum (private)

> The submitted CA1/CA2 documents, architecture diagram, progress deck and weekly
> report template are kept on the Desktop but are **not** committed — they contain your
> student ID, student email, and an Academic Integrity Certificate verification code.
> See `docs/excluded_source_material.md`.


---

## Status

**Checkpoint 1 complete — specification stage. Nothing is implemented yet.**

No dataset has been generated. No retrieval system has been built. No experiment has
been run, and **no results exist**. This is deliberate: the evaluation protocol and the
data design are fixed and recorded *before* any system runs, so that later claims of
methodological integrity are credible.

| Phase | Status |
|---|---|
| 1. Specification, data design, governance | ✅ Complete |
| 2. Technology decisions | ⏸ Awaiting student approval |
| 3. Synthetic corpus generation | ⏸ Blocked on decisions |
| 4. Baseline (BM25) | ⏸ Blocked on decisions |
| 5. RAG pipeline | ⏸ Blocked on decisions |
| 6. Automated evaluation | ⏸ Blocked |
| 7. Human evaluation | 🔒 Blocked pending ethics approval |
| 8. Analysis and write-up | ⏸ Blocked |

---

## Read these first

| Document | What it is |
|---|---|
| `AGENTS.md` | Operating rules. Research integrity rules, controlled-comparison rules, traceability requirements, working style. |
| `PROJECT_SPECIFICATION.md` | Research question, objectives, systems A and B, evaluation methodology, scope, open decisions, assumptions. |
| `DATA_DESIGN.md` | The structured synthetic product model. How the corpus, queries, and ground-truth labels are derived from one source of truth. |
| `DECISIONS.md` | Methodological decision log. Open decisions, open assumptions, decisions taken. |
| `EXPERIMENT_LOG.md` | Append-only record of every experiment run. Currently empty. |

---

## The research question

> To what extent does a Retrieval-Augmented Generation (RAG) AI assistant improve the
> efficiency, relevance, and accuracy of product backlog analysis compared to
> traditional keyword-based documentation search systems?

Carried forward unchanged from CA1, following supervisor feedback. Not to be modified.

---

## The experiment, in one paragraph

Product managers rely on fragmented documentation — PRDs, feature specs, backlog items,
tickets. Keyword search matches words, not meaning, so a query about *"onboarding
delays"* misses a document about *"new-user activation friction"*. This project builds
a RAG assistant that retrieves semantically and generates a cited, grounded answer,
and compares it against a BM25 keyword baseline. Both systems use the **same
synthetic corpus**, the **same query set**, and the **same tasks**. The comparison is
measured with Precision@5, Recall@5, MRR, and dependency accuracy, with task
completion time and human judgements of usefulness, clarity, and trust measured
separately.

The evaluation does **not** assume RAG will win. A negative or null result is a
legitimate contribution.

---

## Why the corpus is synthetic, and why it is structured

Real company documentation is confidential, so a synthetic corpus is used. But
generating documents freely and then grading an LLM against other LLM output would
measure the generator, not retrieval.

Instead there is a single **structured product model** — products, features, PBIs,
technical components, dependencies, documents, conflicts — written as data first.
Documents are then *rendered* from that model. Queries are written against the model.
Ground truth is read directly off the model.

```
Structured Product Model
        ↓
Ground-Truth Relationships
        ↓
Synthetic Documentation
        ↓
Query Set
        ↓
Ground-Truth Evaluation Labels
        ↓
BM25 + RAG Experiment
```

Full design in `DATA_DESIGN.md`. The two design elements that matter most:

- **Lexical divergence.** Documents and queries deliberately use different vocabulary
  for the same concept, stratified into easy / moderate / hard. Without this, BM25
  scores well and the experiment does not test its own question. The divergence pattern
  is fixed before any system runs and is never adjusted afterwards.
- **Heterogeneity and distractors.** Long formal PRDs alongside three-line meeting
  notes; superseded document versions left in the repository; topically adjacent
  non-relevant documents, so Precision@5 is not trivially 1.0.

---

## Project structure

```
RAG- Practicum/
├── AGENTS.md                  # operating rules
├── PROJECT_SPECIFICATION.md   # research question, systems, evaluation design
├── DATA_DESIGN.md             # structured synthetic product model
├── DECISIONS.md               # methodological decision log
├── EXPERIMENT_LOG.md          # append-only run record
│
├── data/
│   ├── raw/                   # any source material (currently empty)
│   ├── processed/             # pre-processed documents
│   ├── synthetic/
│   │   ├── source_model/      # THE structured source of truth
│   │   └── documents/         # documents rendered from it
│   ├── queries/               # evaluation query set
│   ├── ground_truth/          # labels derived from the source model
│   └── versions/              # MANIFEST.json — version + hash registry
│
├── src/
│   ├── data_generation/       # builds the source model; renders documents
│   ├── preprocessing/         # cleaning, chunking, provenance propagation
│   ├── bm25/                  # System A — keyword baseline
│   ├── embeddings/            # embedding generation
│   ├── vectorstore/           # vector index
│   ├── retrieval/             # shared retrieval interface
│   ├── rag/                   # System B — generation with citations
│   ├── evaluation/            # P@5, R@5, MRR, dependency accuracy
│   └── common/                # config, logging, versioning helpers
│
├── experiments/               # experiment configs / driver scripts
├── results/                   # results/EXP-YYYYMMDD-NNN/ — never overwritten
├── app/                       # end-user prototype interface
├── tests/                     # unit tests, especially for metric implementations
├── docs/                      # additional documentation
├── notebooks/                 # exploratory analysis
│
├── requirements.txt           # (provisional — pending technology decisions)
└── README.md
```

### Why `data/synthetic/` is split in two

`source_model/` and `documents/` are separate because ground-truth labels must come from
the structured model, not from re-reading generated prose. That separation has to be
enforced by the folder layout, otherwise the derivation path becomes unverifiable after
the fact. See `DECISIONS.md` D-000.

---

## Setup

**Not yet available** — dependencies are not pinned, because the technology decisions
in `DECISIONS.md` are still open. Once approved, this section will carry exact
install and run commands.

Environment verified so far: Python 3.14.2 on macOS. A dry-run resolution check
confirmed that the candidate packages (`openai`, `chromadb`, `bm25s`, `numpy`, `pandas`,
`streamlit`, `pytest`) all have compatible distributions available. There is no
environment blocker.

---

## What still needs your decision

Nine implementation decisions and eight data-design questions are open. The ones that
block the next phase of work:

1. **Orchestration** — CA2 committed to Flowise. Flowise is a no-code GUI, which makes
   prompt versions and retrieval state hard to log and hard to reproduce. Native Python
   would be more traceable but deviates from the committed design. Your call — I will
   not silently drop Flowise.
2. **Embedding model** — CA1/CA2 committed to OpenAI embeddings. A local open-weights
   model would be free, offline, and deterministic. Different reproducibility
   trade-off.
3. **Corpus scale and query distribution** — the query count and category spread
   materially affect methodology, so they need your explicit approval before the query
   set is built.
4. **Rendering approach** — pure templates (reproducible, less natural prose) vs
   LLM-assisted prose (natural, still model-grounded, less deterministic).

All options with recommendations are in `PROJECT_SPECIFICATION.md` §11 and
`DATA_DESIGN.md` §11.

---

## Research integrity

The rules in `AGENTS.md` §1 are binding on any assistant or contributor working on this
repository. In summary: no invented results, no fabricated citations, no adjusting
ground truth to favour a system, no removal of negative results, no silent change of
the research question, and no presenting assumptions as facts.

If something cannot be verified from the available project information, the correct
response is to say so — not to fill the gap.

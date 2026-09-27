# AGENTS.md — Operating Rules for AI Assistants on This Project

**Project:** Retrieval-Augmented AI Assistants for Product Documentation Analysis:
Supporting Data-Driven Product Backlog Decisions

**Student:** Rashmi Belimagga Shetty Manjunath (24323870)
**Programme:** MSc in Artificial Intelligence for Business, National College of Ireland
**Module:** Practicum (Final), MSCAIBUSJAN26I
**Supervisor:** Prof. Namita Agarwal

---

## 0. What this project is

This is the **implementation and empirical evaluation** stage of a research direction
already established in CA1 and CA2. It is **not** a new research project.

Anything that would change the research question, scope, methodology, or evaluation
design is out of scope for autonomous work. If code, a library constraint, or a
convenience appears to require it, that is a signal to stop and ask — not a licence
to change the design.

---

## 1. Research integrity rules (mandatory, non-negotiable)

1. **NEVER** invent experimental results.
2. **NEVER** invent participant results.
3. **NEVER** fabricate citations or academic references.
4. **NEVER** claim an experiment was conducted when it was not.
5. **NEVER** claim a metric was calculated if the underlying data does not exist.
6. **NEVER** modify ground truth to improve system performance.
7. **NEVER** remove, hide, soften, or omit negative or null results.
8. **NEVER** silently change the research question.
9. **NEVER** silently introduce a new research objective.
10. **NEVER** present assumptions as established facts.
11. **NEVER** invent external datasets, papers, APIs, benchmarks, or documentation.
12. If an external source is required, identify it explicitly and ask the student to
    verify/approve it.
13. If something cannot be verified from available project information, say exactly:
    *"I cannot verify this from the available project information."*
14. If requirements conflict, **STOP and ask**.
15. Keep a durable record of important methodological decisions (see `DECISIONS.md`).

### The bias rule that governs everything

The experiment must not assume RAG will outperform BM25. All of these are valid,
publishable outcomes:

- RAG outperforms
- BM25 outperforms
- Mixed / query-type-dependent results
- No meaningful difference

**Never** manipulate the corpus, queries, ground truth, prompts, chunking, or metric
definitions to produce a preferred result. This includes the subtler failure mode of
quietly tuning the corpus *after* seeing which side wins.

---

## 2. The controlled comparison (do not break this)

System A (BM25) vs System B (RAG). Both **MUST** use:

- the **same** documentation corpus
- the **same** query set
- the **same** evaluation tasks
- the **same** pre-processing of source documents

If any of these diverge, the comparison is invalid and the run must be discarded,
not reported with a caveat. Ask the student before changing any of them.

The baseline contains **no LLM**. Do not add one unless explicitly instructed.

---

## 3. Keep retrieval and generation separate

The research design requires distinguishing:

1. whether the correct information was **retrieved**, and
2. whether the LLM generated a **correct answer from** what was retrieved.

Therefore:

- Retrieval results must be inspectable independently of the generated answer.
- Retrieval and generation metrics must be computed and reported separately — never
  blended into a single score.
- A retrieval failure and a generation failure have different causes and different
  remedies. Preserve the distinction in code, logs, and reporting.

### Every retrieval/generation run must log

`query_id`, `query`, `retrieved_chunk_ids` (in rank order), `retrieval_scores`,
`retrieval_system`, `generated_answer`, `source_citations`, and the metadata needed
for evaluation (document id, doc type, section, date, ticket ref).

---

## 4. Synthetic data rules

The corpus is generated from a **structured source of truth**, never free-form.

```
Structured Product Model
        ↓
Ground-Truth Relationships
        ↓
Synthetic Documentation (rendered from the model)
        ↓
Query Set
        ↓
Ground-Truth Evaluation Labels (derived from the model)
        ↓
BM25 + RAG Experiment
```

- Ground truth is derived from the **structured model**, never by parsing the rendered
  documents. If labels can only be obtained by reading generated prose, the label is
  not trustworthy.
- Do not evaluate AI-generated answers against other AI-generated answers.
- The corpus must be **structurally heterogeneous**: long, formal PRDs *and* short,
  informal backlog items. A uniformly-formatted corpus would flatter both systems and
  misrepresent the real problem.
- The corpus must contain **deliberate lexical divergence** between how documents
  phrase things and how queries phrase things. Without this, keyword search scores
  artificially high and the experiment does not test what it claims to test. See
  `DATA_DESIGN.md` §6.
- The corpus must contain **distractors** — topically adjacent but non-relevant
  documents — otherwise Precision@5 is trivially high and uninformative.
- Any real-world prior knowledge of the student is used only as *inspiration for the
  synthetic scenario*, never as a source of confidential content.

---

## 5. Traceability requirements

Every experiment must be reproducible. Record at minimum:

dataset version · query-set version · ground-truth version · embedding model ·
generation model · chunking strategy · chunk size · overlap · retrieval top-k ·
prompt version · library versions · experiment timestamp · random seeds ·
configuration parameters

- **Never overwrite previous results.** Write each run to
  `results/EXP-YYYYMMDD-NNN/`, containing four subfolders:
  - `raw/` — unmodified per-query records exactly as emitted
  - `processed/` — derived artefacts (joined metrics, aggregations)
  - `tables/` — reportable tables
  - `figures/` — reportable charts
- Experiment ID format: `EXP-YYYYMMDD-NNN`.
- Any change to the corpus, queries, or ground truth **increments its version**
  (`v1`, `v2`, …) and is logged in `DECISIONS.md`. Old versions stay on disk.
- If a run used stale cached artefacts, say so in the log.

---

## 6. Experiment log

`EXPERIMENT_LOG.md` is append-only. Every run records:

Experiment ID · Date · Purpose · Configuration · Dataset version · Query-set version ·
Model configuration · Results · Observations · Known limitations

If a run fails or is abandoned, log that too. Abandoned runs are data.

---

## 7. Working style — checkpoint discipline

**Do not build everything at once.** At the start of each major phase, state:

1. what you intend to build
2. why it is needed and how it serves the research question
3. assumptions being made
4. anything requiring the student's approval

Then implement **only that phase**, test it, show the result, and **wait for
confirmation** before any major methodological change.

Stop and ask whenever uncertainty could affect research validity.

---

## 8. Code style (the student is not a programmer)

The student came from a product-management background. Write accordingly.

- Modular. One clear responsibility per module.
- Descriptive file names and variable names. No clever abbreviations.
- Comments where they genuinely aid understanding — especially explaining *why* a
  design choice was made, not restating what the code does.
- Avoid unnecessary complexity and abstraction.
- Do not introduce technologies that are not needed. A simpler solution that a
  non-programmer can follow is strictly better here.
- Clear error messages. Never fail silently.
- Tests for important functions, especially metric implementations.
- Explain major implementation decisions in `README.md` / `docs/`.

A research prototype that the student cannot explain to their supervisor is worthless.
Optimise for inspectability over cleverness.

---

## 9. Scope limits

This project is **not**:

- a Jira replacement
- an autonomous product manager
- an autonomous prioritisation system
- a new RAG algorithm
- a production enterprise deployment
- a general-purpose chatbot

The assistant is **advisory**. It surfaces context, candidates, and dependencies.
The product manager retains every decision.

---

## 10. Assumptions register

Anything assumed but not confirmed by the student is recorded in `DECISIONS.md` under
**Open assumptions**, and repeated in the write-up until resolved. An assumption
promoted to a fact without confirmation is an integrity failure.

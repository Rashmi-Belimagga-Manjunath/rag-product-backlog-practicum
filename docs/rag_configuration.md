# RAG Configuration

**Status: FROZEN (D-007, approved 2026-09-28).** This document is the configuration of
record. Frozen only by explicit approval, **before** any comparative result is examined;
the machine-readable location of record is `experiments/configs/rag_config.json` and the
prompt is `experiments/configs/rag_prompt.txt` (SHA-256 `7ab1534…`).

Every value below is proposed with a rationale that is *independent of retrieval
performance*. If a value is ever changed after results are visible, the experiment is no
longer a controlled comparison, and the change must be reported as a protocol deviation.

---

## 1. Retrieval depth: `top_k = 5`

**Proposed: 5 chunks.**

| Consideration | Reasoning |
|---|---|
| Matches the evaluation cutoff | Precision@5, Recall@5 and MRR are all defined at `@5`. Retrieving 5 makes the system and the metrics describe the same object. Retrieving 20 and scoring the top 5 would mean the 6th-20th chunk changed the answer without being measured. |
| Bounded generation context | ~5 chunks x ~250 words is roughly 1,250 words, about 1,700 tokens. That fits a generation context with room for instructions and output, without truncation. |
| Matches the approved chunk projection | ~289 projected chunks. Top-5 is ~1.7% of the corpus - selective enough to be a real ranking test, not so small that a single bad document dominates. |
| Corresponds to a reviewable set | Five chunks is roughly one screen of evidence. It matches the "evidence a person would read" framing of the research question. |

**Considered and rejected:** `k=3` (too little context for cross-document queries, which is
where RAG's advantage is expected to show); `k=10` (bigger context, but Recall@5 would then
depend on a ranking the metrics never see, and a weaker answer could be hidden at ranks
6-10).

**This is a pre-registered choice.** It is not revisited after seeing results.

---

## 2. Generation model: `gpt-4o-mini`

**Proposed: `gpt-4o-mini`.** Verified available on the account API on 2026-09-28.

| Consideration | Reasoning |
|---|---|
| Cost | At roughly 1,700 input + 400 output tokens x 32 queries x 3 runs, generation cost is well under $1. Cost is not a constraint and does not motivate a smaller model. |
| Determinism at temperature 0 | Supports a reproducible, low-variance generation step, which matters when a single run is compared against a deterministic baseline. |
| Representative | A current small production model is a realistic RAG component for the context the research question describes. |
| Availability | Confirmed present in the account model list. |

**The model is a fixed component of the RAG treatment, not an experimental variable.** This
study compares BM25 against RAG. It does not compare generation models, and no result may
be attributed to model choice.

**Considered and rejected:** `gpt-4o` (higher cost and latency for no methodological benefit
at this corpus size); newer mini variants (nothing in the design requires reasoning beyond
~1,700 tokens of evidence).

---

## 3. Generation configuration

| Parameter | Proposed | Rationale |
|---|---|---|
| `temperature` | **0.0** | Maximum determinism. Removes sampling variance from the generation step, so a RAG-vs-BM25 difference is not partly a difference in sampling luck. |
| `top_p` | not set | Redundant at temperature 0; leaving it unset avoids implying it was tuned. |
| `max_tokens` | **800** | Sufficient for a grounded answer with 5 citations. A truncated answer would be a generation artefact, not a system finding. |
| Seed, if the endpoint supports it | fixed and recorded | Reduces residual non-determinism. Recorded whether or not the endpoint honours it. |
| `n` | 1 | One answer per query. Multiple samples would be a different design and would need their own metric definition. |

`temperature = 0` does **not** guarantee byte-identical output across the API's model
versions. Because no dated snapshot is published for the embedding model, the same applies
here: the exact `gpt-4o-mini` snapshot string is recorded at freeze time, and the full
prompt plus every response is stored as a reproducibility artefact.

---

## 4. System prompt

**Frozen verbatim at approval.** The prompt is the single largest lever on RAG's answer
quality, so it is fixed in advance and never revised after results.

Its requirements are fixed by the research design:

1. **Grounding.** Answer **only** from the supplied chunks. No outside knowledge.
2. **Abstention.** If the chunks do not contain the answer, say so explicitly. Abstaining
   correctly is scored as success, not failure - otherwise the system is rewarded for
   guessing, which is the opposite of the intended behaviour.
3. **Citation on every claim.** Each factual claim carries the chunk ID(s) supporting it.
4. **No invented identifiers.** A document or chunk ID that was not supplied is a fabricated
   citation and is counted as the most serious generation failure.
5. **Version awareness.** When a supplied chunk belongs to a superseded document, say so and
   name the current document if it is among the supplied chunks. This is what Q-SUP-1/2/3
   test, and the prompt must not silently launder a superseded value into a current answer.
6. **Advisory framing.** The assistant supports a human decision; it does not decide.
7. **No autonomous action.** It does not modify, reprioritise or commit a backlog.

The exact final wording is recorded in `experiments/configs/rag_prompt.txt` and hashed at
freeze.

---

## 5. Citation / provenance format

**Proposed format**, chosen so citations are machine-checkable against the retrieval log:

```
... claim text ... [DOC-PRD-A-01-v2#C0]
```

- `<document_id>#<chunk_index>`, matching the frozen chunk-ID format.
- Every citation ID must exist in the retrieval log for that query.
- A citation to a chunk that was retrieved but does not support the claim is a
  **mis-citation**; a citation to an ID that was never supplied is a **fabricated
  citation**. Both are counted and reported.

Rationale for a bracketed machine-readable form rather than prose attribution: it can be
validated automatically against the logged retrieval set, which prose cannot. Citation
correctness then becomes a measured quantity rather than a matter of opinion.

---

## 6. Vector store

| Setting | Value | Status |
|---|---|---|
| Store | Chroma | Approved (D3) |
| Version | 1.5.9 | Verified installed |
| Metric | cosine | Verified: OpenAI returns unit-normalised vectors (L2 norm 0.9999), so cosine is a plain dot product |
| Persistence | `data/vectorstore/v1-corpus` | Proposed |

Chroma must preserve stable document IDs, stable chunk IDs, metadata, scores, ranking and
source traceability.

### 6.1 Exact NumPy cross-check - validation only

An exact brute-force NumPy cosine retrieval over the stored embedding matrix runs alongside
Chroma and asserts:

- identical top-k chunk-ID set
- identical ranking order
- all scores finite
- no stale or duplicated chunk IDs

At roughly 289 chunks, brute force is exact and instantaneous, so no approximate index is in
play and "exact" genuinely means exact.

**This is a validation instrument, not a second experimental treatment.** Its purpose is to
distinguish vector-store implementation problems from embedding/retrieval behaviour. If it
disagrees with Chroma, that is a finding to report - it is **never** used to alter, correct
or tune experimental results.

---

## 7. Output form, relative to BM25

RAG's user-facing output is a **generated grounded answer** with `[DOC-ID#Cn]` citations.
BM25's is its **top-5 retrieved passages**. The two forms are explicitly not identical and
are not claimed to be. Evaluation is layered accordingly — see
`docs/evaluation_metrics.md` §0.

## 8. What is deliberately NOT decided here

- No comparison of `text-embedding-3-large` against `-small`. The embedding model is a fixed
  component of the RAG treatment.
- No alternative chunking configuration, pending the C6 decision recorded in
  `CHUNKING_DECISION.md`.
- No prompt variants, no temperature sweep, no top-k sweep. Running several and selecting
  the best would make this an optimisation exercise, not a controlled comparison.

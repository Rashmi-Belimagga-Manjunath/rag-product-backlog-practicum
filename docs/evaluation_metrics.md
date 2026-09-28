# Evaluation Metric Definitions

**Status:** defined before any comparative run. Every formula, cutoff and tie-break is
fixed here, because a metric defined after seeing results can be made to say whatever the
results happen to need.

**Scope note.** This document defines *how* metrics are computed. It contains no results.

## 0. Evaluation design: two layers, and why the outputs differ

Evaluation is split into two layers because **the two systems do not produce the same kind
of output**, and pretending otherwise would corrupt the comparison.

| | BM25 (System A) | RAG (System B) |
|---|---|---|
| Output form | **retrieved evidence** — the top-5 ranked passages | **generated grounded answer** built on the retrieved evidence |
| Generation component | none | yes |
| Answer prose | none | yes, with `[DOC-ID#Cn]` citations |

**The two output forms are explicitly not identical and are not claimed to be.** BM25 is a
pure retrieval system; it has no model that could synthesise an answer, and **no prose
answer will be fabricated for BM25 to make the two superficially symmetrical.** Doing so
would invent a capability the baseline does not have, and it would blur the very distinction
the research question is about.

This asymmetry is a **documented characteristic of the systems under comparison**, not a
confound to be engineered away. It also has a direct consequence: the two layers below
measure different things, and a difference between layers must be interpreted as a
difference in *output capability*, not as a like-for-like win.

### Layer A — retrieval comparison (like-for-like)

BM25 and RAG **retrieval** are compared directly, because both return a ranked list of the
same chunk objects under the same conditions:

- same corpus
- same 32 queries
- same ground truth
- same `k = 5`

Metrics: **Precision@5, Recall@5, MRR**, and **dependency retrieval accuracy** where
applicable. This layer is a genuine like-for-like comparison of ranking quality.

### Layer B — user-facing decision support (not like-for-like)

Each system is presented as it actually is, and the resulting user-facing output is
evaluated on: **usefulness, clarity, trust, and task completion time.**

BM25's user-facing output is its top-5 retrieved passages. RAG's is the generated grounded
answer with citations. Because these are different artefacts, Layer B measures **the
end-to-end decision-support experience of each system as designed**, including the cost of
BM25 leaving the user to read and reconcile passages unaided. Section 7.1 records what this means
for interpretation; the difference is disclosed rather than removed.

Any claim of the form "RAG and BM25 produce the same thing, but RAG does it better" is
unsupported by design and will not be made.

---

## 1. Preliminaries

### 1.1 Unit of retrieval and relevance

Both systems retrieve **chunks**, produced by the same structure-aware chunker over the same
corpus. A chunk is the unit because that is the unit both systems actually rank.

A retrieved chunk counts as **relevant** to a query if and only if its ID is in that
query's ground-truth `relevant_chunk_ids`. Relevance is assigned by provenance — the
declared `DocumentLink` set of the target entity — and never by comparing query text to
chunk text. Text-similarity relevance would be a second, unstated retrieval model sitting
inside the scoring, and it would favour the embedding system by construction.

Ground truth is derived from the structured source of truth only. No LLM and no retrieval
run produces a label.

### 1.2 Cutoff

`k = 5` for all `@k` metrics, matching the RAG retrieval depth proposed in
`docs/rag_configuration.md`. BM25 and RAG are truncated to the same 5 chunks, so the
comparison is at equal budget.

### 1.3 Independent logging

Each system writes a retrieval log **before** any answer is generated:

```
{query_id, system, chunk_id, rank, score, document_id, retrieved_at}
```

Generation output is written to a separate file keyed by `query_id`. If a retrieval log is
missing for a query, that query is a **failed run**, reported as failed — never silently
dropped from the denominator.

---

## 2. Precision@5

```
Precision@5 = |retrieved_top5 ∩ relevant| / |retrieved_top5|
```

Both systems always return exactly 5 chunks, so the denominator is 5. If a system returns
fewer, the denominator is the number returned **and the shortfall is logged**, because
returning 3 results and scoring 3/3 would reward a broken retriever.

Reported as a proportion, per query, then averaged over the 32 queries (macro-average). The
per-query values are also retained so category-level analysis is possible.

## 3. Recall@5

```
Recall@5 = |retrieved_top5 ∩ relevant| / |relevant|
```

`|relevant|` is the number of ground-truth chunks for that query, which varies: a query
pointing at one feature spec has few relevant chunks, a cross-document query has more.
A system that returns 5 chunks cannot achieve Recall@5 = 1.0 on a query with 9 relevant
chunks. This is a property of the metric, not a system defect, and must be stated in the
results rather than worked around by widening `k`.

## 4. MRR (Mean Reciprocal Rank)

```
RR(q)  = 1 / rank of the FIRST relevant chunk in the ranked list
       = 0 if no relevant chunk appears in the top 5
MRR    = (1 / 32) × Σ RR(q)
```

Rank is 1-based within the top-5 list. `RR = 0` when the answer-relevant chunk is present
at rank 6 — it counts as a miss at this cutoff, which is the point of the metric.

## 5. Dependency accuracy

Defined over the 13 dependency-related queries. The unit is a **dependency ID**, not a
document.

For query `q` with expected dependency set `E(q)` and system-identified set `P(q)`:

```
TP(q) = |P(q) ∩ E(q)|            correctly identified
FP(q) = |P(q) \ E(q)|            FALSE dependency
FN(q) = |E(q) \ P(q)|            MISSED dependency
```

Per query:

```
Dependency precision(q) = TP / (TP + FP)      0 if TP+FP = 0
Dependency recall(q)    = TP / (TP + FN)      0 if TP+FN = 0
Dependency F1(q)        = 2PR / (P + R)       0 if P+R = 0
```

Aggregated over the 13 dependency-related queries, and reported **split by explicitness**
(6 explicit, 7 implicit) because they are different tasks: an explicit dependency is stated
in the retrieved text, an implicit one is not.

The 19 non-dependency queries are scored on **false-dependency rate only**: any dependency
the system asserts when none is expected is a false positive. A system that invents
dependencies on unrelated queries scores 1.0 precision here, and that must be reported.

### 5.1 Retrieval error vs generation error — mandatory separation

This distinction is the difference between "the RAG pipeline works" and "the retriever
missed", and collapsing it would make the results uninterpretable.

For every dependency error, classify it into exactly one:

| Class | Condition | Applies to |
|---|---|---|
| **Retrieval error** | The required evidence was **not** retrieved into the top-5, so the answer could not be grounded on it. | Both systems |
| **Generation / reasoning error** | The required evidence **was** retrieved, but the answer was incorrect, incomplete, unsupported by the retrieved evidence, or failed to use that evidence correctly. | **RAG only** |
| **Correct** | The dependency set matches `E(q)` exactly. | Both systems |

**BM25.** BM25 has no generation stage, so it cannot commit a generation or reasoning error.
**Every BM25 error is a retrieval error, and this is assessed directly**: the ground-truth
document is simply absent from, or ranked below the cutoff in, the top-5. BM25 dependency
accuracy is therefore a pure retrieval measurement with no interpretation required.

**RAG.** RAG can fail at either stage, and conflating them would make the results
uninterpretable — a missing dependency could mean the retriever missed it or that the
generator ignored evidence it was given, and those are opposite findings about the system.

Procedure for RAG, applied per error: check whether any ground-truth-relevant chunk appears
in that query's logged top-5.

- Not present → **retrieval failure** (required evidence was not retrieved).
- Present, but the answer still omitted the dependency, asserted a wrong one, or did not
  cite the evidence → **generation/reasoning failure**.

The classification is driven by the **retrieval log**, which is written before generation, so
it cannot be influenced by what the generator went on to say. Both counts are reported, and
the generation-error count is always stated as conditional on a retrieval success.

An answer that invents a dependency **not present in any retrieved chunk** is recorded
separately as a **fabrication**, counted, and reported. It is a distinct and more serious
failure than a wrong inference from retrieved evidence, because it means the generator
asserted something the evidence does not support at all.

---

## 6. Task completion time

```
time(q, system) = t_answer_visible - t_query_submitted
```

Measurement protocol, fixed in advance:

- Client-side wall clock around the system's full user-facing path, including retrieval and
  generation for RAG, and retrieval plus presentation for BM25.
- **One warm-up run per system** over 3 fixed queries, discarded, to exclude first-call
  model and connection overhead.
- Every query run **3 times**; the **median** of the three is used. The median rather than
  the mean because a single API-side stall would otherwise dominate.
- Both systems run on the same machine, same session, interleaved **A/B/A/B** per query, so
  neither system systematically benefits from a warmer cache.
- Wall clock is recorded **separately** from API-reported latency, which excludes
  network and client overhead and would flatter RAG.

Reported per query, then summarised by median, IQR, and per category.

**Disclosed confound:** RAG includes a generative call and BM25 does not. Task completion
time therefore measures *system cost as deployed*, which is the practical question, not
retrieval speed in isolation. It must not be reported as evidence that BM25 "retrieves
faster" in a like-for-like retrieval comparison. A retrieval-only latency figure (time to
return the ranked 5 chunks, excluding generation) is logged for both systems so the two can
be separated.

---

## 7. Usefulness, clarity and trust

**Human rating is gated.** No participant data is collected until the NCI determination is
confirmed. Until then these three are rated by the researcher/assessor against a fixed
rubric, and that substitution is **disclosed as a limitation**, not presented as
equivalent to participant evaluation.

All three use the same 5-point anchored scale:

| Score | Anchor |
|---|---|
| 5 | Fully — directly answers the question with no gaps |
| 4 | Mostly — correct, with a minor omission or imprecision |
| 3 | Partly — partially correct, or correct but incomplete |
| 2 | Barely — recognisably on topic but largely unhelpful or wrong |
| 1 | Not at all — irrelevant, or actively misleading |

**Usefulness** — does the response contain the information needed to answer the query?
**Clarity** — is the response comprehensible and well organised?
**Trust** — does the response give a reader confidence in its correctness, through
accurate citations and calibrated statements of uncertainty?

Reported as mean and distribution per system. With a single rater and n=32, these are
**descriptive only** — no significance test, no inter-rater reliability claim.

### 7.1 The BM25 answer problem — RESOLVED by the two-layer design

BM25 returns ranked passages, not prose, so usefulness, clarity and trust cannot be measured
on a like-for-like basis. Three options were considered:

1. Rate the top-5 passages as the BM25 "response".
2. Report generation metrics for RAG only.
3. Add a neutral extractive summariser to BM25.

**Decision taken: option 1, implemented as Layer B.** BM25's top-5 passages are presented as
its user-facing output and rated as such.

Options 2 and 3 were rejected for stated reasons. Option 2 leaves the research question
partly unanswered, since the question asks about efficiency, relevance *and* accuracy.
Option 3 introduces a second generative component into a baseline that is defined as
keyword-based retrieval, and risks turning the baseline into a second RAG system.

**Consequences that must be disclosed in the results, not glossed over:**

- Layer B is **not** a like-for-like comparison. It compares a retrieval-only system's
  output against a generation system's output. That is the honest description of the two
  systems being compared.
- BM25's usefulness and clarity scores are affected by the readability of the underlying
  documentation, not only by retrieval quality. This is a property of the closed-domain
  templated corpus and a limitation of the design, not of the BM25 implementation.
- A BM25 score that reflects a user having to read and mentally reconcile five passages is a
  **real cost of the keyword-search workflow**, which is exactly the practical problem the
  research question asks about. It is reported as such, and the confound is stated in the
  same sentence as the number.
- No prose answer is fabricated for BM25 at any point.

### 7.2 Citation correctness (RAG only)

For every claim in a RAG answer that carries a citation, the cited chunk must contain the
supporting content:

```
Citation precision = cited-and-supporting / cited
Citation recall    = cited-and-supporting / supportable
```

A citation pointing at a chunk that does not contain the claim is a **mis-citation**,
counted separately and reported. Fabricated or non-existent document IDs are
**fabricated citations** — the most serious generation failure in this system, and reported
as a headline number.

---

## 8. Reporting requirements

- Every metric is computed over **all 32 queries**. No query is excluded. If a query failed
  to run, it is reported as a failure with its denominator intact.
- Category-level breakdowns are reported for all six categories, and explicitness-split
  breakdowns for the 13 dependency-related queries.
- n=32 supports **descriptive statistics, direction and magnitude of differences, and error
  analysis**. It does not support significance testing or generalisation beyond this corpus.
- RAG performing worse on any metric is reported as a valid finding.
- A metric that cannot be computed is reported **with the reason**, never omitted silently.

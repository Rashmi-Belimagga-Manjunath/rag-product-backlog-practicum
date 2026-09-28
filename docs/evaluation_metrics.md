# Evaluation Metric Definitions

**Status: D-009 NOT FROZEN.** Definitions below are submitted for review. The two-layer
design (§0) and the BM25 output form are already approved (D-010) and are not reopened
here.

This document specifies the operational definition of all eight metrics. Each entry states
the numerator and denominator, unit of analysis, aggregation, tie handling, zero-relevant
queries, dependency-not-applicable queries, the scale for human-facing measures, missing
value handling, which system it applies to, and whether it is retrieval-level or
user-facing. Nothing here is a result.

---

## 0. Evaluation design

**BM25 and RAG do not produce the same kind of output, and this is not engineered away.**

| | BM25 (System A) | RAG (System B) |
|---|---|---|
| Output form | **retrieved evidence** — top-5 ranked passages | **generated grounded answer** with `[DOC-ID#Cn]` citations |
| Generation component | none | yes |

**The two output forms are explicitly not identical and are not claimed to be.** No prose
answer is fabricated for BM25. That asymmetry is a documented characteristic of the systems
under comparison.

- **Layer A — retrieval comparison (like-for-like).** Both systems return the *same chunk
  objects* over the same corpus, the same 32 queries, the same ground truth, at the same
  `k = 5`. Metrics 1–4. This layer is a genuine like-for-like ranking comparison.
- **Layer B — user-facing decision support (not like-for-like).** Each system is rated as it
  actually is. Metrics 5–8. This layer measures the end-to-end experience of each system as
  designed, **including** the cost of BM25 leaving the user to reconcile passages unaided.
  That cost is real and is reported as such, with the confound stated in the same sentence
  as the number.

A difference between layers is a difference in **output capability**, not a like-for-like
win. Claims that the two systems produce "the same thing, but RAG does it better" are
unsupported by design and will not be made.

### 0.1 Metric applicability summary

| # | Metric | Level | BM25 | RAG | Layer |
|---|---|---|---|---|---|
| 1 | Precision@5 | retrieval | yes | yes | A |
| 2 | Recall@5 | retrieval | yes | yes | A |
| 3 | MRR | retrieval | yes | yes | A |
| 4 | Dependency accuracy | retrieval | yes | yes | A |
| 5 | Task completion time | user-facing | yes | yes | B |
| 6 | Usefulness | user-facing | yes | yes | B |
| 7 | Clarity | user-facing | yes | yes | B |
| 8 | Trust | user-facing | yes | yes | B |
| — | Citation precision / recall | generation | **no** | yes | B |
| — | Mis-citation count | generation | no | yes | B |
| — | Fabricated-citation count | generation | no | yes | B |
| — | Fabrication count (invented dependency) | generation | no | yes | B |

---

## 1. Global conventions

These apply to every metric and are stated once rather than repeated eight times.

**Relevance assignment.** A retrieved chunk is relevant to a query **iff** its ID is in that
query's ground-truth `relevant_chunk_ids`. Relevance comes from declared `DocumentLink`
provenance in the structured source of truth. It is **never** assigned by comparing query
text to chunk text. A text-similarity label would be a second, unstated retrieval model
inside the scoring and would favour the embedding system by construction.

**Unit of analysis.** The query. Every metric is computed per query, then aggregated. There
is no per-chunk or per-document unit, because a query is the task a user actually performs.

**Aggregation.** Macro-average: the unweighted mean of per-query values across all 32
queries. Every query carries equal weight regardless of how many relevant items it has, so
a query with 1 relevant chunk cannot dominate one with 9. The per-query values are retained
and reported per category (6 categories) and, for dependency metrics, per explicitness
(6 explicit, 7 implicit).

**Denominator integrity.** Every metric is reported over **all 32 queries**. Nothing is
silently dropped.

**Zero-relevant-item queries.** `|relevant| = 0` is a **ground-truth defect, not a metric
value.** The benchmark specification guarantees every one of the 32 slots resolves to at
least one relevant item, and `validate_ground_truth --against-final` enforces it as a hard
stop. If a query nonetheless reaches scoring with zero relevant items, the run is **aborted
and reported as invalid** — Recall@5 would have an undefined denominator and a system could
not be rewarded or penalised for it.

**Dependency-not-applicable queries.** 19 of the 32 queries expect no dependency; 13 do.
Handling differs by metric and is specified per metric in §5.

**Ties.** Resolved **at retrieval time**, before any metric is computed. BM25 ties on score
break on ascending chunk ID (frozen, D-008). RAG ties on cosine score break on ascending
chunk ID. Both are content-independent and deterministic, so a chunk is unambiguously
inside or outside the top-5. No metric is ever computed over a tied, order-ambiguous list.
Ties in *human ratings* are handled in §6.

**Missing values.** Two distinct cases, which must not be conflated:

- **A failed run is not a missing value.** A query whose retrieval log is absent, or which
  errors, is scored as a **failure**: Precision@5 = 0, Recall@5 = 0, RR = 0, dependency
  set = ∅, and its time is recorded as the failure value with the reason. It stays in every
  denominator. A retriever that crashes on hard queries must not score better by dropping
  them. Any missing retrieval log is counted and reported in the run summary.
- **A human rating that was never assigned is a missing value.** It is **never imputed.**
  Means are computed over the scored subset, the denominator is always printed alongside
  every mean, and the missing count is reported. See §6.

---

## 2. Precision@5 — retrieval-level

| Attribute | Specification |
|---|---|
| Numerator | `\|retrieved_top5 ∩ relevant\|` — count of top-5 chunks whose ID is in the query's ground-truth relevant set |
| Denominator | `\|retrieved_top5\|`, which is 5 when the system returns 5 chunks |
| Shortfall rule | If a system returns fewer than 5, the denominator is **the number actually returned** and the shortfall is logged and reported. Scoring 3/3 would reward a broken retriever. |
| Unit of analysis | query |
| Aggregation | macro-average over 32 queries; also per category |
| Ties | resolved pre-scoring by ascending chunk ID; no order ambiguity at the boundary |
| Zero-relevant queries | impossible by construction; would abort the run (§1) |
| Dependency N/A | no effect; applies to all 32 queries |
| Human scale | n/a |
| Missing values | failed run scores 0 and stays in the denominator |
| Applies to | **both** BM25 and RAG |
| Level | **retrieval** (Layer A) |

```
Precision@5(q) = |retrieved_top5(q) ∩ relevant(q)| / |retrieved_top5(q)|
```

## 3. Recall@5 — retrieval-level

| Attribute | Specification |
|---|---|
| Numerator | `\|retrieved_top5 ∩ relevant\|` |
| Denominator | `\|relevant(q)\|` — the number of ground-truth relevant chunks for that query, which varies across queries |
| Unit of analysis | query |
| Aggregation | macro-average over 32 queries; also per category |
| Ties | resolved pre-scoring, as §1 |
| Zero-relevant queries | **undefined denominator — would abort the run** (§1) |
| Dependency N/A | no effect |
| Human scale | n/a |
| Missing values | failed run scores 0 and stays in the denominator |
| Applies to | **both** |
| Level | **retrieval** (Layer A) |

```
Recall@5(q) = |retrieved_top5(q) ∩ relevant(q)| / |relevant(q)|
```

**Interpretive note, to be stated wherever this metric appears.** A system returning 5
chunks cannot score Recall@5 = 1.0 on a query with 9 relevant items. That is a property of
the metric at `k = 5`, not a system defect, and it is reported rather than worked around by
widening `k` after the fact.

## 4. MRR — retrieval-level

| Attribute | Specification |
|---|---|
| Numerator | `1`, for the **first** ground-truth-relevant chunk in the ranked top-5; `0` if none appears |
| Denominator | none — MRR is already a ratio of a reciprocal rank |
| Unit of analysis | query |
| Aggregation | mean of RR over 32 queries |
| Ties | resolved pre-scoring; if two relevant chunks tie, the one with the lower chunk ID is the first, per the frozen tie-break |
| Zero-relevant queries | cannot abort the run on this metric alone (no denominator needed); RR = 0. The Recall@5 abort rule (§1) fires first in any case. |
| Dependency N/A | no effect |
| Human scale | n/a |
| Missing values | failed run scores RR = 0 |
| Applies to | **both** |
| Level | **retrieval** (Layer A) |

```
RR(q) = 1 / rank_of_first_relevant_chunk_in_top5,  else 0
MRR   = (1/32) * Σ RR(q)
```

Rank is 1-based. `RR = 0` when the relevant chunk sits at rank 6: it counts as a miss at
this cutoff, which is the point of the metric.

## 5. Dependency accuracy — retrieval-level

**Two distinct quantities, because the 32 queries are not uniform.** Defining the unit as
the **dependency ID**, not the document, and let `E(q)` be the expected dependency set and
`P(q)` the system's identified set:

```
TP(q) = |P(q) ∩ E(q)|     correctly identified
FP(q) = |P(q) \ E(q)|     FALSE dependency asserted
FN(q) = |E(q) \ P(q)|     MISSED dependency
```

**On all 32 queries — dependency precision:**

| Attribute | Specification |
|---|---|
| Numerator | `TP(q)` |
| Denominator | `TP(q) + FP(q)` |
| Zero denominator | if `TP+FP = 0` — the system asserted nothing — precision is defined as **1.0**, and the count of such queries is reported explicitly so a system cannot look perfect by staying silent |
| Aggregation | macro-average over 32 queries |
| Applies to | both |
| Level | retrieval (Layer A) |

**On the 13 dependency-related queries only — recall and F1:**

| Attribute | Specification |
|---|---|
| Numerator (recall) | `TP(q)` |
| Denominator (recall) | `TP(q) + FN(q)`, guaranteed ≥ 1 because `E(q)` is non-empty on these 13 |
| Numerator (F1) | `2·TP(q)` |
| Denominator (F1) | `2·TP(q) + FP(q) + FN(q)`; defined as 0 if this is 0 |
| Dependency N/A treatment | On the **19 non-dependency queries**, `E(q) = ∅`, so recall would be `0/0` and is **undefined and not reported**. F1 is likewise undefined there. Those queries contribute to **precision only**, which is well defined: a system that invents a dependency on an unrelated query scores 0.0 precision on it, and that is the intended penalty. |
| Aggregation | macro-average over the 13; **also split by explicitness (6 explicit, 7 implicit)** because these are different tasks — an explicit dependency is stated in the retrieved text, an implicit one is not |
| Ties | n/a (set comparison, no ranking) |
| Zero-relevant queries | n/a; the abort rule in §1 still applies corpus-wide |
| Missing values | failed run sets `P(q) = ∅`, giving FN on the 13 and precision 1.0 on the 19; it remains in every denominator and the run summary counts the failure |
| Applies to | both |
| Level | retrieval (Layer A) |

**A system that answers "no dependencies" to everything scores precision 1.0 on all 32 and
recall 0.0 on all 13.** Both are always reported together. Precision alone is not a valid
summary of this metric and will not be used as one.

### 5.1 Error classification — mandatory

Every dependency error is classified into exactly one class, from the **retrieval log**,
which is written **before** generation and therefore cannot be influenced by what the
generator went on to say.

**BM25.** BM25 has no generation stage, so it **cannot** commit a generation or reasoning
error. **Every BM25 error is a retrieval error, and it is assessed directly:** the
ground-truth document is absent from the top-5, or ranked below the cutoff. BM25 dependency
accuracy is a pure retrieval measurement needing no interpretation.

**RAG.**

| Class | Condition |
|---|---|
| **Retrieval failure** | The required evidence was **not** retrieved into the top-5. |
| **Generation / reasoning failure** | The required evidence **was** retrieved, but the answer was incorrect, incomplete, unsupported by the retrieved evidence, or failed to use that evidence correctly. |
| **Correct** | `P(q) = E(q)`. |

Procedure, applied per error: check whether any ground-truth-relevant chunk appears in that
query's logged top-5. Absent → retrieval failure. Present but misused → generation/reasoning
failure. The generation-failure count is always reported as **conditional on a retrieval
success**, never as a standalone rate.

Two fabrication types are counted separately, because they are worse than a wrong inference:

- **Fabricated dependency** — a dependency asserted that appears in **no** retrieved chunk.
- **Fabricated citation** — a cited ID that was never supplied in the top-5. This is the most
  serious generation failure in the system.

## 6. Task completion time — user-facing

| Attribute | Specification |
|---|---|
| Quantity | `time(q, system) = t_answer_visible − t_query_submitted`, client-side wall clock over the system's **full user-facing path** |
| BM25 path | retrieval **plus** presentation of the top-5 passages as the output |
| RAG path | retrieval **plus** generation **plus** presentation |
| Unit of analysis | query |
| Aggregation | **median** of 3 runs per query (not the mean: one API-side stall would otherwise dominate), then median and IQR across the 32 queries, plus per category |
| Ties | n/a |
| Zero-relevant queries | n/a; timing is measured whatever the relevance |
| Dependency N/A | n/a |
| Human scale | n/a |
| Missing values | a failed run is **excluded from the median but counted in the run summary**, with the reason. Time is not imputed. The count of excluded failures is printed next to the median so the reader can see how many queries the median is based on. |
| Warm-up | one warm-up run per system over 3 fixed queries, **discarded**, to exclude first-call model and connection overhead |
| Ordering | both systems interleaved **A/B/A/B** per query on the same machine, so neither systematically benefits from a warmer cache |
| Applies to | **both** |
| Level | **user-facing** (Layer B) |

**Two figures are logged, and they must not be conflated:**

1. **Task completion time** — the full user-facing path. This is the practical number and it
   answers the research question about efficiency.
2. **Retrieval-only latency** — time to return the ranked 5 chunks, excluding generation,
   logged for both systems.

**Disclosed confound.** RAG includes a generative call and BM25 does not, so task completion
time measures *system cost as deployed*, not retrieval speed in isolation. It must never be
reported as evidence that BM25 "retrieves faster" in a like-for-like retrieval comparison.
The retrieval-only figure exists so the two can be separated.

## 7. Usefulness, clarity, trust — user-facing

**These three are one instrument with one scale.** Each is scored on the same 5-point
anchored scale:

| Score | Anchor |
|---|---|
| 5 | **Fully** — directly answers the question, with no gaps |
| 4 | **Mostly** — correct, with a minor omission or imprecision |
| 3 | **Partly** — partially correct, or correct but incomplete |
| 2 | **Barely** — recognisably on topic, but largely unhelpful or wrong |
| 1 | **Not at all** — irrelevant, or actively misleading |

**Definitions.**

- **Usefulness** — does the output contain the information needed to answer the query?
  A response that is correct but omits the required fact scores below 5.
- **Clarity** — is the output comprehensible and well organised? Scored on presentation,
  independent of correctness; a correct but incoherent answer loses points here and not on
  usefulness.
- **Trust** — does the output give a reader confidence in its correctness, through accurate
  attribution and calibrated statements of uncertainty? For RAG this includes whether
  citations point at the passages that support the claims.

| Attribute | Specification |
|---|---|
| Unit of analysis | query |
| Scale | 5-point anchored ordinal, 1–5, anchors above |
| Aggregation | mean **and full distribution** per system. The distribution is mandatory: with one rater and n = 32, a mean of 3.4 can hide a mode of 3 or a bimodal split, and the distribution is what shows it. |
| Ties in ratings | no tie-breaking rule exists or is needed — the scale has no midpoint-forcing convention, and 3 ("partly") is a real distinct score, not a tie. Ties in the *data* are reported as ties, not smoothed. |
| Zero-relevant queries | n/a; the abort rule in §1 still applies corpus-wide |
| Dependency N/A | n/a; all 32 queries are rated on all three measures |
| Missing values | **never imputed.** Means are over the scored subset only, the denominator is printed with every mean, and the missing count is reported. **If more than 10% of ratings are missing, Layer B is reported as incomplete and the three metrics are not compared across systems.** |
| Rater | researcher/assessor, **not** a participant — see the ethics constraint below |
| Applies to | **both**, on each system's real output |
| Level | **user-facing** (Layer B) |

**Disclosure required wherever these three appear.** A single rater and n = 32 make these
**descriptive only**. No significance test, no inter-rater reliability statistic, and no
generalisation beyond this corpus is claimed.

**BM25 output form.** BM25 is rated on its **top-5 retrieved passages presented as
retrieved evidence**. It is not given a fabricated prose answer. Consequently BM25's
usefulness and clarity are affected by the readability of the underlying documentation, not
only by retrieval quality. This is a limitation of the design and of the closed-domain
templated corpus, and it is stated in the same sentence as the number. That BM25 leaves the
user to read and mentally reconcile five passages unaided is a **real cost of the keyword
search workflow**, which is the practical problem the research question asks about, and it is
reported as such rather than adjusted away.

### 7.1 Ethics constraint on these three

No human-participant data is collected. Ratings are made by the researcher against the
anchors above, and that substitution is **disclosed as a limitation, not presented as
equivalent to participant evaluation**. D-011 remains **OPEN**: no assumption is made about
whether ethics approval is required, and none may be assumed either way. No participant
recruitment, consent process or data collection begins until the NCI coordinator or the
appropriate ethics process has determined what is required.

If participant evaluation is later approved, it must evaluate the **already-frozen technical
system** without modifying it. Changing the system during participant testing would
invalidate both the technical comparison and the participant data.

## 8. Citation correctness — generation-level, RAG only

Not one of the eight required metrics, but reported because a citation system that cannot be
audited is not evidence of anything. For every claim carrying a citation:

```
Citation precision = cited-and-supporting / cited
Citation recall    = cited-and-supporting / supportable
```

| Class | Condition |
|---|---|
| **Mis-citation** | cited a chunk that *was* retrieved, but which does not contain the supporting content |
| **Fabricated citation** | cited an ID that was **never supplied** in the top-5 |

Both are counted and reported. Fabricated citations are reported as a headline number.

## 9. Reporting requirements

- Every metric is computed over **all 32 queries**. No query is excluded. A failed query is
  reported as a failure with its denominator intact.
- Category breakdowns are reported for all six categories; explicitness breakdowns for the
  13 dependency-related queries.
- `n = 32` supports **descriptive statistics, direction and magnitude of difference, and
  error analysis**. It does not support significance testing or generalisation beyond this
  corpus.
- RAG performing worse on any metric is a valid finding and is reported as such.
- A metric that cannot be computed is reported **with its reason**, never omitted silently.
- Layer A and Layer B results are reported **separately and never merged into a single
  score.**

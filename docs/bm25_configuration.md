# BM25 Baseline Configuration

**Status:** PROPOSED. Not frozen. Frozen only on explicit approval, before any comparative
result is examined.

The baseline is a **standard BM25 lexical retriever** over the same corpus, the same chunks
and the same queries as the RAG system. It contains no generation component. It is the
traditional system named in the research question and must not be weakened.

---

## 1. Scoring parameters

| Parameter | Value | Note |
|---|---|---|
| `k1` | **1.5** | Standard BM25 term-frequency saturation. Frozen, never tuned. |
| `b` | **0.75** | Standard BM25 length normalisation. Frozen, never tuned. |

Both are the conventional default values from Robertson & Zaragoza (2009). They were fixed
before any retrieval run and are **not** adjusted to close a performance gap to RAG. Tuning
BM25 after seeing RAG's performance would invalidate the comparison by converting a
"traditional baseline" into a fitted competitor.

The scoring function, implemented as written:

```
score(D, Q) = Σ_{t ∈ Q}  IDF(t) · ( f(t,D) · (k1 + 1) )
                          ─────────────────────────────────────
                          f(t,D) + k1 · (1 - b + b · |D|/avgdl)
```

with `IDF(t) = ln( 1 + (N - df(t) + 0.5) / (df(t) + 0.5) )` — the non-negative Lucene
variant, which cannot produce negative scores and is the standard implementation choice.
Document frequency is computed over the **chunk set** that the system actually indexes.

---

## 2. Indexing and text handling

Fixed so the baseline is reproducible and the comparison is not confounded by tokenisation.

| Setting | Value | Note |
|---|---|---|
| Unit of retrieval | chunk | Identical to RAG. The two systems must rank the same objects. |
| Lowercasing | yes | Applied to both systems' inputs, so query and document text are treated consistently. |
| Tokenisation | Unicode word tokens, `[\w']+` | Hyphenated terms such as "run-book" split consistently on both sides. |
| Stopword removal | **none in scoring** | BM25's IDF already down-weights ubiquitous terms. Removing stopwords would be an unstated, unjustified deviation from standard BM25. |
| Stemming | **none** | Porter stemming is common but is a transformation with its own failure modes; omitting it keeps the baseline transparent and defensible. Recorded as a deliberate choice. |
| Stopwords for *difficulty measurement* | frozen `STOPWORDS` set | Used only for query difficulty banding, never inside the retriever. Keeping the two separate prevents the benchmark-construction measure from leaking into the system. |

---

## 3. Query handling

- The query string is used **verbatim** as written in the benchmark. No query expansion, no
  synonym rewriting, no spell correction. Those are RAG-side capabilities and adding them
  to the baseline would confound the comparison.
- Both systems receive byte-identical query strings.
- No system-specific preprocessing is applied to queries for one system but not the other.

---

## 4. Result presentation

- Returns the **top 5 chunks**, ranked by score, to match `top_k = 5` and the `@5` metrics.
- Ties in score broken by **ascending chunk ID** — a deterministic, content-independent
  tie-break. An arbitrary tie-break would make runs non-reproducible.
- The output logs, per query: `chunk_id`, `rank`, `score`, `document_id`. Retrieval is
  logged **before** any presentation step, independently of any answer.

### Output form — decided 2026-09-28

**BM25's user-facing output is the top-5 retrieved passages, presented as retrieved
evidence.** It has no generation component, and **no prose answer is fabricated for BM25** in
order to make it look like RAG's output. The two systems produce different output forms:
BM25 produces retrieved evidence, RAG produces a generated grounded answer.

This is resolved by the two-layer evaluation design in `docs/evaluation_metrics.md` §0:
Layer A compares retrieval like-for-like, Layer B rates each system's real output. The
asymmetry is a documented characteristic of the systems being compared, and the confound it
introduces into the Layer B user-facing metrics is disclosed rather than engineered away.

---

## 5. Implementation

- Reference implementation, no tuning constants beyond `k1` and `b`.
- No document re-ranking stage, no learning-to-rank model, no query-dependent boosting.
- A hand-written implementation of the formula above is preferred over a library default,
  so that the exact scoring is auditable and no undocumented library behaviour (pruning,
  caching, tie-breaking) silently enters the experiment. If a library is used instead, its
  version and every non-default parameter are recorded here before the freeze.

---

## 6. What is forbidden after the freeze

- Adjusting `k1` or `b`.
- Adding stemming, stopword removal, or n-gram expansion after seeing results.
- Adding a re-ranking or fusion stage.
- Changing the unit of retrieval from chunk to document.
- Truncating or extending the top-5 output to close a gap to RAG.
- Removing queries, or excluding queries where BM25 performs badly.

If a genuine defect in the BM25 implementation is discovered after the freeze, it is fixed
and the fix is **disclosed as a protocol deviation**. Silently correcting a baseline so it
performs better, or worse, would compromise the comparison in whichever direction it was
corrected.

# Chunking Decision — Pending Approval

**Status:** DECISION REQUIRED. Neither the C6 measure nor the configuration choice is
frozen. No BM25 or RAG result has been computed or consulted at any point in this document.

---

## 1. What was run

Both approved configurations were compared on the deterministic long-document pilot, which
extends the 34-document mechanism sample past the approved length band to stress the
packer. C1–C8 only.

| | A: 1000 / 200 | B: 600 / 100 |
|---|---|---|
| Chunks | 42 | 63 |
| C1 contiguous sentence units | PASS | PASS |
| C2 no requirement split | PASS | PASS |
| C3 no version pair split | PASS | PASS |
| C4 no orphan references | PASS | PASS |
| C5 dependency coverage | PASS | PASS |
| **C6 <2% duplicate chunks** | **FAIL** | **FAIL** |
| C7 all chunks retrievable | PASS | PASS |
| C8 zero unassigned content | PASS | PASS |

**C6 is the only failing criterion, and it fails identically for both configurations.**

---

## 2. Why C6 fails: the measure cannot work in this corpus

C6 as pre-specified uses **same-document word-type-bag containment > 0.9** as its
definition of a duplicate chunk. Diagnostic on the flagged pairs:

| | mean type-bag containment | mean 8-gram containment |
|---|---|---|
| A | 0.945 | 0.375 |
| B | 0.945 | 0.419 |

The two measures disagree by ~2x, and the type-bag measure is the one failing. The cause is
structural, not a packer defect: a chunk of ~1,000 tokens drawn from a closed-domain
templated corpus of ~1,700 words contains only **169 word types** (A) or **143** (B). Once
vocabulary saturates, nearly every long chunk contains nearly every other long chunk's
vocabulary, so type-bag containment approaches 1.0 by arithmetic rather than by copying.

**Direct measurement of the full per-chunk distribution confirms there is no duplication at
all.** Maximum 8-gram containment of each chunk against every other chunk *in the same
document*:

| Threshold | A (% chunks) | B (% chunks) |
|---|---|---|
| > 0.2 | 0.0% | 0.0% |
| > 0.3 | 0.0% | 0.0% |
| > 0.4 | 0.0% | 0.0% |
| > 0.5 | 0.0% | 0.0% |
| > 0.6 | 0.0% | 0.0% |
| > 0.8 | 0.0% | 0.0% |

**Every same-document pair of chunks shares zero 8-grams.** The type-bag measure is
therefore producing ~100% false positives. C6 is not detecting a defect; it is
indistinguishable from the criterion it was meant to implement.

Cross-document containment is substantial (23–32% of chunks above 0.3), but that is shared
section-template boilerplate across different documents — legitimate documentation
consistency, and related to the D-distractor design, not chunk duplication.

---

## 3. Proposed C6 revision — REQUIRES APPROVAL

**Proposed:** define a duplicate chunk pair as two chunks **in the same document** sharing
more than **50%** of their 8-gram shingles (8-word shingles, containment against the
smaller shingle set). Criterion: **fewer than 2% of chunks** involved in such a pair.

Rationale, fixed before any comparative run:

1. It measures the construct C6 is named for — **verbatim duplication** — rather than
   vocabulary overlap.
2. Threshold 0.5 means "half the chunk is copied word-for-word", a conservative bar. Real
   duplication of a requirement table, an acceptance-criterion block or a risk paragraph
   clears it easily; template phrasing does not.
3. Restricting to the same document keeps shared cross-document boilerplate out of the
   criterion, which is correct — two documents agreeing on a section heading is not a
   chunking fault.
4. It is derived from the **construct-validity** argument and the measured distribution
   above. No retrieval or generation result was involved.

**Under this revision both configurations pass C6 with 0.0% of chunks flagged.**

I am not asserting the revision is approved. Until it is, C6 remains failing and the
methodology cannot be frozen.

---

## 4. Consequence: C1–C8 do not discriminate A from B

Even with C6 repaired, **both configurations pass all eight criteria.** C1–C8 are coherence
and provenance criteria; they check that chunking is not *breaking* documents. They do not
measure retrieval quality, and they were never designed to rank two healthy configurations.

No configuration may be selected on BM25 or RAG performance — that would make chunking a
tuned variable and destroy the comparison.

**Recommended tie-break, stated in advance and not derived from any result:** keep **A
(1000 / 200)**, the already-approved configuration, because

- it is the configuration already in the approved specification, so freezing it introduces
  no new parameter choice;
- it yields 42 chunks versus 63, i.e. 33% fewer vectors, lower embedding and index cost,
  and a smaller evaluation surface — real operational advantages that do not depend on
  which system is being tested;
- choosing B would introduce finer-grained retrieval units at exactly the point where we
  know finer granularity tends to favour embedding retrieval, which is a reason to
  withhold that change, not to make it.

**This is a recommendation requiring explicit approval.** If B is preferred, say so and it
will be recorded as a deliberate deviation, with the bias noted.

---

## 5. Open items

1. Approve or reject the C6 revision in §3.
2. Approve or reject configuration A as the tie-break in §4.
3. If both approved, the chunking criterion is frozen and C8 remains the hard halt for the
   final corpus.

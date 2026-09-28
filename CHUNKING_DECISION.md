# Chunking Decision — APPROVED AND FROZEN

**Frozen 2026-09-28 on explicit student approval. Recorded before any BM25 or RAG run.**
No retrieval or generation result exists, and none was used at any point in this document.

**Frozen configuration: chunk target 1000 words, overlap 200 words.**

---

## 1. Correction to an earlier draft of this record

An earlier draft of this document claimed that "maximum same-document 8-gram containment is
0.0% at every threshold from 0.2 to 0.8, for every chunk, in both configurations", and used
that to support the C6 revision.

**That figure was wrong, and it was an artefact of a bug in the analysis script, not a
property of the corpus.** The script grouped chunks by splitting the chunk ID on `"#"`, but
chunk IDs have the form `<document_id>-C<index>` and contain no `#`. Every chunk therefore
formed its own group, the "same document" comparison set was always empty, and the reported
maximum was necessarily 0.0.

The claim is withdrawn. All numbers below were recomputed after grouping by `document_id`
correctly. The corrected figures change the *reason* the configuration was selected, and
strengthen the case for the C6 revision, but they do not change the outcome.

---

## 2. What was run

Both approved candidates on the deterministic long-document pilot, against C1–C8 only.

| | A: 1000 / 200 | B: 600 / 100 |
|---|---|---|
| Chunks | 42 | 63 |
| C1 contiguous sentence units | PASS | PASS |
| C2 no requirement split | PASS | PASS |
| C3 no version pair split | PASS | PASS |
| C4 no orphan references | PASS | PASS |
| C5 dependency coverage | PASS | PASS |
| **C6 duplicate chunks (revised measure)** | **PASS — 0 pairs = 0.0%** | **FAIL — 4 pairs = 6.3%** |
| C7 all documents retrievable | PASS | PASS |
| C8 zero unassigned content | PASS | PASS |

---

## 3. Why the original C6 had to be replaced

**Original definition:** a duplicate chunk pair is two chunks in the same document whose
word-**type**-bag containment exceeds 0.9, where the type bag is the set of distinct
lowercased word tokens of length > 3.

**Corrected measurement of that measure, grouping by document:**

| | same-document pairs | pairs the original measure flags | mean type-bag | max type-bag |
|---|---|---|---|---|
| A | 12 | **12 (100%)** | 0.940 | 0.974 |
| B | 53 | 29 (55%) | 0.908 | 0.985 |

For configuration A the original measure flags **every single pair**, including pairs whose
true 8-gram containment is as low as 0.000 — pairs that share no repeated text at all.

The cause is saturation, not duplication. In this closed-domain templated corpus a chunk
carries only **128 distinct word types across 577 words** (A) and **111 across 401 words** (B),
a type-per-word ratio of 0.22–0.28. Once vocabulary is this narrow, two long chunks of the
same document necessarily contain almost all of the same types, so type-bag containment
approaches 1.0 by arithmetic whether or not anything was copied. A threshold of 0.9
therefore measures corpus vocabulary size, not chunk duplication, and cannot serve as a
coherence criterion.

The original threshold has **not** been weakened in the sense of being loosened to make a
configuration pass; the criterion was replaced with one that measures the construct it was
named for.

---

## 4. The replacement, as approved

**A duplicate chunk pair is two chunks in the same document whose 8-word shingle
containment exceeds 0.5.** Containment is measured against the smaller shingle set, and the
criterion requires fewer than 2% of chunks to be involved in such a pair.

Corrected measurement:

| | same-document pairs | pairs the revised measure flags | mean 8-gram | max 8-gram |
|---|---|---|---|---|
| A | 12 | **0 (0%)** | 0.306 | 0.454 |
| B | 53 | **4 (7.5%)** | 0.262 | 0.786 |

**Scope and status of this threshold, stated explicitly:**

- **It is a project-defined structural validation threshold for this corpus.** It is not an
  externally validated constant, not drawn from a published standard, and must not be
  described as one.
- **C6 is a corpus/chunk coherence check, not an experimental retrieval-performance metric.**
  It asks only whether the chunker duplicated content. It says nothing about how BM25 or
  RAG will perform, and no C6 result may be used as evidence about either system.
- Restricting the comparison to a **single document** is deliberate. Two documents that
  agree on a section heading are consistent documentation, not a chunking fault. Measured
  cross-document 8-gram containment is substantial (0.3–0.45) and is expected.
- A positive control is enforced in `tests/test_benchmark_spec.py`: the measure is shown to
  **fail** on a genuine verbatim duplicate and to **pass** on identical text in two different
  documents. A measure that only ever returned zero would be worthless, and this test
  prevents that from going unnoticed.

### What B actually does wrong

All four flagged B pairs are the same pattern: a full chunk followed by a short ragged
remainder. For example, in `DOC-PRD-A-01-v2`, a 597-word chunk is followed by a 109-word
tail whose shingles are 75.8% contained in the preceding chunk. With a 100-word overlap
window, almost the whole tail restates what came immediately before it. B's smaller chunk
target produces more of these short tails; A's larger target produces fewer, and A's worst
pair reaches only 0.454. This is real, explainable duplication, which is exactly what C6
exists to catch.

---

## 5. Basis for freezing 1000/200

**Frozen on C1–C8 structural grounds: A is the only candidate that satisfies every
criterion.** B fails C6 at 6.3% against a 2% limit.

This is a stronger basis than the tie-break originally anticipated, and it is still not a
performance basis. C6 measures duplication introduced by the chunker; it is a property of
the chunker alone and is computable without running either retrieval system.

**Explicitly forbidden going forward:**

- Switching to 600/100 on the basis of anticipated or observed retrieval performance. Finer
  granularity can favour embedding retrieval, which is a reason to withhold that change, not
  to make it.
- Re-tuning chunk size or overlap after any BM25 or RAG result is seen.
- Relaxing the C6 threshold to admit a configuration.

---

## 6. State

- C6 measure: **frozen** at same-document 8-gram containment > 0.5, <2% of chunks.
- Chunking configuration: **frozen** at 1000 / 200.
- C8 remains the hard halt for the final corpus.

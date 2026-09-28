# Mechanism Sample Validation Report

Model: `v1-schema-sample` · seed `20260928` · created 2026-09-28

## 1. Source-model structural validation

| Check | Result | Detail |
|---|---|---|
| V1 | PASS |  |
| V2 | PASS |  |
| V3 | PASS |  |
| V3b | PASS |  |
| V4 | PASS *(scale target, not applicable at sample size)* | actual: 3 |
| V5 | PASS |  |
| V6 | PASS |  |
| V6b | PASS |  |
| V7 | PASS |  |
| V8 | PASS |  |
| V9 | PASS *(scale target, not applicable at sample size)* | actual: 5 explicit, 5 implicit, 10 total |

## 2. Rendering

- Documents: **34**
- Total words: **3046**
- Document links: **69**
- Superseded: **3**

| Document type | Count |
|---|---:|
| component_doc | 6 |
| decision_log | 2 |
| feature_spec | 8 |
| meeting_notes | 2 |
| pbi | 9 |
| prd | 4 |
| runbook | 1 |
| ticket | 2 |

## 3. Determinism

- Model rebuilt identically: **True**
- Rendering byte-identical: **True**
- Chunking byte-identical: **True**

## 4. Chunk provenance

- Chunks with no entity provenance: **0**
- Distinct entities reachable through chunk provenance: **38**
- Every requirement has a subject chunk: **False**
- Every PBI has a subject chunk: **True**

## 5. Link-type coverage

| Link type | Count |
|---|---:|
| `blocks` | 1 |
| `contextualises` | 27 |
| `defines` | 16 |
| `depends_on` | 2 |
| `implements` | 20 |
| `supersedes` | 3 |

- Declared but not exercised: **none**

## 6. Ground-truth derivation

- Derived from model only: **yes** (no retrieval, no LLM, no re-reading chunk text)
- Traceability problems: **none**
- Measured overlap: **42.9%** → band **easy** (slot targeted `hard`)
- Relevant chunk IDs resolved: **2**

> The band disagreement above is the intended demonstration. The slot targeted `hard` and the measurement returned a different band, because lexical overlap is a property of wording plus corpus, not a property of the slot label.

## 7. Chunking coherence

### Primary 1000 / 200

- **C1 PASS** — No chunk splits a sentence (exact contiguous-unit test)
  - 0/34 chunks split a unit (threshold 0%)
- **C2 PASS** — Dependency statements not split within a document
  - 0 split of 5 explicit (10 declared; implicit ones have no corpus text to split) (threshold 0)
- **C3 PASS** — Requirement statements not split within a document
  - 0 split of 5 requirements (2 legitimately appear in both a superseded and a current version) (threshold 0)
- **C4 PASS** — Every chunk carries an entity ID
  - 0 without provenance of 34 (threshold 0)
- **C5 FAIL** — Orphan chunks under 50 words (threshold calibrated for full-corpus scale)
  - 12/34 chunks under 50 words = 35.3%; concentrated in component_doc, decision_log, meeting_notes, pbi, ticket. SAMPLE-SCALE ARTEFACT: these document types are well below the approved full-corpus length targets, so this is not yet a corpus-level result. See project_scaling() for the projection and the full corpus for the measurement. (threshold <3%)
- **C6 PASS** — Near-duplicate chunks within a document
  - 0 pairs = 0.0% (threshold <2%)
- **C7 PASS** — Every document produces at least one chunk
  - 34/34 (threshold 100%)
- **C8 PASS** — Every ground-truth document ID resolves to >=1 chunk
  - 34/34 reachable (threshold 100%)

### Comparison 600 / 100

- **C1 PASS** — No chunk splits a sentence (exact contiguous-unit test)
  - 0/34 chunks split a unit (threshold 0%)
- **C2 PASS** — Dependency statements not split within a document
  - 0 split of 5 explicit (10 declared; implicit ones have no corpus text to split) (threshold 0)
- **C3 PASS** — Requirement statements not split within a document
  - 0 split of 5 requirements (2 legitimately appear in both a superseded and a current version) (threshold 0)
- **C4 PASS** — Every chunk carries an entity ID
  - 0 without provenance of 34 (threshold 0)
- **C5 FAIL** — Orphan chunks under 50 words (threshold calibrated for full-corpus scale)
  - 12/34 chunks under 50 words = 35.3%; concentrated in component_doc, decision_log, meeting_notes, pbi, ticket. SAMPLE-SCALE ARTEFACT: these document types are well below the approved full-corpus length targets, so this is not yet a corpus-level result. See project_scaling() for the projection and the full corpus for the measurement. (threshold <3%)
- **C6 PASS** — Near-duplicate chunks within a document
  - 0 pairs = 0.0% (threshold <2%)
- **C7 PASS** — Every document produces at least one chunk
  - 34/34 (threshold 100%)
- **C8 PASS** — Every ground-truth document ID resolves to >=1 chunk
  - 34/34 reachable (threshold 100%)

### Config selection

Both configurations produce an identical chunk layout on this sample, because no sample document exceeds 239 words and therefore fits in one chunk at either size. **The sample cannot discriminate between them.** Primary 1000/200 is carried forward on the approved 289-chunk projection, and the comparison must be repeated on the full corpus before the freeze.

## 8. Scale projection

- Projected documents: **272** (approved 272)
- Projected chunks: **292** (approved target 289)
- Projected orphans: **0** = 0.00%

> Projection from approved word-count targets only, using the real packer. Not a measured corpus result. C5 must be re-measured on the generated corpus.


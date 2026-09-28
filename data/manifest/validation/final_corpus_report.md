# Final corpus validation report (v1-final-corpus)

Built 2026-09-28. Model `v1-final-corpus` · seed `20260928`.

## 1. Source-model invariants (V1-V9)

| Check | Result | Detail |
|---|---|---|
| V1 | PASS |  |
| V2 | PASS |  |
| V3 | PASS |  |
| V3b | PASS |  |
| V4 | PASS | actual: 12 |
| V5 | PASS |  |
| V6 | PASS |  |
| V6b | PASS |  |
| V7 | PASS |  |
| V8 | PASS |  |
| V9 | PASS | actual: 104 explicit, 104 implicit, 208 total |

## 2. Corpus cardinality (approved targets)

| Type | Actual | Approved |
| --- | ---: | ---: |
| component_doc | 18 | 18 | PASS
| decision_log | 16 | 16 | PASS
| feature_spec | 29 | 29 | PASS
| meeting_notes | 24 | 24 | PASS
| pbi | 120 | 120 | PASS
| prd | 17 | 17 | PASS
| runbook | 8 | 8 | PASS
| ticket | 40 | 40 | PASS
| **total** | **272** | **272** | PASS
- Dependencies: **208** (104 explicit / 104 implicit)
- Conflicts: **12** (7 resolved / 5 unresolved)
- Document links: **543**

## 3. Determinism (two independent builds)

- Model byte-identical: **True**
- Rendering byte-identical: **True**
- Chunking byte-identical: **True**

## 4. Chunking coherence

### Primary 1000/200

- **C1 PASS** - No chunk splits a sentence (exact contiguous-unit test)
  - observed 0/272 chunks split a unit (threshold 0%)
- **C2 PASS** - Dependency statements not split within a document
  - observed 0 split of 104 explicit (208 declared; implicit ones have no corpus text to split) (threshold 0)
- **C3 PASS** - Requirement statements not split within a document
  - observed 0 split of 16 requirements (12 legitimately appear in both a superseded and a current version) (threshold 0)
- **C4 PASS** - Every chunk carries an entity ID
  - observed 0 without provenance of 272 (threshold 0)
- **C5 PASS** - Orphan chunks under 50 words (threshold calibrated for full-corpus scale)
  - observed 3/272 chunks under 50 words = 1.1%; concentrated in pbi, runbook. SAMPLE-SCALE ARTEFACT: these document types are well below the approved full-corpus length targets, so this is not yet a corpus-level result. See project_scaling() for the projection and the full corpus for the measurement. (threshold <3%)
- **C6 PASS** - Near-duplicate chunks within a document (8-gram containment)
  - observed 0 pairs = 0.0% (threshold <2% of chunks (pair overlap >0.5))
- **C7 PASS** - Every document produces at least one chunk
  - observed 272/272 (threshold 100%)
- **C8 PASS** - Every ground-truth document ID resolves to >=1 chunk
  - observed 272/272 reachable (threshold 100%)

### Comparison 600/100

- **C1 PASS** - No chunk splits a sentence (exact contiguous-unit test)
  - observed 0/272 chunks split a unit (threshold 0%)
- **C2 PASS** - Dependency statements not split within a document
  - observed 0 split of 104 explicit (208 declared; implicit ones have no corpus text to split) (threshold 0)
- **C3 PASS** - Requirement statements not split within a document
  - observed 0 split of 16 requirements (12 legitimately appear in both a superseded and a current version) (threshold 0)
- **C4 PASS** - Every chunk carries an entity ID
  - observed 0 without provenance of 272 (threshold 0)
- **C5 PASS** - Orphan chunks under 50 words (threshold calibrated for full-corpus scale)
  - observed 3/272 chunks under 50 words = 1.1%; concentrated in pbi, runbook. SAMPLE-SCALE ARTEFACT: these document types are well below the approved full-corpus length targets, so this is not yet a corpus-level result. See project_scaling() for the projection and the full corpus for the measurement. (threshold <3%)
- **C6 PASS** - Near-duplicate chunks within a document (8-gram containment)
  - observed 0 pairs = 0.0% (threshold <2% of chunks (pair overlap >0.5))
- **C7 PASS** - Every document produces at least one chunk
  - observed 272/272 (threshold 100%)
- **C8 PASS** - Every ground-truth document ID resolves to >=1 chunk
  - observed 272/272 reachable (threshold 100%)

## 5. Ground truth: all 32 slots, final mode (`--against-final`)

- Specification problems: **none**
- Broken references: **0**
- Unresolved slots: **0**

| Slot | Category | Docs | Rel. basis | Note |
|---|---|---:|---|---|
| Q-01 | information_retrieval | 10 | current |  |
| Q-02 | information_retrieval | 8 | current |  |
| Q-03 | information_retrieval | 24 | current |  |
| Q-04 | information_retrieval | 16 | current |  |
| Q-SUP-1 | information_retrieval | 1 | current | D5 distractor: superseded predecessor DOC-PRD-M-01 |
| Q-05 | information_retrieval | 20 | current | colloquial register; lowest lexical overlap target |
| Q-06 | feature_context | 1 | current |  |
| Q-SUP-3 | feature_context | 1 | current | historical limit ['2,500.', 'ersion 1.0,'] differs from curr |
| Q-07 | feature_context | 1 | current |  |
| Q-08 | feature_context | 1 | current |  |
| Q-SUP-2 | feature_context | 2 | both | claim stated in superseded DOC-FEAT-M-01; authoritative curr |
| Q-09 | dependency_identification | 24 | current | stated in prose in the feature specification |
| Q-10 | dependency_identification | 22 | current | stated in the technical component document |
| Q-11 | dependency_identification | 22 | current | explicit ordering constraint between stages |
| Q-12 | dependency_identification | 22 | current | stated dependency on an external party |
| Q-13 | dependency_identification | 22 | current | not stated in prose; encoded in the model, requires context |
| Q-14 | dependency_identification | 23 | current | ordering implied by the model, not written down |
| Q-15 | dependency_identification | 22 | current | spans two features; only inferable from context |
| Q-16 | dependency_identification | 8 | current | evidence sits in a runbook, not in the feature prose |
| Q-17 | cross_document_reasoning | 24 | current | dependency and its target both inside one document |
| Q-18 | cross_document_reasoning | 24 | current | target and dependency are in different documents |
| Q-19 | cross_document_reasoning | 24 | current | relationship recoverable from meeting notes |
| Q-20 | cross_document_reasoning | 23 | current | ordering inferred from PRD sequence |
| Q-21 | cross_document_reasoning | 12 | current | evidence in superseded ['DOC-PRD-M-02'] |
| Q-22 | conflict_identification | 3 | current | resolved conflict |
| Q-23 | conflict_identification | 2 | current | unresolved conflict |
| Q-24 | conflict_identification | 3 | current | resolution recorded only in a later document version |
| Q-25 | backlog_analysis | 16 | current | documented prioritisation decision, not a dependency questio |
| Q-26 | backlog_analysis | 1 | current | stated non-goal |
| Q-27 | backlog_analysis | 2 | both | rationale behind a changed decision |
| Q-28 | backlog_analysis | 1 | current | deprioritisation documented |
| Q-29 | backlog_analysis | 2 | current | synthesis across a feature and its decision record |

## 6. The seven former corpus requirements (freeze checklist B)

- **Q-05: RESOLVED**
- **Q-SUP-3: RESOLVED**
- **Q-10: RESOLVED**
- **Q-11: RESOLVED**
- **Q-14: RESOLVED**
- **Q-20: RESOLVED**
- **Q-21: RESOLVED**

## 7. Twenty-item validation checklist

| # | Item | Result |
|---|---|---|
| 1 | V1-V8 source-model invariants | PASS |
| 2 | V9 dependency scale (104 explicit / 104 implicit / 208 total) | PASS |
| 3 | Superseded document count = 12 | PASS |
| 4 | Corpus cardinality = 272 documents | PASS |
| 5 | Per-type counts match the approved targets | PASS |
| 6 | Conflicts = 12 with 7 resolved / 5 unresolved | PASS |
| 7 | No broken document references (543 links resolvable) | PASS |
| 8 | Determinism: model serialisation byte-identical | PASS |
| 9 | Determinism: rendered documents byte-identical | PASS |
| 10 | Determinism: chunking byte-identical | PASS |
| 11 | C1 no sentence split at chunk boundary | PASS |
| 12 | C2 dependency statements never split | PASS |
| 13 | C3 requirement statements never split | PASS |
| 14 | C4 every chunk carries entity provenance | PASS |
| 15 | C5 orphan chunks under 50 words below 3% | PASS |
| 16 | C6 no near-duplicate chunks within a document | PASS |
| 17 | C7 every document yields >=1 chunk | PASS |
| 18 | C8 every ground-truth document reachable | PASS |
| 19 | Ground truth: zero broken references | PASS |
| 20 | Ground truth: all 32 slots resolved (final mode) | PASS |

## Verdict

**PASS - the final corpus is freezable on every check.**

The corpus, its dependencies, chunks, and ground truth are all deterministic;
the seven former corpus requirements (Q-05, Q-SUP-3, Q-10, Q-11, Q-14, Q-20,
Q-21) and all 32 benchmark slots resolve against the resulting documents. The
corpus is ready for the BM25 and RAG comparison.

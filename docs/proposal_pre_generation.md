# Pre-Generation Specification — Final Seven Items

**Status:** Awaiting approval. No corpus generated, no query set generated, no BM25, no
RAG, no results.
**Date:** 2026-09-28

Covers: 32-query distribution · explicit/implicit · difficulty · superseded queries ·
embedding model · final source-of-truth schema · chunking validation.

---

## 1. Exact 32-query category distribution

| # | Category | Queries | Easy | Moderate | Hard |
|---|---|---|---|---|---|
| 1 | Information retrieval | 6 | 3 | 2 | 1 |
| 2 | Feature context | 5 | 2 | 2 | 1 |
| 3 | Dependency identification | 8 | 2 | 3 | 3 |
| 4 | Cross-document reasoning | 5 | 1 | 1 | 3 |
| 5 | Conflict identification | 3 | 1 | 1 | 1 |
| 6 | Backlog analysis | 5 | 2 | 2 | 1 |
| | **Total** | **32** | **11** | **11** | **10** |

Sums: categories 6+5+8+5+3+5 = **32**. Difficulty 3+2+2+1+2+1+1+2 = **11 easy**,
2+2+3+1+1+2 = **11 moderate**, 1+1+3+3+1+1 = **10 hard**. Total **32**.

**Why the hard queries are concentrated where they are.** 6 of the 10 hard queries sit in
dependency identification and cross-document reasoning. This is deliberate. If hard
queries clustered in information retrieval, the experiment would measure lexical mismatch
rather than reasoning, and the result would flatter whichever system tolerates paraphrase.
The difficulty is placed where the research question is.

### Per-category difficulty rationale

| Category | Why this spread |
|---|---|
| Information retrieval | Mostly easy — this is the capability both systems share. One hard query confirms the category is not trivial. |
| Feature context | Mixed. "What did we decide about X" is often lexically close; "why did we rule out Y" is not. |
| Dependency identification | 3 hard. Explicit dependencies are findable by keyword; the hard ones require reading across documents. |
| Cross-document reasoning | 3 of 5 hard. Structural: these questions cannot be answered from any single document, so low overlap is intrinsic rather than contrived. |
| Conflict identification | One each. Probing contradictions is inherently multi-document. |
| Backlog analysis | Mostly easy/moderate — synthesis questions usually restate documented rationale. |

---

## 2. Explicit / implicit dependency confirmation

**13 dependency-related queries** = all 8 dependency identification + all 5 cross-document
reasoning.

| Category | Total | Explicit | Implicit |
|---|---|---|---|
| Dependency identification | 8 | 4 | 4 |
| Cross-document reasoning | 5 | 2 | 3 |
| **Total** | **13** | **6** | **7** |

**Non-dependency queries: 19** (information retrieval 6, feature context 5, conflict
identification 3, backlog analysis 5). 13 + 19 = **32**.

### Definitions, as approved

**Explicit** — the dependency is directly stated in the relevant documentation.
**Implicit** — the dependency is **not** directly stated in the relevant documentation,
but the relationship is explicitly encoded in the structured source-of-truth model and is
therefore objectively evaluable.

**"Implicit" describes what the documents say, never what the model knows.** An implicit
dependency is always derivable from the model. It never means the system should apply
common sense and a human should then decide whether the answer looks reasonable. There is
no judgement step anywhere in the label.

### Design constraint on the other 19

Backlog analysis naturally invites dependency reasoning ("what should we build next?").
To keep the split at exactly 13, backlog queries are framed around **documented rationale
and requirement priority** — what the decision records say, what the requirements state —
not around dependency discovery. If a drafted backlog query turns out to need dependency
reasoning to answer, it is **relabelled into the dependency-related set before the run**,
not after. This is a pre-system correction, recorded in the decision log.

### Reporting

Results reported separately for the 6 explicit and 7 implicit queries. The 7-query implicit
subset is **descriptive evidence only** — enough to indicate direction, not enough to
support a statistical claim, and the thesis will say so.

---

## 3. Difficulty distribution confirmation

**Measure** (already implemented and printed by `build_sample_run.py`):

```
overlap = |content_words(Q) ∩ content_words(G)| / |content_words(Q)|
content_words = lowercased, stopword-removed, length > 2
```

| Band | Overlap | Target count |
|---|---|---|
| Easy | ≥ 40% | 11 |
| Moderate | 20–39% | 11 |
| Hard | < 20% | 10 |
| | | **32** |

**Status of these numbers: targets, not achieved facts.** They are what the query set is
*designed* to produce. The actual distribution is measured against the generated corpus and
reported. If it differs materially, query wording or labels are corrected **before** either
system is evaluated.

### Required framing for the methodology section

Lexical overlap is a **benchmark-construction measure**. It creates controlled variation in
lexical alignment between a query and the information that answers it. It is **not** a
validated psychological or cognitive measure of task difficulty, and must not be described
as one. A "hard" query here means low lexical alignment with its target — not that it is
hard for a person or cognitively demanding.

**Frozen before either system is evaluated.** No reclassification after seeing BM25 or RAG
performance.

### Superseded-query difficulty placement

| Query | Band | Why |
|---|---|---|
| Q-SUP-1 "Which PRD is in production?" | moderate | Query vocabulary overlaps the current PRD's own wording |
| Q-SUP-2 "A spec says X — which document, and is it current?" | hard | The target claim lives in a *superseded* document, so overlap with the current version is deliberately low |
| Q-SUP-3 "What is the current approval limit?" | easy | Maps closely onto a specific current specification |

These are placed within the existing category budgets in §1 and require no change to the
totals.

---

## 4. Superseded-query allocation

12 superseded documents: 7 PRD `v1` → `v2`, 5 feature-spec `v1` → `v2`.

**3 of 32 queries.** They occupy slots inside existing categories — they are **not**
additional queries.

| ID | Query | Category | Ground truth | Role of the superseded version |
|---|---|---|---|---|
| Q-SUP-1 | Which PRD is in production, and what changed? | Information retrieval | current `v2` | `v1` is a **distractor** — tests recency preference |
| Q-SUP-2 | A specification says tax is collected at first login. Which document states this, and is it still current? | Feature context | `v1` **and** `v2` | `v1` is **relevant** — the question is about what a document said |
| Q-SUP-3 | What is the current approved limit for bulk approval? | Feature context | current spec | `v1` holds a **different, superseded** limit — a lexical near-perfect trap |

**Q-SUP-2 exists to defeat a degenerate strategy.** A benchmark where "always retrieve the
newest document" is always correct tests date filtering, not version reasoning. Including
one query where the superseded document is the correct answer is what makes the category
measure something.

**No manufactured ambiguity.** If a version query proves ambiguous, it is rephrased or
dropped. Difficulty is not to be manufactured for its own sake.

---

## 5. Proposed embedding model

### Recommendation: `text-embedding-3-large`, native 3072 dimensions

### Verification status

> **I cannot verify this from the available project information.**

`openai` and `chromadb` are **not installed** and **`OPENAI_API_KEY` is not set** in the
current environment, so I could not confirm live model availability or run a compatibility
test. I have not claimed otherwise.

To verify before freezing, run:

```bash
pip install openai chromadb
export OPENAI_API_KEY="..."
python - <<'PY'
import os
from openai import OpenAI
client = OpenAI()
models = client.models.list()
names = sorted(m.id for m in models.data if "embedding" in m.id)
print("available embedding models:", names)
r = client.embeddings.create(
    model="text-embedding-3-large",
    input="chunking coherence check",
    encoding_format="float32",
)
print("dim:", len(r.data[0].embedding))
print("usage:", r.usage)
PY
```

Expected: `dim: 3072`. If the model is absent or returns a different dimension, **stop and
report back** rather than substituting silently.

### Why `text-embedding-3-large`

**1. Cost is not a reason to choose the smaller model.** The corpus is ~289 chunks ×
~250 tokens ≈ **72,000 tokens**. At $0.13 / 1M tokens that is roughly **$0.009** for a full
corpus embedding. Even 20 repeat runs total about $0.18. Choosing
`text-embedding-3-small` to save roughly $0.008 would be a false economy that measurably
weakens the arm of the study.

**2. With n=32, I cannot afford to handicap RAG.** This study cannot support significance
testing. If a deliberately weaker embedder produced a null result, the finding would be
about my model choice, not about RAG. A small-corpus, underpowered design needs its
strongest reasonable configuration, or a null result is uninterpretable.

**3. The bias runs in the conservative direction.** This choice deliberately favours the
RAG arm. That is the defensible direction: selecting a weaker embedder to make the keyword
baseline look relatively better would be the biasing choice. The choice and its rationale
are disclosed in the methodology.

**4. Retrieval quality is the variable under study.** `text-embedding-3-large` is
substantially stronger than `-small` on retrieval benchmarks, and retrieval quality is
precisely what System B is being asked to demonstrate.

### Configuration to freeze

| Setting | Value | Note |
|---|---|---|
| Model | `text-embedding-3-large` | Exact string, no alias |
| Dimensions | native 3072 | **Do not set the `dimensions` parameter.** Matryoshka truncation would add a free parameter that could be mistaken for tuning |
| `encoding_format` | `float32` | Consistent with the NumPy cross-check |
| Batch size | fixed, recorded | Documented per run |

**Do not change after seeing results.**

### Reproducibility limitation — must be disclosed

OpenAI does **not** version-pin embedding models. There is no
`text-embedding-3-large-2024-xx-xx` identifier, so there is no immutable snapshot to pin.
If the provider changes the model, a re-run produces different vectors. This is a genuine
reproducibility threat and belongs in the limitations section.

**Mitigation: cache the embedding matrix in the repository.** Store the vectors as a
committed derived artefact (`.npy` plus a metadata JSON recording model name, dimension
count, corpus version, chunking config, and embedding timestamp). Re-runs and re-analysis
then reuse byte-identical vectors, so the experiment remains reproducible even though the
model itself is not pinable.

### Documented alternative

If you prefer the conventional default: `text-embedding-3-small`, 1536 dimensions,
$0.02 / 1M tokens. It is what most production RAG systems use, which makes the study more
representative of typical practice. The trade-off is a weaker retriever in System B. Either
choice is defensible provided it is frozen before the run — but only one can be.

---

## 6. Final source-of-truth schema

### Changes required from the v0 sample schema

| # | Change | Reason |
|---|---|---|
| 1 | **Generalise version lineage to both PRDs and feature specs** with a uniform field set | Q7 requires version metadata on all 12 superseded documents. `Feature` currently has **no version fields at all** — only `Requirement` does. |
| 2 | **Add `is_current` as a single authoritative flag**, enforced by a validator | Q7: "the current version must be objectively identifiable". Currently the only signal is `is_superseded` on `Requirement`, which is negative and easy to get wrong. |
| 3 | **Add `DocumentLink` as a first-class entity** | Makes the ~435 reference edges a countable property of the model rather than a side effect of rendering, and lets distractors be *declared* rather than hoped for. |
| 4 | **Add `confusable_with` to `Feature` and `adjacent_component_ids` to `TechnicalComponent`** | Q6 requires distractors established by construction. Declared adjacency makes D1/D2/D3 reproducible instead of emergent. |
| 5 | **Remove `formal_term` / `colloquial_terms` from `Pbi`** | `Pbi` duplicates `Feature`'s vocabulary fields. Two sources of truth for the same lexical-divergence control will drift, and drift would silently corrupt the central experimental control. `Pbi` should inherit from its feature. |
| 6 | **Remove the `_rendered_documents` dynamic-attribute hack** in `SourceModel.documents_for_entity` | `getattr(self, "_rendered_documents", [])` silently returns `[]` if the attribute was never set, so the function can fail quietly and return no provenance. `DocumentLink` replaces it. |

### Version lineage (new, uniform across PRDs and feature specs)

Applied identically to `Requirement` and `Feature`:

| Field | Type | Meaning |
|---|---|---|
| `version` | `str` | e.g. `"2.0"` |
| `status` | `Literal["current","superseded"]` | Explicit, not inferred from dates |
| `created_date` | ISO date | |
| `modified_date` | ISO date | |
| `superseded_by` | `str` | `document_id` of the newer version; `""` iff current |
| `supersedes` | `str` | `document_id` of the older version; `""` iff first version |
| `is_current` | `bool` | **The single authoritative flag.** Exactly one `True` per feature / requirement |

### `DocumentLink` (new entity)

```python
@dataclass
class DocumentLink:
    link_id: str
    from_document_id: str
    to_entity_type: Literal["product","feature","requirement","pbi","component"]
    to_entity_id: str
    link_type: Literal[
        "defines",        # PRD/spec defines a feature
        "implements",     # PBI/ticket implements a feature
        "depends_on",     # a document-level dependency statement
        "supersedes",     # version lineage
        "contextualises", # D1/D2 distractor: nearby but not the answer
        "blocks",
    ]
```

`contextualises` is what makes distractors **declared**. A D1 distractor is a
`contextualises` link from a document about feature X to feature Y, where Y shares
vocabulary with X. Because it is in the model, its non-relevance is objectively derivable —
which is exactly what Q6 requires and what a hand-judged distractor set cannot provide.

### Unchanged, and deliberately so

`Product` (with `documentation_maturity` — the CA2 §3 control) · `Feature` (`formal_term`,
`colloquial_terms`) · `Requirement` (`is_normative`) · `Pbi` · `TechnicalComponent` ·
`Ticket` · `DecisionRecord` · `MeetingNote` · `Runbook` · `Dependency` (with
`is_explicit_in_docs`) · `Conflict` (with `is_resolved`).

### Validation invariants to enforce at generation time

| # | Invariant |
|---|---|
| V1 | Exactly one `is_current=True` per feature and per requirement |
| V2 | Every `is_current=False` entity has a non-empty `superseded_by` that resolves to a real document |
| V3 | Every `is_current=True` entity has `superseded_by == ""` |
| V4 | Exactly 12 documents have `is_current=False` (7 PRD, 5 spec) |
| V5 | Every `DocumentLink` endpoint resolves to a real document and entity |
| V6 | Every `confusable_with` target is a real feature, is **not** self, and is in the same product |
| V7 | No `Dependency` has `from_id == to_id` |
| V8 | Every rendered document has ≥ 1 `DocumentLink` and a resolvable `source_entity_id` |
| V9 | Exactly 104 explicit and 104 implicit dependencies (targets — actual reported) |

V1–V3 are what make "the current version is objectively identifiable" a checkable claim
rather than an assurance.

---

## 7. Proposed chunking validation procedure

**Sequence position:** after query design and difficulty validation, before the
configuration freeze. Before any system runs.

### 7.1 Splitter decision, made now, before any data exists

**Propose a structure-aware splitter, not a fixed character window:**

1. Split on markdown heading boundaries.
2. Pack sections into chunks up to 1000 words.
3. If a single section exceeds 1000 words, split at sentence boundaries.
4. Apply 200-word overlap at the sentence level.

**Why this is necessary rather than preferential.** Ground truth attaches to chunks by
provenance propagation. A naive fixed window splits a dependency statement or a requirement
across a boundary, and the required fact then sits in a chunk that does not carry the
entity's ID. That produces an unscoreable label and a retrieval system that cannot be
credited for retrieving it. With short documents (PBIs 60–130 words, tickets 80–160) most
of the corpus is unaffected either way — the difference matters for the long PRDs, which
are exactly the documents that carry the richest dependency statements.

**Rule: no chunk begins or ends mid-sentence.**

### 7.2 Pilot checks with pre-specified thresholds

Run on the v1 corpus. Thresholds are fixed **now**, before seeing any output, so the
decision to change the splitter cannot be driven by downstream performance.

| # | Check | Threshold | If failed |
|---|---|---|---|
| C1 | Chunks beginning or ending mid-sentence | 0% | Fix splitter |
| C2 | Dependency descriptions split across a boundary | **0** | Fix splitter or raise chunk size |
| C3 | Requirement statements split across a boundary | **0** | Fix splitter or raise chunk size |
| C4 | Chunks with no entity ID in metadata | 0 | Fix provenance |
| C5 | Orphan chunks under 50 words | < 3% of chunks | Merge into predecessor |
| C6 | Chunks > 90% duplicate of another | < 2% | Reduce overlap |
| C7 | Every document yields ≥ 1 chunk | 100% | Fix splitter |
| C8 | Every ground-truth document ID resolves from ≥ 1 chunk | **100%** | **Critical failure — halt** |

**C8 is the critical one.** If a ground-truth document maps to no chunk, its label cannot
be scored, and the query's ground truth is broken.

### 7.3 Sensitivity comparison

Because A4 (chunk size) is still unconfirmed, the pilot evaluates two configurations:

- **Primary:** 1000 words / 200 overlap
- **Comparison:** 600 words / 100 overlap

Both are scored on the coherence checks above. The coherence metrics, **not** any BM25 or
RAG score, decide which is used. Both results are recorded.

**Why this is legitimate pre-registration.** Choosing a chunking configuration on
structural-coherence grounds, before any retrieval system exists, is experimental design.
Choosing it on BM25 or RAG scores would be result-tuning. The distinction is temporal, and
it is why this step sits where it does in the sequence.

### 7.4 Freeze

1. Record both pilots' metrics in the decision log.
2. State the decision and its reason.
3. Write the frozen config to `experiments/configs/` and commit it.
4. Both systems consume **identical chunk IDs** from the same frozen corpus. The chunking
   policy is not a variable between BM25 and RAG.

### 7.5 Disclosed limitation

Chunking parameters are validated on **coherence only**. They are not tuned for retrieval
quality, and the thesis will state that chunk size was fixed on structural grounds and never
optimised against either system's scores.

---

## 8. Frozen-sequence confirmation

Per the approved research-integrity sequence:

```
SOURCE-OF-TRUTH DESIGN      ← schema in §6 above, awaiting approval
        ↓
CORPUS GENERATION           ← 272 docs, targets measured and reported after
        ↓
GROUND TRUTH                ← derived from model only
        ↓
QUERY DESIGN                ← 32, distribution in §1
        ↓
DIFFICULTY VALIDATION       ← measured overlap, §3
        ↓
CHUNKING PILOT              ← §7, coherence thresholds pre-specified
        ↓
CONFIGURATION FREEZE        ← chunking + embedding model + BM25 params
        ↓
BM25 + RAG EXPERIMENT       ← not yet implemented
        ↓
RESULTS
        ↓
ANALYSIS
```

Nothing in this document has been executed. On approval, the next step is the structured
source-of-truth sample and a small rendered corpus sample — still not the full corpus, and
still no BM25 or RAG.

## 9. Still outstanding

| ID | Item |
|---|---|
| A7 | Embedding model — **proposed, awaiting approval and live verification** |
| A6 | Ethics requirement for the synthetic-only corpus. NCI coordinator/supervisor. Hard gate on all human-participant activity. Documentation must not state a determination either way until confirmed. |

# D6 + D7 — Combined Proposal: Corpus Scale and Query Design

**Status:** PROPOSAL — awaiting student approval. Nothing here has been generated.
**Date:** 2026-09-28
**Decided before results:** Yes. No corpus generated, no query set generated, BM25 not
run, RAG not run, no results exist.

**Preconditions already approved:** D3 (Chroma + NumPy cross-check), Q5 (explicit/implicit
stratification), Q6 (distractor ratio), Q7 (superseded versions).

---

## 1. The design principle that drives every number

Retrieval difficulty is not governed by raw document count. It is governed by the ratio of
**plausible candidates** to **top-k**.

With `k = 5`, a corpus of 20 documents makes finding 5 relevant ones trivial — a keyword
baseline will look excellent, and the experiment will measure nothing. A corpus in which
each query has 20–60 documents that share vocabulary with it, of which only 1–3 are
genuinely relevant, is where the comparison becomes informative.

So every number below is justified by **plausible candidates per query**, and by whether
the ground truth stays hand-auditable. Document count is a consequence of those two
constraints, not the target.

---

## 2. D6 — Proposed corpus scale

### 2.1 Products and features

| Entity | Count | Split | Rationale |
|---|---|---|---|
| Products | 2 | 1 formally documented (Meridian), 1 informally documented (Tally) | This is the CA2 §3 contrast, held constant across both systems. It is the controlled variable, not a variable. |
| Features | 24 | 12 per product | 12 per product is enough to form real topical neighbourhoods (approvals, reporting, access control, notifications…), so a query about one feature always has plausible near-misses. Below ~8, siblings stop being genuine distractors. |
| Business requirements | 16 | 8 per product | Requirement-level dependencies and conflicts need somewhere to attach. |
| Technical components | 18 | across both products | Needed so "which systems does this need" is answerable from technical docs, and so type-D3 distractors (related components that are *not* the required dependency) exist at all. |

### 2.2 Document types and counts

| Type | Current | Superseded | Total docs | Target length (words) | Chunks each | Total chunks |
|---|---|---|---|---|---|---|
| PRD | 10 | 7 | **17** | 900–2,200 | 1–3 | ~34 |
| Feature specification | 24 | 5 | **29** | 400–700 | 1 | ~29 |
| PBI / user story | 120 | 0 | **120** | 60–130 | 1 | ~120 |
| Technical component doc | 18 | 0 | **18** | 300–550 | 1 | ~18 |
| Ticket | 40 | 0 | **40** | 80–160 | 1 | ~40 |
| Decision record | 16 | 0 | **16** | 150–300 | 1 | ~16 |
| Meeting note | 24 | 0 | **24** | 50–110 | 1 | ~24 |
| Runbook | 8 | 0 | **8** | 250–450 | 1 | ~8 |
| **Total** | **260** | **12** | **272** | | | **~289** |

Superseded versions are counted as additional documents beyond the current set, so
`current` and `total` differ.

### 2.3 Relationship structure

| Relationship | Count | Rationale |
|---|---|---|
| Feature-level dependencies | 72 (24 × 3) | Feature A requires feature B. The layer a product manager reasons about. |
| PBI-level dependencies | 120 (120 × 1) | Each PBI depends on a component or another PBI. The layer that makes questions concrete. |
| Requirement-level dependencies | 16 (16 × 1) | Requirement-to-requirement. |
| **Total dependencies** | **~208** | |
| Cross-document reference edges | ~435 | Every PBI → feature + component (240), ticket → PBI + feature (80), PRD → features (17), meeting note → feature/PBI (~36), decision → feature/requirement (~24), spec → product + PRD (29), runbook → component (8). |
| Conflicts | 12 (7 resolved, 5 unresolved) | Gives conflict_identification queries real material and lets "unresolved" be distinguished from "resolved". |
| Superseded versions | 12 (7 PRD v1, 5 spec v1) | Q7. Each has unambiguous `superseded_by` and status in the model. |

### 2.4 Why this scale is sufficient

**Sufficient to create retrieval challenges:**
- ~289 chunks with `k=5` → roughly **58 result pages** of candidates. A query cannot
  succeed by retrieving broadly.
- 24 features across 2 products means every query's target has same-product siblings
  (D1/D2 distractors) and near-miss components (D3 distractors) by construction.
- 120 short PBIs are the bulk of the candidate pool and are the hardest to discriminate,
  because PBI titles are near-identical in form.
- 40 tickets carry the colloquial register, which is where lexical divergence — the
  validity-critical control — actually lives.

**Sufficient to remain feasible for ground-truth validation:**
- Ground truth is *derived* by provenance, not authored per query. A human audits a
  sample and checks derivation logic once, rather than labelling 272 documents.
- 272 documents is auditable end to end in an afternoon. 2,000 would not be.
- All rendering is deterministic, so ground truth is reproducible bit-for-bit and
  independently re-derivable by a marker.

### 2.5 Why this scale is a limitation, stated up front

~289 chunks is **at the small end** of retrieval research. It is defensible here because
the research question is about *documentation analysis for backlog decisions*, not about
retrieval at scale, and small corpora isolate the semantic-vs-lexical difference more
cleanly. But it must be disclosed as a **threat to external validity** alongside the
synthetic-corpus limitation already required by D9.

A3 ("a few hundred chunks is sufficient") is therefore **assumed, not proven**. If the
main experiment returns an ambiguous or null result, the honest response is a
pre-registered second experiment at larger scale — not a retrofit of this corpus after
seeing which way the numbers went.

---

## 3. D7 — Proposed query design

### 3.1 Total: 32 queries

This is **2 above the 20–30 planning range** stated in D7, and I want that deviation to be
explicit rather than quietly absorbed.

**Justification:** Q5 approved stratification by explicit vs implicit dependencies, which
makes this a *comparative* study rather than a demonstration. At 30 queries the implicit
subset lands at 5 observations — too few to report anything beyond a direction. The two
extra queries go to `dependency_identification` and `backlog_analysis` to bring the
implicit subset to 7. If you prefer to hold 30, the honest consequence is that the
explicit/implicit comparison must be reported as descriptive only, with that limitation
stated in the thesis.

**32 cannot support significance testing.** With n=32, no significance claim is
defensible. Results will be reported as descriptive statistics with confidence intervals,
and the thesis will state plainly that the study is underpowered by design — a 32-query
hand-validated set was chosen over a large auto-generated one precisely because ground
truth has to be correct.

### 3.2 Category distribution

| # | Category | Queries | Rationale for the count |
|---|---|---|---|
| 1 | Information retrieval | 6 | Baseline capability. If basic retrieval fails, every downstream comparison is uninformative, so this category carries more weight than its difficulty suggests. |
| 2 | Feature context | 5 | Why a feature exists, what was decided, what was ruled out. Driven by PRDs, specs, and decision records. |
| 3 | Dependency identification | 8 | The research core. Highest count. |
| 4 | Cross-document reasoning | 5 | The capability BM25 structurally lacks. |
| 5 | Conflict identification | 3 | Proportionate to 12 available conflicts; 3 keeps 9 in reserve for held-out or robustness checks. |
| 6 | Backlog analysis | 5 | Synthesis — most expensive per query, and the closest to the real use case. |
| | **Total** | **32** | |

### 3.3 Difficulty definition — measured, not declared

This is the change the small sample forced, and it is the most important part of D7.

**The finding:** in the sample, a query labelled *hard* shared **43%** of its content words
with its target document (`bulk`, `timesheet`, `approval`). It was not a hard query. If
difficulty labels are wrong, the stratified analysis — the most interesting output of the
whole project — is invalid, because it would be comparing systems on categories that do
not exist.

**Definition.** For query `Q` with ground-truth document set `G`:

```
overlap = |content_words(Q) ∩ content_words(G)| / |content_words(Q)|
```

where `content_words` = lowercased, stopword-removed, length > 2. This is the same
measure already implemented and printed in `build_sample_run.py`, so it is not a new
mechanism.

| Label | Overlap |
|---|---|
| easy | ≥ 40% |
| moderate | 20–39% |
| hard | < 20% |

**Target distribution:** 11 easy / 11 moderate / 10 hard.

**Procedure, and why it is not result-tuning.** Query wording is *authored* to target a
band, then *verified* against the generated corpus. If a query lands in the wrong band it
is rephrased or relabelled. This happens **before BM25 or RAG exist**, so no system
performance has been observed. Selecting query wording to hit a target difficulty is
normal benchmark construction; doing it *after* seeing which system wins would be fraud.
The distinction is temporal, and this is why the step is sequenced here.

### 3.4 Explicit vs implicit dependency distribution

13 queries carry a dependency expectation (all 8 `dependency_identification` + all 5
`cross_document_reasoning`).

| | Queries | Share |
|---|---|---|
| Explicit | 6 | 46% |
| Implicit | 7 | 54% |

**On the 54/46 split.** I am proposing a *slight majority implicit*, which cuts against
semantic retrieval rather than for it. Real repositories state many dependencies outright;
skewing implicit would flatter the RAG system in a way that is not representative. But a
heavy explicit skew would make the approved Q5 stratification uninformative, because there
would be little implicit subset to compare against.

Note this split does not depend on the full 13 being split evenly — it is 7/6. The
reason for leaning implicit is that `cross_document_reasoning` queries are inherently
implicit: that is what makes them cross-document.

**Binding constraint carried over from Q5:** implicit dependencies must **not** require
unsupported common-sense inference. Every implicit dependency is explicitly defined in the
structured model; it is "implicit" only with respect to *what the documents say*, never
with respect to whether the model knows it. Ground truth stays reproducible.

**Stated limitation:** 7 implicit queries support a directional statement, not a strong
statistical one. This will be written down as such.

### 3.5 Distractor strategy and distribution

**Ratio target: ~1/3**, operationalised as ≈ 2 distractors per relevant document.

**An honest correction to how this gets counted.** Distractors are **not separately
authored**. They are *produced by the model*: a feature's 11 siblings within its product,
a PBI's near-miss components, the 12 superseded versions, and deliberately
same-terminology/different-feature feature pairs (D2) all generate them as a by-product of
having a structured corpus.

So the 1/3 cannot be honestly *promised* before generation. What can be done — and what I
propose — is:

1. Design the model to produce near-misses in the required proportions.
2. **Measure** the actual ratio after generation, defined as
   `n_distractors / (n_relevant + n_distractors)` over the plausible-candidate set
   (documents sharing ≥1 content word with the query, or in the target feature's product).
3. **Report the measured ratio** and freeze it.
4. If it deviates materially from ⅓, adjust the *model* and regenerate — **before any
   system runs.**

Reporting a fabricated 1/3 in advance would be the kind of number that looks rigorous and
means nothing.

**Approved distractor types, by construction (Q6):**

| Type | Description | Produced by |
|---|---|---|
| D1 | Same terminology, different feature | Sibling features with shared vocabulary |
| D2 | Related features, different requirements | Feature pairs deliberately given overlapping scope |
| D3 | Technically related component that is *not* the required dependency | 18 components with adjacency, of which only some are actual dependencies |
| D4 | Overlapping keywords, insufficient context | Colloquial tickets sharing symptom vocabulary across features |
| D5 | Superseded version of the correct document | Q7 version chain |

**How relevance / non-relevance is established:** by **construction, never by judgement**.
Each distractor's non-relevance is asserted in the model by a differing
`feature_id`/`component_id`/`dependency_id`. Ground truth is derivable, so the distractor
set is auditable rather than subjective.

**Frozen before the experiment** (Q6). Not adjustable after seeing BM25 or RAG output.

### 3.6 Superseded-version strategy

12 superseded documents: 7 PRD `v1` → `v2`, 5 spec `v1` → `v2`.

**Required metadata on every versioned document** (Q7): `document_id`, `feature_id`,
`version`, `status`, `created`/`modified` date, `superseded_by`, `is_current`. The current
version is unambiguous in the model — `is_current` is a single authoritative flag, not an
inference from dates.

**3 of 32 queries involve versions.** Critically, they are not all "prefer the newest":

| Query | Relevant | Role of the superseded version |
|---|---|---|
| Q-SUP-1 — "Which version of the onboarding PRD is in production, and what changed?" | current `v2` | `v1` is a **distractor** — tests recency preference |
| Q-SUP-2 — "A spec says tax is collected at first login. Which document says that, and is it still current?" | `v1` **and** `v2` | `v1` is **relevant** — the question is about what a document said |
| Q-SUP-3 — "What is the current approved limit for bulk approval?" | current spec | `v1` carries a **superseded, different** limit — a lexical near-perfect trap |

Q-SUP-2 exists to defeat the degenerate strategy of "always retrieve the newest
document." A benchmark where newest is always correct tests nothing about version
reasoning, only about date filtering.

**Q7 constraint honoured:** no ambiguity is manufactured for its own sake. If a drafted
version query turns out ambiguous, it is rephrased or dropped — not made harder.

---

## 4. Why these numbers — summary of rationale

| Decision | Primary reason |
|---|---|
| 2 products | The controlled variable from CA2 §3. Held constant, not varied. |
| 24 features (12/product) | Enough siblings for genuine near-miss distractors |
| 272 documents / ~289 chunks | ~58 candidate pages at k=5; still hand-auditable in an afternoon |
| 120 PBIs | The candidate-pool bulk; hardest to discriminate because titles are formulaic |
| 40 tickets | Carries the colloquial register where lexical divergence actually lives |
| 18 component docs | Makes "which systems" answerable, and enables D3 distractors |
| 12 conflicts (7/5 resolved) | Lets resolved and unresolved be distinguished |
| 12 superseded versions | Q7; enough for 3 version queries without repetition |
| ~208 dependencies (104 explicit / 104 implicit) | Supports Q5 stratification at the model level |
| ~435 reference edges | Makes cross-document reasoning structurally possible, not incidental |
| 32 queries | Enough to stratify Q5; still hand-validatable; explicitly underpowered |
| Measured difficulty | The sample showed hand-assigned labels are unreliable |
| 54/46 implicit/explicit | Slight lean implicit, chosen to cut against the RAG system |
| ~1/3 distractors | Q6, but **measured** after generation rather than promised now |
| 3 version queries | Q7, including one where the superseded doc is the correct answer |

---

## 5. What happens on approval

1. Freeze this document and the measured distractor ratio into `DECISIONS.md` as `D-003`.
2. Generate the corpus at the approved scale, writing `source_model.json` and Markdown
   documents to `data/synthetic/v1-corpus/` (new version directory; the sample is
   untouched).
3. Chunk, then **verify** chunk counts against the estimates in §2.2.
4. Run the pilot for A4 (chunk size 1000/200) and report actual recall behaviour.
5. Generate the query set, then **verify** the measured difficulty distribution and
   report it. Adjust wording or labels if the distribution is wrong — still before any
   retrieval system exists.
6. Freeze corpus, queries, and distractor ratio in version control. Only then implement
   BM25 and RAG.

## 6. Still outstanding (not resolved by this proposal)

| ID | Item |
|---|---|
| A7 | Exact OpenAI embedding model name. Must be frozen before the comparison runs. |
| A4 | Chunk size 1000 / overlap 200. This proposal assumes it; the pilot verifies it. |
| A6 | Whether ethics approval is required for the synthetic-only corpus. NCI coordinator/supervisor. Hard gate on all human-participant activity. |

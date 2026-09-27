# Data Design — Structured Synthetic Product Model

**Status:** Proposal. Not implemented, not generated.
**Purpose:** Define the structured source of truth from which the synthetic
documentation corpus, the query set, and the ground-truth labels are all derived.

**Governing principle from `AGENTS.md` §4:**

```
Structured Product Model
        ↓
Ground-Truth Relationships
        ↓
Synthetic Documentation (rendered from the model)
        ↓
Query Set
        ↓
Ground-Truth Evaluation Labels (derived from the model)
        ↓
BM25 + RAG Experiment
```

Labels must come from the **model**. If a label can only be produced by reading
generated prose, the label is not trustworthy.

---

## 1. Why a structured model at all

Generating documents freely and then generating queries and answers from the same
free text produces a circular experiment: an LLM writes the corpus, another LLM reads
it, and a third grades the result. Whatever the outcome, it measures the generator, not
retrieval.

A structured model inverts this. The dependencies, statuses, and relationships are
*asserted first*, in data. Documents are then rendered from that data. Queries are
written against the model. Ground truth is read directly off the model. Retrieval is
then measured against ground truth that the retrieval systems had no role in creating.

This is what makes Precision@5, Recall@5, MRR, and dependency accuracy meaningful.

---

## 2. Entity model (proposed)

Nine entity types. Every entity carries a stable, human-readable ID.

### 2.1 `products`

| Field | Notes |
|---|---|
| `product_id` | e.g. `PROD-A` |
| `name` | |
| `domain` | e.g. workforce analytics, field service |
| `documentation_maturity` | `formal` or `informal` — **load-bearing, see §7** |
| `team_size` | |

### 2.2 `features`

| Field | Notes |
|---|---|
| `feature_id` | `FEAT-A-01` |
| `product_id` | |
| `name` | |
| `status` | `discovered` / `planned` / `in_progress` / `launched` / `deprecated` |
| `formal_term` | the precise technical name, e.g. "Progressive Profiling" |
| `colloquial_terms` | informal phrasings used in prose, e.g. "onboarding ramp" |
| `priority` | |

`formal_term` and `colloquial_terms` exist for the lexical-divergence mechanism in §6.
They are **not** decoration — they are the experimental control.

### 2.3 `requirements` (PRD-level)

| Field | Notes |
|---|---|
| `requirement_id` | `REQ-A-01` |
| `product_id` | |
| `title` | |
| `version` | documents are versioned, as real PRDs are |
| `author_role` | e.g. "Group Product Manager" |
| `created_date` | |
| `sections` | ordered list of section headings + bodies |
| `is_normative` | whether this document is authoritative when documents disagree (§8) |

### 2.4 `pbis`

| Field | Notes |
|---|---|
| `pbi_id` | `PBI-A-014` |
| `product_id` / `feature_id` | |
| `title` | |
| `description` | short, often informal |
| `story_points` | |
| `status` | `to_do` / `in_progress` / `in_review` / `done` |
| `created_date` | |
| `author_role` | e.g. "Product Owner" |
| `formal_term` / `colloquial_terms` | as with features |

### 2.5 `technical_components`

| Field | Notes |
|---|---|
| `component_id` | `COMP-07` |
| `name` | e.g. "Identity Service", "Event Bus", "Payments SDK" |
| `component_type` | `service` / `database` / `queue` / `third_party` |
| `owner_team` | |
| `notes` | |

Third-party components are important — they create dependencies the product team does
not control, which is where a PM's context is most often missing.

### 2.6 `dependencies` — the core of the ground truth

| Field | Notes |
|---|---|
| `dependency_id` | `DEP-031` |
| `from_type` / `from_id` | entity type + id |
| `to_type` / `to_id` | entity type + id |
| `dependency_type` | `blocks` / `depends_on` / `duplicates` / `conflicts_with` / `informs` |
| `description` | natural-language statement |
| `is_explicit_in_docs` | whether any document states this, or it is only inferable |

`is_explicit_in_docs` is a valuable distinction: an explicitly-stated dependency is
findable by good keyword search, whereas an implicit one requires semantic reasoning.
Reporting them separately would show *where* semantic retrieval actually adds value.
**This is a proposed analytical split, not a committed analysis — flagged for approval.**

### 2.7 `documents` — the rendered artefacts

| Field | Notes |
|---|---|
| `document_id` | `DOC-0031` |
| `source_entity_type` / `source_entity_id` | what it was rendered from |
| `doc_type` | `prd` / `feature_spec` / `pbi` / `ticket` / `decision_log` / `meeting_notes` / `runbook` |
| `title` | |
| `body` | rendered text |
| `product_id` | |
| `created_date` | |
| `version` | |
| `ticket_ref` | where applicable |

`source_entity_id` is what makes ground truth derivable: given a query, we know which
documents *should* be relevant because we know which entity the query is about.

### 2.8 `conflicts`

| Field | Notes |
|---|---|
| `conflict_id` | `CONF-04` |
| `document_a` / `document_b` | the two documents in tension |
| `conflict_type` | e.g. incompatible scope, contradictory status, duplicated requirement |
| `resolution` | if resolved, and by which document |
| `is_resolved` | |

Conflict identification is a named objective in CA1. Conflicts must exist in the model
by construction, not be hoped for.

### 2.9 `query_set` and `ground_truth`

| Field | Notes |
|---|---|
| `query_id` | `Q-001` |
| `query` | natural-language phrasing |
| `query_type` | one of the categories in `PROJECT_SPECIFICATION.md` §7 |
| `relevant_document_ids` | **derived from the model** |
| `relevant_chunk_ids` | derived after chunking, by provenance — not by re-reading text |
| `expected_dependencies` | the `dependency_id`s a correct answer must surface |
| `expected_answer_elements` | discrete, checkable claims |
| `authored_via` | `template` or `human` — provenance of the query itself |
| `difficulty` | expected difficulty, used only for reporting, never for tuning |

Note on `relevant_chunk_ids`: because each chunk retains its `source_entity_id` and
`document_id` after chunking, ground truth at chunk level is obtained by **provenance
propagation**, not by semantic judgement. This is why the document-generation step must
emit chunk provenance rather than plain text.

---

## 3. Proposed documentation mix

CA2 §3.4 requires the corpus to deliberately span document structures, so that chunking
is evaluated across realistic variety rather than tuned to one artificially uniform
type. Proposed mix:

| Document type | Count | Character |
|---|---|---|
| PRD | 6–8 | Long, formal, multi-section, versioned |
| Feature spec | 8–12 | Medium, technical, structured |
| PBI | 40–60 | Short, informal, sometimes vague |
| Support ticket | 15–25 | Symptom-oriented, customer language |
| Decision log | 4–6 | Short, records a choice and its reason |
| Meeting notes | 5–8 | Fragmentary, unlabelled, informal |
| Runbook / tech doc | 4–6 | Technical, dense, unrelated to most queries |

*Exact counts depend on D6 (corpus scale) and require approval.*

Two structural asymmetries are deliberate and should be preserved:

- **Length spread.** PRDs run to several thousand words; meeting notes may be three
  lines. Real documentation looks like this, and a fixed chunk size behaves very
  differently across that range.
- **Authority spread.** Some documents are obsolete but still present in the
  repository. Retrieval systems that rank purely on similarity will surface stale
  documents; this is a realistic failure mode worth measuring.

---

## 4. Generation approach

Documents are **rendered deterministically from the model by template**, not
free-written by an LLM.

Why templates:

- Ground truth stays derivable and auditable.
- Provenance (`source_entity_id`) is guaranteed at generation time.
- Fully reproducible — same seed, same corpus, same chunk IDs.
- Cheap and fast to iterate.

Where natural variation is wanted, variation comes from **structured slots** — sentence
frames, section orderings, formality registers, document metadata — not from
free-form generation.

**Constraint:** an LLM must not be used to author corpus documents or to author
ground-truth labels. It may be used only as System B's generation component, which is
the thing under test.

**Open question for approval:** the alternative is LLM-assisted prose generation with a
deterministic structured model still governing the facts. This produces more realistic
prose and remains grounded, at higher cost and lower determinism. I recommend pure
templates for v1 and treating LLM-assisted rendering as a possible v2 corpus — but
this changes corpus character, so it needs your decision.

---

## 5. Randomness control

All randomness flows from a single recorded seed. The seed is part of the dataset
version, so a corpus is fully reproducible from `(seed, model version)`.

---

## 6. Lexical divergence — the validity-critical design element

This is the most important section in this document. Without it the experiment does not
test its own research question.

CA1 states the motivating failure directly: a query about *"onboarding delays"* will not
retrieve a document about *"new-user activation friction"*. If our synthetic documents
and our synthetic queries use the same words, BM25 will score well — and we will have
demonstrated only that BM25 works when lexical matching is easy. That is not the
research question.

### Proposed mechanism

Each feature and PBI carries a controlled vocabulary of three registers:

| Register | Example (same underlying concept) | Where it appears |
|---|---|---|
| `formal_term` | "Progressive Profiling" | PRD headings, spec titles, technical docs |
| `colloquial_terms` | "onboarding ramp", "new-user activation", "first-run setup" | meeting notes, tickets, some PBIs |
| query phrasing | "why do new signups struggle in their first session" | query set |

Documents mix registers according to `documentation_maturity` and `doc_type`:
formal-PRD-heavy repositories lean on `formal_term`; ticket and meeting-note
artefacts lean on `colloquial_terms`. Real repositories look exactly like this.

### The rule that protects validity

The divergence pattern is **fixed and recorded before any system is run**, and is
**never adjusted afterwards**. If it is tuned after seeing that BM25 underperforms, the
result is an artefact of the tuning and the experiment is void.

Concretely: the vocabulary mapping is part of the dataset version, committed before
the first evaluation run, and any later change is a new dataset version with a logged
rationale.

### Divergence should be graded, not binary

Real lexical mismatch varies. A corpus that is 100% paraphrase-only is as unrealistic
as one that is 100% verbatim. Proposed: queries distributed across **easy**
(terminology present in the document), **moderate** (synonym present), and **hard**
(only a general concept present, no shared terminology) — with the distribution
documented and fixed in advance, and reported as a stratified breakdown.

This stratification is also what would let us say something genuinely interesting:
*semantic retrieval helps most exactly where lexical overlap fails, and the size of that
band is the practically useful number.*

---

## 7. Formal / informal documentation contrast

CA2 §3 states the corpus should include both a more formally structured domain and a
smaller, less formally documented one, so findings can speak indicatively to whether
RAG's advantage depends on how well-structured the underlying documentation already is.

The `documentation_maturity` field on `products` operationalises this. Proposed
minimum: **two products** —

- **Product A** — B2B SaaS / workforce analytics. Formal: multi-section PRDs, versioned
  specs, compliance documentation, normative statements, long dependency sections.
- **Product B** — small consumer-facing team. Informal: short PBIs, chat-derived
  tickets, sparse meeting notes, undocumented decisions, heavy colloquial vocabulary.

This is **not** a cross-domain generalisability study, and will not be presented as one —
that would exceed a single Capstone semester, as CA2 acknowledges. It is a deliberate
design choice to avoid drawing a conclusion that holds only for one documentation
style.

*Number of products, and the specific domains, require approval (D6).*

---

## 8. Distractors

Without distractors, Precision@5 approaches 1.0 trivially and carries no information.

The model should deliberately generate topically adjacent but non-relevant documents:

- Same product, different feature
- Same concept, superseded document version
- Related component, different dependency relationship
- Similar customer complaint, different root cause

A useful target: roughly **one-third of topically-near documents should be true
distractors** for any given query. The exact ratio is a design parameter to be fixed
before the first run.

---

## 9. Versioning

| Artefact | Path | Versioning |
|---|---|---|
| Structured model | `data/synthetic/source_model/v{N}/` | immutable once used in a run |
| Rendered documents | `data/synthetic/documents/v{N}/` | immutable once used in a run |
| Query set | `data/queries/v{N}/` | immutable once used in a run |
| Ground truth | `data/ground_truth/v{N}/` | immutable once used in a run |

`data/versions/MANIFEST.json` records, for each version: version number, creation date,
seed, generator version, counts per entity type, and a content hash.

A run is only valid if it declares which version of each artefact it consumed.

---

## 10. Traceability of every label

The rule is that any ground-truth label can be traced to the model in one hop:

```
Q-014 expected_dependencies: [DEP-031, DEP-044]
        → DEP-031.from_id = PBI-A-014  → DOC-0044
        → DEP-044.to_id   = COMP-07    → DOC-0019
        → relevant_document_ids: [DOC-0044, DOC-0019, ...]
```

A label that cannot be produced this way is not a label; it is a guess. Any such label
must be rejected rather than kept.

---

## 11. Status of open questions

Ratified by the student on 2026-09-27, before any experiment was run. See
`DECISIONS.md` D-001.

| # | Question | Status |
|---|---|---|
| Q1 | Corpus scale | ⏸ **Open** — deferred until the source model exists. Proposal to follow. |
| Q2 | Query count and category distribution | ⏸ **Open** — deferred. Proposal to follow, then **approval required** before the query set is built. |
| Q3 | Two products (formal + informal), or one? | ⏸ **Open** — will be answered as part of the D6 corpus proposal, since the two are coupled. |
| Q4 | Template-only rendering, or LLM-assisted prose? | ✅ **Template-only, deterministic.** No LLM may invent documents or ground truth. |
| Q5 | Stratify results by explicit vs implicit dependencies? | ⏸ **Open** — recommendation is yes; awaiting confirmation. |
| Q6 | Distractor ratio target | ⏸ **Open** — ~1/3 topically-near documents. To be fixed with the D6 proposal. |
| Q7 | Include superseded/stale document versions? | ⏸ **Open** — recommendation is yes. |
| Q8 | Any anonymised real artefacts at all? | ✅ **No.** Fully synthetic (D9). Must be documented as a threat to external validity. |

---

## 12. Known limitations of this design, stated in advance

Recording these now, before results exist, so the write-up cannot be accused of
retrofitting limitations to an outcome.

1. **Synthetic corpus.** Ecological validity is limited. Real documentation is messier,
   more contradictory, and more politically loaded than anything we can template.
2. **Scale.** A corpus of this size is far smaller than an industrial repository, and
   retrieval difficulty scales with corpus size. Findings will likely *overstate*
   RAG's advantage on large corpora.
3. **Off-the-shelf embeddings.** Not tuned to product-management terminology. May
   underperform on domain vocabulary, which would bias *against* RAG. CA2 §2.2 treats
   this as an empirical question, not an assumption, in either direction.
4. **Keyword baseline is not industry search.** BM25 is a clean, reproducible baseline
   — not Elasticsearch, Solr, or a commercial product with semantic features. The
   comparison is against lexical retrieval, not against "what a company has today".
5. **Chunking.** One chunking configuration is not a property of RAG. Results are
   conditional on the chunking strategy chosen, and two strategies should be piloted
   rather than one assumed.
6. **Template prose.** Consistent register within a document type is less varied than
   real writing. Naturalness of phrasing is bounded by what templates can express.
7. **No temporal reasoning.** We model document versions but not the evolution of
   decisions over time in depth.
8. **No multi-user evaluation yet.** Human-in-the-loop measures are gated on ethics
   approval and are not part of the automated result.

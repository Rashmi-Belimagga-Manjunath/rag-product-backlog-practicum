# Query Benchmark Specification (32 slots)

> **Generated file.** Produced by `python3 -m src.benchmark.render_spec_doc`
> from `src/benchmark/query_spec.py`. Do not edit by hand; a test asserts this
> file matches the code.

The slot distribution is **APPROVED and FROZEN**. All 32 slots now carry
approved wording (see Exact approved wording). The three Q-SUP queries were fixed
before the corpus existed; the other 29 were authored against the frozen
272-document corpus, each derived from the corpus and the slot's own selector.
Difficulty is re-measured from the final wording before either system is
evaluated.

## Approved totals

| Property | Required |
|---|---|
| Total slots | 32 |
| Difficulty: easy | 11 |
| Difficulty: moderate | 11 |
| Difficulty: hard | 10 |
| Information retrieval | 6 |
| Feature context | 5 |
| Dependency identification | 8 |
| Cross-document reasoning | 5 |
| Conflict identification | 3 |
| Backlog analysis | 5 |
| Dependency-related total | 13 (6 explicit, 7 implicit) |

Dependency-related categories are `cross_document_reasoning` and `dependency_identification`.

## Slot register

Slots are **selectors over the structured model**, not hard-coded document IDs.
The final 272-document corpus has different IDs from the mechanism sample, so a
selector that resolves against the sample must also resolve against the final
corpus. An unresolved slot is a hard STOP at freeze, never a warning.

| Slot | ID | Category | Difficulty | Selector | Dep. | Version | Purpose |
|---:|---|---|---|---|---|---|---|
| 1 | `Q-01` | Information retrieval | easy | `current_prd` | - | - | Locate the PRD that governs the primary flow. |
| 2 | `Q-02` | Information retrieval | easy | `runbook` | - | - | Locate the operational runbook for a core component. |
| 3 | `Q-03` | Information retrieval | easy | `current_feature_spec` | - | - | Locate a single current feature specification. |
| 4 | `Q-04` | Information retrieval | moderate | `decision_record` | - | - | Locate a decision record and the choice it records. |
| 5 | `Q-SUP-1` | Information retrieval | moderate | `current_prd_with_superseded_sibling` | - | recency | Q-SUP-1. A superseded PRD is the D5 distractor; the answer is the current one. |
| 6 | `Q-05` | Information retrieval | hard | `informal_ticket` | - | - | Colloquial ticket text with low lexical overlap against its target. |
| 7 | `Q-06` | Feature context | easy | `feature_summary` | - | - | Summarise a feature from its own specification. |
| 8 | `Q-SUP-3` | Feature context | easy | `current_spec_with_approval_limit` | - | current_value | Q-SUP-3. The superseded version holds a different historical value. |
| 9 | `Q-07` | Feature context | moderate | `requirement_statement` | - | - | State a normative requirement and its owning document. |
| 10 | `Q-08` | Feature context | moderate | `ruled_out_option` | - | - | Identify an option the documentation explicitly rules out. |
| 11 | `Q-SUP-2` | Feature context | hard | `superseded_spec_with_current_successor` | - | provenance | Q-SUP-2. The claim exists in a superseded spec; ground truth must name the authoritative current document. relevance_basis = both. |
| 12 | `Q-09` | Dependency identification | easy | `explicit_dep_feature_to_component` | explicit | - | A stated feature->component dependency. |
| 13 | `Q-10` | Dependency identification | easy | `explicit_dep_component_to_component` | explicit | - | A stated component-to-component dependency. |
| 14 | `Q-11` | Dependency identification | moderate | `explicit_dep_ordering` | explicit | - | A stated ordering constraint between two stages. |
| 15 | `Q-12` | Dependency identification | moderate | `explicit_dep_third_party` | explicit | - | A stated dependency on an external party. |
| 16 | `Q-13` | Dependency identification | moderate | `implicit_dep_component` | implicit | - | An unstated component dependency, encoded in the model and inferable only from context. |
| 17 | `Q-14` | Dependency identification | hard | `implicit_dep_ordering` | implicit | - | An unstated ordering constraint. |
| 18 | `Q-15` | Dependency identification | hard | `implicit_dep_cross_feature` | implicit | - | An unstated dependency spanning two features. |
| 19 | `Q-16` | Dependency identification | hard | `implicit_dep_via_runbook` | implicit | - | A dependency implied by a runbook rather than stated in prose. |
| 20 | `Q-17` | Cross-document reasoning | easy | `cdr_single_document` | explicit | - | A dependency visible within one document. |
| 21 | `Q-18` | Cross-document reasoning | moderate | `cdr_two_documents` | explicit | - | A dependency that must be assembled from two documents. |
| 22 | `Q-19` | Cross-document reasoning | hard | `cdr_meeting_notes` | implicit | - | A relationship recoverable from meeting notes, stated as a stand-in rather than asserted. |
| 23 | `Q-20` | Cross-document reasoning | hard | `cdr_prd_sequence` | implicit | - | An ordering inferred from the sequence of a PRD's requirements. |
| 24 | `Q-21` | Cross-document reasoning | hard | `cdr_via_superseded_document` | implicit | - | A dependency whose only textual evidence sits in a superseded document. |
| 25 | `Q-22` | Conflict identification | easy | `conflict_resolved` | - | - | A conflict that the documentation resolves. |
| 26 | `Q-23` | Conflict identification | moderate | `conflict_unresolved` | - | - | A conflict the documentation leaves open. |
| 27 | `Q-24` | Conflict identification | hard | `conflict_resolved_in_later_version` | - | - | A conflict resolved only in a later document version. |
| 28 | `Q-25` | Backlog analysis | easy | `backlog_prioritisation_decision` | - | - | A documented prioritisation decision. |
| 29 | `Q-26` | Backlog analysis | easy | `backlog_non_goal` | - | - | A stated non-goal and why it was excluded. |
| 30 | `Q-27` | Backlog analysis | moderate | `backlog_changed_decision_rationale` | - | - | The rationale behind a decision that changed. |
| 31 | `Q-28` | Backlog analysis | moderate | `backlog_deprioritised_rationale` | - | - | The documented reason an item was deprioritised. |
| 32 | `Q-29` | Backlog analysis | hard | `backlog_synthesis` | - | - | A synthesis across a feature and its decision record. |

## Exact approved wording

All 32 slots are worded. These are fixed by the specification and are **not**
placeholders.

- `Q-01`: "Which Meridian PRD defines employee onboarding and payroll readiness?"
- `Q-02`: "Where is the runbook for recovering a delayed event on the domain event bus?"
- `Q-03`: "Which document is the current feature specification for Progressive Profiling?"
- `Q-04`: "Which decision record explains why tax paperwork is no longer part of initial registration?"
- `Q-SUP-1`: "Which PRD is in production?"
- `Q-05`: "When I logged in this morning the whole thing just sat there frozen for ages, so I had to give up on it."
- `Q-06`: "Can you summarise what the Progressive Profiling feature does?"
- `Q-SUP-3`: "What is the current approval limit?"
- `Q-07`: "Which document would an internal audit point to as the place where tax paperwork is requested only after a person has signed in for the very first time?"
- `Q-08`: "What does the onboarding PRD explicitly leave out of its remit?"
- `Q-SUP-2`: "A spec says tax at first login — which doc, still current?"
- `Q-09`: "Which component does Progressive Profiling depend on, per the feature specification?"
- `Q-10`: "Which component document says the Timesheet Approval Engine depends on the payroll ledger database?"
- `Q-11`: "Is there a stated order so identity verification finishes before progressive profiling in the product sequence?"
- `Q-12`: "According to the specification, which external third-party service does Progressive Profiling rely on?"
- `Q-13`: "Which component is needed to support Bulk Timesheet Approval even though no specification states it directly?"
- `Q-14`: "Which part of the product must be available before streak saver can work even though no document states that plainly?"
- `Q-15`: "Which feature's work has to wait on another feature's delivery before its own items can proceed?"
- `Q-16`: "Which operating guide reveals the hidden dependency that Bulk Timesheet Approval has on another component?"
- `Q-17`: "Which document mentions that Progressive Profiling depends on the taxband rate service?"
- `Q-18`: "Which two places in the documentation must a reader consult together to spot where Progressive Profiling leans on the taxband rate service?"
- `Q-19`: "Which set of meeting minutes alludes to a connection between two backend services without ever asserting it outright?"
- `Q-20`: "From the sequence in which the product's requirements are listed, which stage must complete before streak saver can act?"
- `Q-21`: "Which older document still holds the only written trace of the dependency between requirement REQ-M-03 and the timesheet engine?"
- `Q-22`: "Which documents settle the dispute between the onboarding PRD and the Progressive Profiling specification?"
- `Q-23`: "Which documents disagree about how long generated payslips stay available for download?"
- `Q-24`: "Which two documents were originally at odds until a later PRD revision quietly resolved the discrepancy?"
- `Q-25`: "Which decision record prioritised releasing bulk approval for whole batches only?"
- `Q-26`: "What does the onboarding PRD state as a non-goal and why was it excluded?"
- `Q-27`: "What exactly is different in the second release of the onboarding PRD, and which documented decision explains that difference?"
- `Q-28`: "Why did the team deprioritise partial-batch approval according to the decision record?"
- `Q-29`: "Putting the Progressive Profiling specification next to the tax-collection decision record, what do these two documents together tell a stakeholder?"

## Corpus requirements attached to slots

Some slots cannot resolve against the 34-document mechanism sample because the
sample deliberately does not contain the phenomenon. These are **corpus
requirements, not defects**; `validate_ground_truth --against-final` makes them
hard stops.

- `Q-SUP-3`:
  - A feature specification whose approval limit CHANGED between v1 and v2, so the superseded value differs from the current one. Not present in the mechanism sample.

## Difficulty definition

Easy `>=40%` lexical overlap, moderate `20-39%`, hard `<20%`, computed with the
frozen stopword set over query text versus the target documents. This is a
property of the benchmark, not a psychological claim about difficulty.

## Difficulty labels vs lexical overlap

Evidence terminology: `difficulty_label` is the frozen benchmark difficulty
designation; `lexical_overlap` is the measured lexical-overlap percentage;
`lexical_overlap_band` is the band produced by the frozen overlap thresholds;
`difficulty_status` is MATCH / MISMATCH between the frozen label and the band.
The QUERIES sheet of the evidence workbook reports one row per slot with all
four fields.

Difficulty labels were assigned during benchmark construction based on the intended reasoning complexity of each task. Lexical overlap was subsequently measured as a corpus-dependent diagnostic. Because product-management queries may necessarily contain domain-specific terminology, feature names, component names, and requirement identifiers, lexical-overlap bands do not always correspond to the intended difficulty labels. The original difficulty labels were retained rather than altered post hoc to force agreement with the lexical measure.

The slots whose lexical-overlap band differs from their frozen difficulty label are documented and kept visible rather than hidden. A band mismatch is not treated as evidence that the benchmark difficulty labels are automatically wrong: the labels encode intended task/reasoning complexity, whereas lexical overlap is a corpus-dependent diagnostic.

## Chunking limitation

The frozen 1000/200 chunking configuration does not produce multi-chunk documents in the final synthetic corpus. Consequently, the experiment evaluates retrieval over document-sized chunks and does not test cross-chunk retrieval behaviour.

## Validation

`python3 -m src.benchmark.query_spec` prints the table and exits non-zero on any
distribution violation. `python3 -m src.benchmark.validate_ground_truth`
resolves every selector against the structured model.

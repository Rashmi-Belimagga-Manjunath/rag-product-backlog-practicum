"""
The 32-slot query benchmark specification.

The distribution is APPROVED and FROZEN. Query WORDING is now authored for all 32 slots
and frozen alongside the query set; difficulty is re-measured from the final wording
before either system is evaluated.

Slots are expressed as SELECTORS over the structured model rather than as hard-coded
document IDs. That is deliberate: the final 272-document corpus has different IDs from the
mechanism sample, so a selector resolved against the sample must resolve against the final
corpus too. Resolution is re-run at freeze time and a slot that resolves to nothing is a
hard STOP, not a warning.

All 32 slots carry approved wording (QUERY_WORDING). The three Q-SUP queries were approved
before the corpus existed; the other 29 were authored against the frozen 272-document
corpus, each derived from the corpus and the slot's own selector.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace as dataclasses_replace
from typing import Literal, Optional

Category = Literal[
    "information_retrieval", "feature_context", "dependency_identification",
    "cross_document_reasoning", "conflict_identification", "backlog_analysis",
]
Difficulty = Literal["easy", "moderate", "hard"]

APPROVED_CATEGORY_COUNTS = {
    "information_retrieval": 6,
    "feature_context": 5,
    "dependency_identification": 8,
    "cross_document_reasoning": 5,
    "conflict_identification": 3,
    "backlog_analysis": 5,
}
APPROVED_DIFFICULTY_COUNTS = {"easy": 11, "moderate": 11, "hard": 10}
DEPENDENCY_CATEGORIES = {"dependency_identification", "cross_document_reasoning"}
APPROVED_DEPENDENCY_TOTAL = 13
APPROVED_EXPLICIT = 6
APPROVED_IMPLICIT = 7

# Approved Q-SUP wording. Fixed by the specification; these three are not placeholders.
Q_SUP_1 = "Which PRD is in production?"
Q_SUP_2 = "A spec says tax at first login \u2014 which doc, still current?"
Q_SUP_3 = "What is the current approval limit?"

# Frozen methodological statements. Single source of truth for the query-specification
# document and the evidence workbook; they must not drift between artefacts.
DIFFICULTY_METHOD_NOTE = (
    "Difficulty labels were assigned during benchmark construction based on the "
    "intended reasoning complexity of each task. Lexical overlap was subsequently "
    "measured as a corpus-dependent diagnostic. Because product-management queries may "
    "necessarily contain domain-specific terminology, feature names, component names, "
    "and requirement identifiers, lexical-overlap bands do not always correspond to the "
    "intended difficulty labels. The original difficulty labels were retained rather "
    "than altered post hoc to force agreement with the lexical measure."
)
DIFFICULTY_MISMATCH_NOTE = (
    "The slots whose lexical-overlap band differs from their frozen difficulty label are "
    "documented and kept visible rather than hidden. A band mismatch is not treated as "
    "evidence that the benchmark difficulty labels are automatically wrong: the labels "
    "encode intended task/reasoning complexity, whereas lexical overlap is a "
    "corpus-dependent diagnostic."
)
CHUNKING_LIMITATION_NOTE = (
    "The frozen 1000/200 chunking configuration does not produce multi-chunk documents "
    "in the final synthetic corpus. Consequently, the experiment evaluates retrieval "
    "over document-sized chunks and does not test cross-chunk retrieval behaviour."
)
Q05_INTENT_NOTE = (
    "Q-05 is deliberately authored as a natural-language problem/symptom statement "
    "rather than an interrogative question. Its intended information-retrieval task is "
    "to match an informal problem description to the support tickets that report the "
    "same symptoms; the ground-truth target is the 20 Tally support tickets "
    "(TKT-T-001 to TKT-T-020). The wording deliberately avoids technical keywords so "
    "that lexical overlap stays the lowest in the benchmark (12.5%, hard). Technical "
    "keywords must not be added merely to raise the measured overlap."
)

# Wording for the remaining 29 slots, authored against the frozen 272-document corpus and
# each slot's approved selector. Frozen here alongside the slot distribution.
QUERY_WORDING: dict = {
    "Q-01": "Which Meridian PRD defines employee onboarding and payroll readiness?",
    "Q-02": "Where is the runbook for recovering a delayed event on the domain event bus?",
    "Q-03": "Which document is the current feature specification for Progressive Profiling?",
    "Q-04": "Which decision record explains why tax paperwork is no longer part of initial "
            "registration?",
    "Q-05": "When I logged in this morning the whole thing just sat there frozen for ages, "
            "so I had to give up on it.",
    "Q-06": "Can you summarise what the Progressive Profiling feature does?",
    "Q-07": "Which document would an internal audit point to as the place where tax "
            "paperwork is requested only after a person has signed in for the very first "
            "time?",
    "Q-08": "What does the onboarding PRD explicitly leave out of its remit?",
    "Q-09": "Which component does Progressive Profiling depend on, per the feature "
            "specification?",
    "Q-10": "Which component document says the Timesheet Approval Engine depends on the "
            "payroll ledger database?",
    "Q-11": "Is there a stated order so identity verification finishes before progressive "
            "profiling in the product sequence?",
    "Q-12": "According to the specification, which external third-party service does "
            "Progressive Profiling rely on?",
    "Q-13": "Which component is needed to support Bulk Timesheet Approval even though no "
            "specification states it directly?",
    "Q-14": "Which part of the product must be available before streak saver can work even "
            "though no document states that plainly?",
    "Q-15": "Which feature's work has to wait on another feature's delivery before its own "
            "items can proceed?",
    "Q-16": "Which operating guide reveals the hidden dependency that Bulk Timesheet "
            "Approval has on another component?",
    "Q-17": "Which document mentions that Progressive Profiling depends on the taxband "
            "rate service?",
    "Q-18": "Which two places in the documentation must a reader consult together to spot "
            "where Progressive Profiling leans on the taxband rate service?",
    "Q-19": "Which set of meeting minutes alludes to a connection between two backend "
            "services without ever asserting it outright?",
    "Q-20": "From the sequence in which the product's requirements are listed, which stage "
            "must complete before streak saver can act?",
    "Q-21": "Which older document still holds the only written trace of the dependency "
            "between requirement REQ-M-03 and the timesheet engine?",
    "Q-22": "Which documents settle the dispute between the onboarding PRD and the "
            "Progressive Profiling specification?",
    "Q-23": "Which documents disagree about how long generated payslips stay available "
            "for download?",
    "Q-24": "Which two documents were originally at odds until a later PRD revision "
            "quietly resolved the discrepancy?",
    "Q-25": "Which decision record prioritised releasing bulk approval for whole batches "
            "only?",
    "Q-26": "What does the onboarding PRD state as a non-goal and why was it excluded?",
    "Q-27": "What exactly is different in the second release of the onboarding PRD, and "
            "which documented decision explains that difference?",
    "Q-28": "Why did the team deprioritise partial-batch approval according to the "
            "decision record?",
    "Q-29": "Putting the Progressive Profiling specification next to the tax-collection "
            "decision record, what do these two documents together tell a stakeholder?",
}


@dataclass(frozen=True)
class Slot:
    query_id: str
    slot: int
    category: Category
    difficulty: Difficulty
    selector: str
    purpose: str
    dependency_explicitness: Optional[str] = None
    version_kind: Optional[str] = None
    query_text: Optional[str] = None
    required_corpus_facts: tuple = ()


SLOTS: tuple = (
    # --- information retrieval: 6 (3 easy, 2 moderate, 1 hard) -----------------
    Slot("Q-01", 1, "information_retrieval", "easy", "current_prd",
         "Locate the PRD that governs the primary flow."),
    Slot("Q-02", 2, "information_retrieval", "easy", "runbook",
         "Locate the operational runbook for a core component."),
    Slot("Q-03", 3, "information_retrieval", "easy", "current_feature_spec",
         "Locate a single current feature specification."),
    Slot("Q-04", 4, "information_retrieval", "moderate", "decision_record",
         "Locate a decision record and the choice it records."),
    Slot("Q-SUP-1", 5, "information_retrieval", "moderate",
         "current_prd_with_superseded_sibling",
         "Q-SUP-1. A superseded PRD is the D5 distractor; the answer is the current one.",
         version_kind="recency", query_text=Q_SUP_1),
    Slot("Q-05", 6, "information_retrieval", "hard", "informal_ticket",
         "Deliberately non-interrogative symptom statement (see Q05_INTENT_NOTE); "
         "lowest lexical overlap in the benchmark.",
         required_corpus_facts=(
             "Requires the 20 Tally support tickets (TKT-T-001 to TKT-T-020) describing "
             "the unresponsive/frozen-product symptom so the informal statement resolves "
             "to them. Q-05 is intentionally a problem/symptom statement, not an "
             "interrogative question (see Q05_INTENT_NOTE).",
         ),),

    # --- feature context: 5 (2 easy, 2 moderate, 1 hard) -----------------------
    Slot("Q-06", 7, "feature_context", "easy", "feature_summary",
         "Summarise a feature from its own specification."),
    Slot("Q-SUP-3", 8, "feature_context", "easy", "current_spec_with_approval_limit",
         "Q-SUP-3. The superseded version holds a different historical value.",
         version_kind="current_value", query_text=Q_SUP_3,
         required_corpus_facts=(
             "A feature specification whose approval limit CHANGED between v1 and v2, so "
             "the superseded value differs from the current one. Not present in the "
             "mechanism sample.",
         ),),
    Slot("Q-07", 9, "feature_context", "moderate", "requirement_statement",
         "State a normative requirement and its owning document."),
    Slot("Q-08", 10, "feature_context", "moderate", "ruled_out_option",
         "Identify an option the documentation explicitly rules out."),
    Slot("Q-SUP-2", 11, "feature_context", "hard",
         "superseded_spec_with_current_successor",
         "Q-SUP-2. The claim exists in a superseded spec; ground truth must name the "
         "authoritative current document. relevance_basis = both.",
         version_kind="provenance", query_text=Q_SUP_2),

    # --- dependency identification: 8 (2 easy, 3 moderate, 3 hard) -------------
    # 4 explicit
    Slot("Q-09", 12, "dependency_identification", "easy",
         "explicit_dep_feature_to_component", "A stated feature->component dependency.",
         dependency_explicitness="explicit"),
    Slot("Q-10", 13, "dependency_identification", "easy",
         "explicit_dep_component_to_component",
         "A stated component-to-component dependency.", dependency_explicitness="explicit"),
    Slot("Q-11", 14, "dependency_identification", "moderate",
         "explicit_dep_ordering", "A stated ordering constraint between two stages.",
         dependency_explicitness="explicit"),
    Slot("Q-12", 15, "dependency_identification", "moderate",
         "explicit_dep_third_party", "A stated dependency on an external party.",
         dependency_explicitness="explicit"),
    # 4 implicit
    Slot("Q-13", 16, "dependency_identification", "moderate",
         "implicit_dep_component", "An unstated component dependency, encoded in the "
         "model and inferable only from context.", dependency_explicitness="implicit"),
    Slot("Q-14", 17, "dependency_identification", "hard", "implicit_dep_ordering",
         "An unstated ordering constraint.", dependency_explicitness="implicit"),
    Slot("Q-15", 18, "dependency_identification", "hard", "implicit_dep_cross_feature",
         "An unstated dependency spanning two features.",
         dependency_explicitness="implicit"),
    Slot("Q-16", 19, "dependency_identification", "hard", "implicit_dep_via_runbook",
         "A dependency implied by a runbook rather than stated in prose.",
         dependency_explicitness="implicit"),

    # --- cross-document reasoning: 5 (1 easy, 1 moderate, 3 hard) --------------
    # 2 explicit, 3 implicit
    Slot("Q-17", 20, "cross_document_reasoning", "easy", "cdr_single_document",
         "A dependency visible within one document.", dependency_explicitness="explicit"),
    Slot("Q-18", 21, "cross_document_reasoning", "moderate", "cdr_two_documents",
         "A dependency that must be assembled from two documents.",
         dependency_explicitness="explicit"),
    Slot("Q-19", 22, "cross_document_reasoning", "hard", "cdr_meeting_notes",
         "A relationship recoverable from meeting notes, stated as a stand-in rather "
         "than asserted.",
         dependency_explicitness="implicit"),
    Slot("Q-20", 23, "cross_document_reasoning", "hard", "cdr_prd_sequence",
         "An ordering inferred from the sequence of a PRD's requirements.",
         dependency_explicitness="implicit"),
    Slot("Q-21", 24, "cross_document_reasoning", "hard", "cdr_via_superseded_document",
         "A dependency whose only textual evidence sits in a superseded document.",
         dependency_explicitness="implicit"),

    # --- conflict identification: 3 (1 easy, 1 moderate, 1 hard) --------------
    Slot("Q-22", 25, "conflict_identification", "easy", "conflict_resolved",
         "A conflict that the documentation resolves."),
    Slot("Q-23", 26, "conflict_identification", "moderate", "conflict_unresolved",
         "A conflict the documentation leaves open."),
    Slot("Q-24", 27, "conflict_identification", "hard", "conflict_resolved_in_later_version",
         "A conflict resolved only in a later document version."),

    # --- backlog analysis: 5 (2 easy, 2 moderate, 1 hard) ---------------------
    # Documented rationale, requirements, and priority/context. Deliberately NOT
    # dependency questions: a slot that turns out to require dependency reasoning is
    # reclassified before the experiment and recorded in DECISIONS.md.
    Slot("Q-25", 28, "backlog_analysis", "easy", "backlog_prioritisation_decision",
         "A documented prioritisation decision."),
    Slot("Q-26", 29, "backlog_analysis", "easy", "backlog_non_goal",
         "A stated non-goal and why it was excluded."),
    Slot("Q-27", 30, "backlog_analysis", "moderate", "backlog_changed_decision_rationale",
         "The rationale behind a decision that changed."),
    Slot("Q-28", 31, "backlog_analysis", "moderate", "backlog_deprioritised_rationale",
         "The documented reason an item was deprioritised."),
    Slot("Q-29", 32, "backlog_analysis", "hard", "backlog_synthesis",
         "A synthesis across a feature and its decision record."),
)

SLOTS = tuple(
    dataclasses_replace(slot, query_text=QUERY_WORDING[slot.query_id])
    if slot.query_id in QUERY_WORDING else slot
    for slot in SLOTS
)


def validate_spec() -> list:
    """Assert the specification satisfies every approved constraint. Empty list = valid."""
    problems: list = []

    if len(SLOTS) != 32:
        problems.append(f"expected 32 slots, found {len(SLOTS)}")

    slots = sorted(SLOTS, key=lambda s: s.slot)
    if [s.slot for s in slots] != list(range(1, 33)):
        problems.append("slot numbers are not exactly 1..32")

    by_category: dict = {}
    by_difficulty: dict = {}
    for s in SLOTS:
        by_category.setdefault(s.category, []).append(s)
        by_difficulty.setdefault(s.difficulty, []).append(s)

    for category, expected in APPROVED_CATEGORY_COUNTS.items():
        actual = len(by_category.get(category, []))
        if actual != expected:
            problems.append(
                f"category '{category}': expected {expected}, found {actual}")

    for difficulty, expected in APPROVED_DIFFICULTY_COUNTS.items():
        actual = len(by_difficulty.get(difficulty, []))
        if actual != expected:
            problems.append(
                f"difficulty '{difficulty}': expected {expected}, found {actual}")

    dependency_slots = [s for s in SLOTS if s.category in DEPENDENCY_CATEGORIES]
    if len(dependency_slots) != APPROVED_DEPENDENCY_TOTAL:
        problems.append(
            f"dependency-related slots: expected {APPROVED_DEPENDENCY_TOTAL}, "
            f"found {len(dependency_slots)}")

    explicit = [s for s in dependency_slots if s.dependency_explicitness == "explicit"]
    implicit = [s for s in dependency_slots if s.dependency_explicitness == "implicit"]
    if len(explicit) != APPROVED_EXPLICIT:
        problems.append(f"explicit dependency slots: expected {APPROVED_EXPLICIT}, "
                        f"found {len(explicit)}")
    if len(implicit) != APPROVED_IMPLICIT:
        problems.append(f"implicit dependency slots: expected {APPROVED_IMPLICIT}, "
                        f"found {len(implicit)}")

    for s in dependency_slots:
        if not s.dependency_explicitness:
            problems.append(f"{s.query_id}: dependency slot has no explicitness label")
    for s in SLOTS:
        if s.category not in DEPENDENCY_CATEGORIES and s.dependency_explicitness:
            problems.append(
                f"{s.query_id}: non-dependency category carries an explicitness label")

    # The three version queries, exactly.
    version_slots = [s for s in SLOTS if s.version_kind]
    if len(version_slots) != 3:
        problems.append(f"version queries: expected 3, found {len(version_slots)}")
    expected_version = {
        "Q-SUP-1": ("information_retrieval", "moderate", "recency", Q_SUP_1),
        "Q-SUP-2": ("feature_context", "hard", "provenance", Q_SUP_2),
        "Q-SUP-3": ("feature_context", "easy", "current_value", Q_SUP_3),
    }
    for query_id, (category, difficulty, kind, text) in expected_version.items():
        match = next((s for s in SLOTS if s.query_id == query_id), None)
        if match is None:
            problems.append(f"{query_id} is missing")
            continue
        if match.category != category:
            problems.append(f"{query_id}: category {match.category} != {category}")
        if match.difficulty != difficulty:
            problems.append(f"{query_id}: difficulty {match.difficulty} != {difficulty}")
        if match.version_kind != kind:
            problems.append(f"{query_id}: version_kind {match.version_kind} != {kind}")
        if match.query_text != text:
            problems.append(f"{query_id}: wording does not match the approved text")

    for s in SLOTS:
        if s.query_text is None or not s.query_text.strip():
            problems.append(f"{s.query_id}: missing query wording")

    if len({s.query_text for s in SLOTS}) != len(SLOTS):
        problems.append("duplicate query wording across slots")

    if len({s.query_id for s in SLOTS}) != 32:
        problems.append("duplicate query_id present")
    return problems

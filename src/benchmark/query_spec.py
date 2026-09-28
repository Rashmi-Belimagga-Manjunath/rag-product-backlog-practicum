"""
The 32-slot query benchmark specification.

The distribution is APPROVED and FROZEN. Query WORDING is authored later, at generation
time, and then difficulty is measured before either system is evaluated.

Slots are expressed as SELECTORS over the structured model rather than as hard-coded
document IDs. That is deliberate: the final 272-document corpus has different IDs from the
mechanism sample, so a selector resolved against the sample must resolve against the final
corpus too. Resolution is re-run at freeze time and a slot that resolves to nothing is a
hard STOP, not a warning.

Only the three Q-SUP queries have approved wording. Every other slot has query_text=None
because no wording may be authored before the corpus exists - wording written against a
sample would encode sample-specific vocabulary into the benchmark.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
         "Colloquial ticket text with low lexical overlap against its target."),

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
        if s.query_id not in expected_version and s.query_text is not None:
            problems.append(
                f"{s.query_id}: wording authored before the corpus exists. Only the three "
                f"Q-SUP queries have approved wording.")

    if len({s.query_id for s in SLOTS}) != 32:
        problems.append("duplicate query_id present")
    return problems

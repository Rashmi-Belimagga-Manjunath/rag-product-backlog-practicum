"""
Tests for the 32-slot query specification and the model-derived selector framework.

These guard the frozen distribution, the exact Q-SUP wording, the generated-document
agreement with the code, and the failure modes that would silently corrupt ground truth.
"""

from __future__ import annotations

import pytest

from src.benchmark import selectors
from src.benchmark.query_spec import (
    APPROVED_CATEGORY_COUNTS, APPROVED_DEPENDENCY_TOTAL, APPROVED_DIFFICULTY_COUNTS,
    APPROVED_EXPLICIT, APPROVED_IMPLICIT, Q_SUP_1, Q_SUP_2, Q_SUP_3, SLOTS,
    validate_spec,
)
from src.benchmark.render_spec_doc import DOC, render
from src.benchmark.selectors import SELECTORS, resolve_slot
from src.benchmark.validate_ground_truth import validate_ground_truth
from src.data_generation.render_v1 import render_corpus
from src.data_generation.v1_sample import build_mechanism_sample


# --------------------------------------------------------------------------- spec

def test_spec_satisfies_every_approved_distribution():
    assert validate_spec() == []


def test_thirty_two_unique_slots():
    assert len(SLOTS) == 32
    assert len({s.query_id for s in SLOTS}) == 32
    assert sorted(s.slot for s in SLOTS) == list(range(1, 33))


def test_difficulty_totals():
    counts = {d: sum(1 for s in SLOTS if s.difficulty == d)
              for d in APPROVED_DIFFICULTY_COUNTS}
    assert counts == APPROVED_DIFFICULTY_COUNTS


def test_category_totals():
    counts = {c: sum(1 for s in SLOTS if s.category == c)
              for c in APPROVED_CATEGORY_COUNTS}
    assert counts == APPROVED_CATEGORY_COUNTS


def test_dependency_explicitness_totals():
    dep = [s for s in SLOTS if s.dependency_explicitness]
    assert len(dep) == APPROVED_DEPENDENCY_TOTAL
    assert sum(1 for s in dep if s.dependency_explicitness == "explicit") == APPROVED_EXPLICIT
    assert sum(1 for s in dep if s.dependency_explicitness == "implicit") == APPROVED_IMPLICIT


def test_only_q_sup_queries_have_approved_wording():
    with_text = {s.query_id for s in SLOTS if s.query_text is not None}
    assert with_text == {"Q-SUP-1", "Q-SUP-2", "Q-SUP-3"}


def test_q_sup_wording_is_exact_including_em_dash():
    # The em dash in Q-SUP-2 is part of the approved wording. A plain hyphen is a
    # different string and must fail here rather than ship silently.
    by_id = {s.query_id: s for s in SLOTS}
    assert by_id["Q-SUP-1"].query_text == Q_SUP_1 == "Which PRD is in production?"
    assert by_id["Q-SUP-2"].query_text == Q_SUP_2
    assert "\u2014" in Q_SUP_2, "Q-SUP-2 must use an em dash"
    assert " - " not in Q_SUP_2, "Q-SUP-2 must not use a hyphen"
    assert by_id["Q-SUP-3"].query_text == Q_SUP_3 == "What is the current approval limit?"


def test_required_corpus_facts_is_a_tuple_of_strings():
    # Guards against a missing trailing comma silently making this one long string,
    # which then gets iterated character by character when reported.
    for s in SLOTS:
        assert isinstance(s.required_corpus_facts, tuple)
        for fact in s.required_corpus_facts:
            assert isinstance(fact, str)
            assert len(fact) > 20


def test_committed_query_specification_matches_the_code():
    # The document is generated; drift between it and the code must fail CI.
    assert DOC.read_text() == render()


# ----------------------------------------------------------------------- selectors

def test_every_referenced_selector_is_implemented():
    for s in SLOTS:
        assert hasattr(selectors, s.selector), f"missing selector {s.selector}"


def test_conflict_ids_use_a_separate_id_space():
    # A conflict_id placed in entity_ids would resolve against no entity and look like a
    # valid empty resolution instead of an error, so the ID spaces must stay separate.
    model = build_mechanism_sample()
    documents = render_corpus(model)
    r = selectors.SELECTORS["conflict_resolved"](model, documents)
    assert r.conflict_ids, "the mechanism sample has a resolved conflict"
    assert not r.entity_ids, "a conflict ID must not be reported as an entity ID"
    assert all(c in {c.conflict_id for c in model.conflicts} for c in r.conflict_ids)


def test_resolution_reports_a_problem_when_nothing_resolves():
    r = selectors.Resolution("test_selector", [], entity_ids=[], relevance_basis="current")
    problems = r.problems("Q-TEST")
    assert any("resolved to no document" in p for p in problems)
    assert any("neither an entity nor a conflict" in p for p in problems)


def test_no_selector_satisfies_a_slot_with_a_fallback():
    """
    A slot that cannot be resolved must be reported as unmet.

    A selector that substitutes some other document to look successful hides a corpus
    requirement and makes the freeze gate lie. This test fails if any selector ever
    reintroduces a fallback.
    """
    model = build_mechanism_sample()
    documents = render_corpus(model)
    offenders = []
    for slot in SLOTS:
        r = resolve_slot(slot, model, documents)
        if not r.document_ids:
            continue
        for note in r.notes:
            if "fallback" in note.lower():
                offenders.append(f"{slot.query_id} ({slot.selector}): {note}")
    assert not offenders, "selectors must not resolve a slot via a fallback:\n" + "\n".join(offenders)


def test_unresolved_selector_returns_no_documents():
    model = build_mechanism_sample()
    documents = render_corpus(model)
    r = selectors.SELECTORS["cdr_prd_sequence"](model, documents)
    if not r.document_ids:
        assert r.problems("Q-20")
        assert all("fallback" not in n.lower() for n in r.notes)


# ---------------------------------------------------------------------- validation

def test_sample_validation_reports_unmet_slots_without_a_broken_reference():
    report = validate_ground_truth(build_mechanism_sample())
    assert report.id_problems == []
    assert report.spec_problems == []
    # 25 of 32 resolve on the mechanism sample; the rest are corpus requirements.
    assert len(report.unmet) == 7
    assert {u["query_id"] for u in report.unmet} == {
        "Q-05", "Q-SUP-3", "Q-10", "Q-11", "Q-14", "Q-20", "Q-21"}


def test_final_mode_treats_any_unmet_slot_as_a_hard_stop():
    report = validate_ground_truth(build_mechanism_sample(), against_final=True)
    assert not report.freezable


def test_sample_mode_is_not_freezable_either():
    report = validate_ground_truth(build_mechanism_sample())
    assert not report.freezable


def test_q_sup_3_does_not_match_a_bare_number():
    """
    Version numbers and dates are numbers.

    Matching on a bare number would make this selector resolve to the WRONG document,
    which is worse than not resolving: a false positive silently corrupts ground truth
    instead of surfacing a corpus requirement.
    """
    model = build_mechanism_sample()
    documents = render_corpus(model)
    r = selectors.SELECTORS["current_spec_with_approval_limit"](model, documents)
    if r.document_ids:
        assert r.entity_ids, "a resolved approval-limit spec must name its feature"
    else:
        assert r.problems("Q-SUP-3")


# ------------------------------------------------------------------- C6 measure

def test_revised_c6_catches_genuine_verbatim_duplication():
    """
    Positive control for the revised C6.

    A measure that only ever returns zero would pass the corpus just as easily as a clean
    chunker, so it must be shown to fail on real duplication.
    """
    from src.chunking.splitter import (C6_MAX_DUPLICATE_RATIO, C6_NGRAM_CONTAMINATION,
                                       Chunk, ChunkingConfig, validate_coherence)

    def make(doc_id, text, i):
        return Chunk(chunk_id=f"{doc_id}-C{i}", document_id=doc_id, chunk_index=i,
                     text=text, word_count=len(text.split()))

    paragraph = "The checkout service must retry failed card authorisations exactly twice."
    duplicated = paragraph + " " + "Retry budget is fixed at two attempts per order."

    chunks = [
        make("DOC-1", duplicated, 0),
        make("DOC-1", duplicated, 1),      # verbatim copy of chunk 0
        make("DOC-1", "Session tokens expire after thirty minutes of inactivity.", 2),
        make("DOC-1", "The warehouse ledger reconciles nightly against supplier invoices.", 3),
    ]
    assert C6_NGRAM_CONTAMINATION == 0.5
    assert C6_MAX_DUPLICATE_RATIO == 0.02

    from src.data_generation.v1_sample import build_mechanism_sample
    results = {r.check_id: r for r in validate_coherence(
        [], chunks, build_mechanism_sample(), ChunkingConfig())}
    c6 = results["C6"]
    assert not c6.passed, "C6 must FAIL on a verbatim duplicate pair"
    assert "1 pairs" in c6.observed


def test_revised_c6_ignores_shared_vocabulary_across_documents():
    """The old measure flagged different documents that merely shared a word type.
    Duplication is scoped to one document, so a near-identical chunk in a DIFFERENT
    document must not be flagged."""
    from src.chunking.splitter import Chunk, ChunkingConfig, validate_coherence
    from src.data_generation.v1_sample import build_mechanism_sample

    text = ("The checkout service retries failed card authorisations twice before "
            "escalating to the payment operations on-call engineer.")

    def make(doc_id, i):
        return Chunk(chunk_id=f"{doc_id}-C{i}", document_id=doc_id, chunk_index=i,
                     text=text, word_count=len(text.split()))

    chunks = [make("DOC-A", 0), make("DOC-B", 0)]
    results = {r.check_id: r for r in validate_coherence(
        [], chunks, build_mechanism_sample(), ChunkingConfig())}
    assert results["C6"].passed, "identical text in two documents is not chunk duplication"

"""
Regression tests for the final schema, renderer, chunker, and ground-truth derivation.

These lock in the four defects found during mechanism-sample validation, so a later change
cannot silently reintroduce them. Run:  python3 -m pytest tests/ -q
"""

import pytest
from typing import get_args

from src.chunking.splitter import (
    ChunkingConfig,
    _filler_text,
    _SyntheticDocument,
    chunk_corpus,
    project_scaling,
    validate_coherence,
)
from src.data_generation.render_v1 import render_corpus
from src.data_generation.source_model import LinkType, validate_model
from src.data_generation.v1_sample import build_mechanism_sample
from src.ground_truth.schema import (
    QuerySpec,
    band_for,
    derive_ground_truth,
    lexical_overlap,
    verify_traceable,
)

CONFIG = ChunkingConfig(1000, 200, "primary")


@pytest.fixture(scope="module")
def model():
    return build_mechanism_sample()


@pytest.fixture(scope="module")
def documents(model):
    return render_corpus(model)


@pytest.fixture(scope="module")
def chunks(documents):
    return chunk_corpus(documents, CONFIG)


# --- structure -------------------------------------------------------------

def test_all_structural_checks_pass(model):
    failures = [r for r in validate_model(model) if not r.passed]
    assert not failures, [r.detail for r in failures]


def test_every_document_type_rendered(documents):
    types = {d.doc_type for d in documents}
    expected = {"prd", "feature_spec", "pbi", "component_doc", "ticket",
                "decision_log", "meeting_notes", "runbook"}
    assert expected == types


def test_every_link_type_exercised(model):
    exercised = {l.link_type for l in model.document_links}
    assert exercised == set(get_args(LinkType)), (
        f"unexercised: {set(get_args(LinkType)) - exercised}"
    )


def test_explicit_and_implicit_dependencies_both_present(model):
    kinds = {d.explicitness for d in model.dependencies}
    assert kinds == {"explicit", "implicit"}


# --- regression: document subject (was the referenced entity) --------------

def test_pbi_document_subject_is_the_pbi(documents):
    """PBI and Ticket carry a feature_id REFERENCE; the subject must not be that."""
    for document in documents:
        if document.doc_type == "pbi":
            assert document.source_entity_id.startswith("PBI-"), document.source_entity_id
        if document.doc_type == "ticket":
            assert document.source_entity_id.startswith("TKT-"), document.source_entity_id
        if document.doc_type == "component_doc":
            assert document.source_entity_id.startswith("COMP-"), document.source_entity_id


def test_every_pbi_is_subject_of_a_chunk(model, chunks):
    subjects = {c.source_entity_id for c in chunks}
    assert {p.pbi_id for p in model.pbis} <= subjects


# --- regression: current-version resolution --------------------------------

def test_get_feature_returns_current_not_first(model):
    versioned = [f for f in model.features if
                 sum(1 for g in model.features if g.feature_id == f.feature_id) > 1]
    assert versioned, "sample must contain a versioned feature"
    for feature in versioned:
        assert model.get_feature(feature.feature_id).is_current
        assert model.get_feature(feature.feature_id).version == "2.0"


def test_get_prd_returns_current(model):
    prd = model.get_prd("PRD-A-01")
    assert prd.is_current and prd.version == "2.0"


# --- regression: chunk provenance propagation ------------------------------

def test_chunks_propagate_referenced_entities(chunks):
    pbi = next(c for c in chunks if c.source_entity_id == "PBI-A-011")
    assert "FEAT-A-01" in pbi.entity_ids
    assert "COMP-06" in pbi.all_entity_ids()


def test_no_chunk_without_provenance(chunks):
    assert [c.chunk_id for c in chunks if not c.all_entity_ids()] == []


def test_version_metadata_propagated(chunks):
    superseded = next(c for c in chunks if c.document_id == "DOC-PRD-A-01")
    current = next(c for c in chunks if c.document_id == "DOC-PRD-A-01-v2")
    assert superseded.is_current is False
    assert superseded.superseded_by == "DOC-PRD-A-01-v2"
    assert current.is_current is True
    assert current.supersedes == ["DOC-PRD-A-01"]


# --- determinism -----------------------------------------------------------

def test_build_is_deterministic(model, documents, chunks):
    rebuilt = build_mechanism_sample()
    assert rebuilt.to_dict() == model.to_dict()
    assert [d.body for d in render_corpus(rebuilt)] == [d.body for d in documents]
    assert [c.__dict__ for c in chunk_corpus(documents, CONFIG)] == [
        c.__dict__ for c in chunks
    ]


# --- chunker behaviour -----------------------------------------------------

def _long_doc(words=3000, doc_id="SYN-LONG"):
    return _SyntheticDocument(
        document_id=doc_id, doc_type="pbi", body=_filler_text(words)
    )


def test_large_document_is_split_into_multiple_chunks():
    result = chunk_corpus([_long_doc()], CONFIG)
    assert len(result) > 1


def test_chunking_never_splits_a_unit():
    """C1 as an exact property: every chunk is a contiguous run of whole units."""
    from src.chunking.splitter import _sections, _split_sentences

    document = _long_doc()
    units = []
    for _heading, section_text in _sections(document.body):
        units.extend(_split_sentences(section_text))
    allowed = {" ".join(units[i:j])
               for i in range(len(units)) for j in range(i + 1, len(units) + 1)}
    for chunk in chunk_corpus([document], CONFIG):
        assert chunk.text in allowed, f"{chunk.chunk_id} is not a contiguous unit run"


def test_overlap_carries_whole_units():
    from src.chunking.splitter import _sections, _split_sentences

    document = _long_doc()
    units = []
    for _heading, section_text in _sections(document.body):
        units.extend(_split_sentences(section_text))
    produced = chunk_corpus([document], CONFIG)
    for chunk in produced:
        for unit in _split_sentences(chunk.text):
            assert unit in units


def test_coherence_reports_only_c5_failing_on_sample(documents, chunks, model):
    results = {r.check_id: r for r in validate_coherence(documents, chunks, model, CONFIG)}
    assert [c for c, r in results.items() if not r.passed] == ["C5"]
    assert "SAMPLE-SCALE ARTEFACT" in results["C5"].observed


def test_projection_lands_near_approved_chunk_target():
    projection = project_scaling(CONFIG)
    assert projection["projected_total_documents"] == 272
    assert 250 <= projection["projected_total_chunks"] <= 330
    assert projection["projected_orphan_chunks"] == 0


# --- ground truth ----------------------------------------------------------

def test_ground_truth_resolves_without_scraping_chunk_text(model, documents, chunks):
    spec = QuerySpec(
        query_id="Q-TEST-1", slot=1, category="dependency_identification",
        target_entity_id="FEAT-A-01",
        target_document_ids=["DOC-FEAT-A-01-v2", "DOC-PRD-A-01-v2"],
        target_dependency_ids=["DEP-006"], dependency_explicitness="implicit",
    )
    gt = derive_ground_truth(spec, "Which service is reached first?", model, documents, chunks)
    assert gt.expected_dependencies == ["DEP-006"]
    assert set(gt.relevant_chunk_ids) == {"DOC-FEAT-A-01-v2-C0", "DOC-PRD-A-01-v2-C0"}
    assert verify_traceable(gt, model) == []


def test_ground_truth_fails_loudly_on_unknown_dependency(model, documents, chunks):
    spec = QuerySpec(
        query_id="Q-TEST-BAD", slot=1, category="dependency_identification",
        target_entity_id="FEAT-A-01", target_document_ids=["DOC-FEAT-A-01-v2"],
        target_dependency_ids=["DEP-DOES-NOT-EXIST"],
    )
    with pytest.raises(KeyError):
        derive_ground_truth(spec, "q", model, documents, chunks)


def test_ground_truth_fails_loudly_on_missing_document(model, documents, chunks):
    spec = QuerySpec(
        query_id="Q-TEST-BAD2", slot=1, category="information_retrieval",
        target_entity_id="X", target_document_ids=["DOC-NOT-A-DOCUMENT"],
    )
    with pytest.raises(KeyError):
        derive_ground_truth(spec, "q", model, documents, chunks)


def test_relevance_basis_detects_superseded():
    assert band_for(0.55) == "easy"
    assert band_for(0.30) == "moderate"
    assert band_for(0.10) == "hard"


def test_overlap_is_bounded_and_ignores_stopwords():
    assert lexical_overlap("the a of", "anything") == 0.0
    assert 0.0 <= lexical_overlap("tax documentation", "tax documentation collected") <= 1.0

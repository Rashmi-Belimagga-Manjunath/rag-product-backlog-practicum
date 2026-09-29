import pytest

from src.evaluation.dependency_evidence import (
    DependencyIndex,
    build_dependency_index,
    dependency_asserted,
    dependency_run_inputs,
    predicted_dependencies,
)
from src.evaluation.ground_truth import QueryGroundTruth
from src.retrieval.units import RetrievalUnit, RetrievalUnitSet


def make_unit(chunk_id, document_id, source_entity_id="", entity_ids=(), text="body"):
    from dataclasses import replace

    idx = int(chunk_id.rsplit("-C", 1)[1])
    u = RetrievalUnit(
        chunk_id=chunk_id,
        document_id=document_id,
        chunk_index=idx,
        text=text,
        source_entity_id=source_entity_id,
        entity_ids=list(entity_ids),
    )
    return u


UNITS = RetrievalUnitSet(
    units=[
        # declaring document of explicit dep A->Z
        make_unit("DOC-A-C0", "DOC-A", source_entity_id="A", entity_ids=["Z"]),
        make_unit("DOC-M-C0", "DOC-M", source_entity_id="M"),
        make_unit("DOC-P-C0", "DOC-P", source_entity_id="P"),
        make_unit("DOC-Q-C0", "DOC-Q", source_entity_id="Q"),
    ],
    by_id={
        "DOC-A-C0": make_unit("DOC-A-C0", "DOC-A", source_entity_id="A", entity_ids=["Z"]),
        "DOC-M-C0": make_unit("DOC-M-C0", "DOC-M", source_entity_id="M"),
        "DOC-P-C0": make_unit("DOC-P-C0", "DOC-P", source_entity_id="P"),
        "DOC-Q-C0": make_unit("DOC-Q-C0", "DOC-Q", source_entity_id="Q"),
    },
    by_document={},
)

# A->Z explicit (declared by DOC-A), M->N implicit (nothing declared), P->Q implicit
DEP_INDEX = DependencyIndex(by_id={
    "DEP-0001": ("A", "Z", "explicit"),
    "DEP-0105": ("M", "N", "implicit"),
    "DEP-0143": ("P", "Q", "implicit"),
})


def dummy_ground_truth(expected=()):
    return QueryGroundTruth(
        query_id="Q-01",
        slot=None,
        relevant_document_ids=("DOC-A",),
        relevant_chunk_ids=("DOC-A-C0",),
        expected_dependencies=tuple(expected),
        is_dependency_query=bool(expected),
        dependency_explicitness="explicit" if expected else "none",
        relevance_basis="test",
    )


class TestDependsOnImplementability:
    def test_build_dependency_index_from_model(self):
        # uses the real frozen model
        from src.data_generation.v1_full import build_final_corpus

        model = build_final_corpus()
        index = build_dependency_index(model)
        assert len(index.by_id) == len(model.dependencies)
        for dep in model.dependencies[:3]:
            assert dep.dependency_id in index.by_id


class TestDependencyAsserted:
    def test_explicit_declaring_doc_asserts(self):
        covers = {"DOC-A-C0": {"A", "Z"}}
        assert dependency_asserted("DEP-0001", ("A", "Z", "explicit"), covers) is True

    def test_explicit_not_asserted_without_declaration(self):
        covers = {"DOC-M-C0": {"M"}}
        assert dependency_asserted("DEP-0001", ("A", "Z", "explicit"), covers) is False

    def test_implicit_requires_both_endpoints(self):
        covers = {"DOC-P-C0": {"P"}, "DOC-Q-C0": {"Q"}}
        assert dependency_asserted("DEP-0143", ("P", "Q", "implicit"), covers) is True

    def test_implicit_fails_when_one_endpoint_missing(self):
        covers = {"DOC-P-C0": {"P"}}
        assert dependency_asserted("DEP-0143", ("P", "Q", "implicit"), covers) is False


class TestPredictedDependencies:
    def test_explicit_dependency_detected_from_retrieved_evidence(self):
        predicted = predicted_dependencies(
            dummy_ground_truth(expected=["DEP-0001"]),
            ["DOC-A-C0"], UNITS, DEP_INDEX,
        )
        assert predicted == {"DEP-0001"}

    def test_implicit_dependency_requires_two_chunks(self):
        # M is referenced only through coverage; with no chunk covering N, it
        # cannot be asserted even though the rest is retrieved.
        predicted = predicted_dependencies(
            dummy_ground_truth(expected=["DEP-0105"]),
            ["DOC-M-C0"], UNITS, DEP_INDEX,
        )
        assert predicted == set()

    def test_non_dependency_query_no_off_topic_assertions(self):
        predicted = predicted_dependencies(dummy_ground_truth(), ["DOC-Q-C0"], UNITS, DEP_INDEX)
        assert predicted == set()

    def test_run_inputs_rows_follows_slots(self):
        from src.evaluation.ground_truth import GroundTruthTable
        from src.benchmark.query_spec import SLOTS

        # Build a tiny table with a single entry to avoid building the full model.
        stubs = {
            s.query_id: dummy_ground_truth(["DEP-0001"] if s.query_id == "Q-01" else [])
            for s in SLOTS
        }
        table = GroundTruthTable(entries={k: v for k, v in stubs.items()})
        retrieved = {"Q-01": ["DOC-A-C0"]}
        rows = dependency_run_inputs(table, retrieved, UNITS, DEP_INDEX)
        assert len(rows) == 32
        # Q-01 (dependency query) predicts DEP-0001 when its declaring doc retrieved
        q01 = rows[0]
        assert q01[1] == {"DEP-0001"}
        assert q01[0] == {"DEP-0001"}
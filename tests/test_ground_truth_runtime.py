"""The critical agreement test.

The harness must derive ground truth at runtime EXACTLY as the committed
evidence workbook does. If it ever disagrees, line-of-evidence integrity is
broken. This test builds the final corpus, validates the ground-truth gate,
derives the relevant chunk sets from resolutions, and forces agreement against
data/exports/practicum_dataset_evidence.xlsx.
"""

import pytest

from src.benchmark.validate_ground_truth import validate_ground_truth
from src.data_generation.render_v1 import render_corpus
from src.data_generation.v1_full import build_final_corpus
from src.evaluation.ground_truth import (
    derive_ground_truth,
    load_export_query_ground_truth,
    verify_agreement_with_export,
)
from src.retrieval.units import load_frozen_units

WORKBOOK = "data/exports/practicum_dataset_evidence.xlsx"


@pytest.fixture(scope="module")
def frozen_inputs():
    model = build_final_corpus()
    documents = render_corpus(model)
    report = validate_ground_truth(model=model, documents=documents, against_final=True)
    units = load_frozen_units()
    return model, report, units


class TestRuntimeGroundTruth:
    def test_gate_freezes(self, frozen_inputs):
        _, report, _ = frozen_inputs
        assert report.freezable is True

    def test_all_32_queries_resolve_at_least_one_relevant(self, frozen_inputs):
        _, report, _ = frozen_inputs
        for slot_id, resolution in report.resolutions.items():
            assert len(resolution.document_ids) >= 1, slot_id

    def test_derivation_matches_committed_workbook(self, frozen_inputs):
        _, report, units = frozen_inputs
        summary = verify_agreement_with_export(units, report, WORKBOOK)
        assert summary["agreement"] == "PASS"
        assert summary["queries_checked"] == 32
        assert summary["workbook_rows"] >= 32

    def test_relevant_chunks_are_frozen_units(self, frozen_inputs):
        _, report, units = frozen_inputs
        table = derive_ground_truth(units, report)
        known = set(units.by_id)
        for entry in table.entries.values():
            assert known.issuperset(entry.relevant_chunk_ids)
            # chunk ids of a chunk set must map back to the relevant documents
            documents = {units.by_id[cid].document_id for cid in entry.relevant_chunk_ids}
            assert documents == set(entry.relevant_document_ids)

    def test_dependency_queries_carry_expected_dependencies(self, frozen_inputs):
        _, report, units = frozen_inputs
        from src.benchmark.query_spec import SLOTS

        table = derive_ground_truth(units, report)
        dependency_entries = [e for e in table.entries.values() if e.is_dependency_query]
        assert len(dependency_entries) == 13
        for entry in dependency_entries:
            assert entry.expected_dependencies, entry.query_id

    def test_frozen_chunk_count_is_272(self, frozen_inputs):
        _, _, units = frozen_inputs
        assert len(units.units) == 272

    def test_workbook_has_rows_for_every_query(self):
        rows = load_export_query_ground_truth(WORKBOOK)
        assert len(rows) == 32
        for query_id, chunk_ids in rows.items():
            assert query_id.startswith("Q")
            assert len(chunk_ids) >= 1
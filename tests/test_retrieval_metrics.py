import pytest

from src.benchmark.query_spec import SLOTS
from src.evaluation.ground_truth import GroundTruthTable, QueryGroundTruth
from src.evaluation.retrieval_metrics import (
    QueryRetrieval,
    build_query_retrievals,
    score_run,
    ZeroRelevantError,
)


def make_row(query_id, retrieved, relevant, category="Information retrieval",
             difficulty="easy", failed=False, is_dep=False, expl="none"):
    return QueryRetrieval(
        query_id=query_id,
        category=category,
        difficulty=difficulty,
        retrieved_chunk_ids=tuple(retrieved),
        relevant_chunk_ids=frozenset(relevant),
        is_dependency_query=is_dep,
        dependency_explicitness=expl,
        failed=failed,
    )


class TestQueryLevelMetrics:
    def test_perfect_precision_and_recall(self):
        row = make_row("Q1", ["c1", "c2", "c3", "c4", "c5"], ["c1", "c2", "c3"])
        assert row.precision_at_5() == pytest.approx(3 / 5)
        assert row.recall_at_5() == pytest.approx(1.0)
        assert row.reciprocal_rank() == pytest.approx(1.0)

    def test_recall_respects_relevant_size(self):
        row = make_row("Q1", ["c1", "c2", "c3", "c4", "c5"], ["c1", "c2", "c3", "c4", "c5", "c6"])
        assert row.recall_at_5() == pytest.approx(5 / 6)
        assert row.precision_at_5() == pytest.approx(1.0)

    def test_mrr_uses_first_relevant_rank(self):
        row = make_row("Q1", ["a", "b", "c1", "c2", "c3"], ["c1"])
        assert row.reciprocal_rank() == pytest.approx(1 / 3)


class TestShortfallDenominator:
    def test_precision_uses_actually_returned(self):
        row = make_row("Q1", ["c1", "c2"], ["c1", "x9"])
        # denominator is 2 (actually returned), not 5
        assert row.precision_at_5() == pytest.approx(1 / 2)
        assert row.recall_at_5() == pytest.approx(1 / 2)

    def test_empty_retrieval_scores_zero_precision(self):
        row = make_row("Q1", [], ["c1"])
        assert row.precision_at_5() == 0.0


class TestFailedRuns:
    def test_failed_scores_zero_everywhere(self):
        row = make_row("Q1", ["c1", "c2", "c3"], ["c1", "c2", "c3"], failed=True)
        assert row.precision_at_5() == 0.0
        assert row.recall_at_5() == 0.0
        assert row.reciprocal_rank() == 0.0


class TestZeroRelevantAbort:
    def test_recall_aborts_when_no_relevant(self):
        row = make_row("Q1", ["c1"], [])
        with pytest.raises(ZeroRelevantError):
            row.recall_at_5()

    def test_precision_still_scores_when_no_relevant(self):
        # D-009 defines zero-relevant as an abort case; precision is undefined
        # but we raise on recall so a broken ground truth cannot slip through.
        row = make_row("Q1", ["c1"], [])
        assert row.precision_at_5() == 0.0


class TestAggregation:
    def test_macro_average_over_queries(self):
        rows = [
            make_row("Q1", ["c1"], ["c1"]),          # p=1.0
            make_row("Q2", ["a1"], ["x1", "x2"]),     # p=0.0, mrr=0
            make_row("Q3", ["x1", "c1"], ["c1"]),     # p=1/2, mrr=1/2
        ]
        metrics = score_run("s", rows)
        assert metrics.n_queries == 3
        assert metrics.mean_precision == pytest.approx((1.0 + 0.0 + 0.5) / 3)
        assert metrics.mean_recall == pytest.approx((1.0 + 0.0 + 1.0) / 3)
        assert metrics.mean_mrr == pytest.approx((1.0 + 0.0 + 0.5) / 3)

    def test_per_query_values_retained(self):
        rows = [make_row("Q1", ["c1"], ["c1"], category="Feature context", difficulty="hard")]
        metrics = score_run("s", rows)
        assert metrics.precision_by_category["Feature context"] == pytest.approx(1.0)
        assert metrics.precision_by_difficulty["hard"] == pytest.approx(1.0)

    def test_failed_query_stays_in_denominator(self):
        rows = [make_row("Q1", ["c1"], ["c1"]), make_row("Q2", ["c1"], ["c1"], failed=True)]
        metrics = score_run("s", rows)
        assert metrics.n_failed == 1
        assert metrics.mean_precision == pytest.approx(0.5)

    def test_per_query_preserves_row_order(self):
        # score_run aggregates over the rows exactly as provided; canonical
        # slot ordering is established upstream by build_query_retrievals
        # (see TestCanonicalRowOrder), not re-imposed here.
        rows = [make_row("Q-09", ["c1"], ["c1"]), make_row("Q-01", ["c1"], ["c1"])]
        metrics = score_run("s", rows)
        assert [r["query_id"] for r in metrics.per_query] == ["Q-09", "Q-01"]

    def test_dependency_split_reported(self):
        rows = [
            make_row("Q1", ["c1"], ["c1"], is_dep=True, expl="explicit"),
            make_row("Q2", ["c1"], ["c1"], is_dep=True, expl="implicit"),
        ]
        metrics = score_run("s", rows)
        assert metrics.precision_explicit == pytest.approx(1.0)
        assert metrics.precision_implicit == pytest.approx(1.0)


def make_fake_entries() -> dict:
    """One QueryGroundTruth per frozen slot (synthetic relevance for ordering tests)."""
    entries = {}
    for slot in SLOTS:
        entries[slot.query_id] = QueryGroundTruth(
            query_id=slot.query_id,
            slot=slot,
            relevant_document_ids=("DOC-X",),
            relevant_chunk_ids=("DOC-X#C0",),
            expected_dependencies=(),
            is_dependency_query=True,
            dependency_explicitness="explicit",
            relevance_basis="test",
        )
    return entries


class TestCanonicalRowOrder:
    def test_build_query_retrievals_follows_slot_order(self):
        # The frozen per-query ordering guarantee: rows are emitted in ascending
        # slot order (Q-01 .. Q-32) no matter how the retrieval dict is keyed.
        gt = GroundTruthTable(entries=make_fake_entries())
        retrieved = {slot.query_id: ["DOC-X#C0"] for slot in SLOTS}
        rows = build_query_retrievals(retrieved, gt)
        expected = [slot.query_id for slot in sorted(SLOTS, key=lambda s: s.slot)]
        assert [row.query_id for row in rows] == expected
        assert rows[0].query_id == "Q-01"
        assert len(rows) == len(SLOTS)
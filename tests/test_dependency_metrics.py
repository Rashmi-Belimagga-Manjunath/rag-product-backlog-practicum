import pytest

from src.evaluation.dependency_metrics import score_dependency_run

D = {"d1", "d2"}


def make_results(predictor, failed_indices=(), n=32, n_dep=13):
    """n_dep = number of queries with a non-empty expected set (front-loaded)."""
    out = []
    for i in range(n):
        expected = D if i < n_dep else set()
        predicted = predictor(i) if i not in failed_indices else set()
        out.append((predicted, expected, i in failed_indices))
    return out


class TestZeroDenominatorConvention:
    """The all-negative predictor must NOT get superficially perfect precision."""

    def test_all_negative_is_not_scored_perfect(self):
        m = score_dependency_run(make_results(lambda i: set()))
        assert m.precision == pytest.approx(19 / 32)  # 0.0 on the 13, 1.0 on the 19
        assert m.recall == pytest.approx(0.0)
        assert m.f1 == pytest.approx(0.0)
        assert m.vacuous_correct_count == 19

    def test_empty_prediction_with_expected_deps_scores_zero(self):
        m = score_dependency_run(make_results(lambda i: set()))
        assert m.precision_on_dependency_queries == pytest.approx(0.0)
        assert m.recall == pytest.approx(0.0)
        assert m.f1 == pytest.approx(0.0)

    def test_empty_prediction_with_empty_expectation_is_vacuous_correct(self):
        m = score_dependency_run(make_results(lambda i: set()))
        # 19 queries have E(q) = {} and the system correctly asserted nothing.
        assert m.precision_on_non_dependency_queries == pytest.approx(1.0)
        assert m.vacuous_correct_count == 19

    def test_recall_f1_are_not_reported_when_never_expected(self):
        # A run that only ever aborts before recall: all dependency queries failed,
        # so recall is applied to 0 queries in the recall population... but they DO
        # have expected sets, so they must still be failures, not exclusions.
        m = score_dependency_run(make_results(lambda i: set(), failed_indices=range(13)))
        assert m.recall == pytest.approx(0.0)
        assert m.f1 == pytest.approx(0.0)


class TestFailedRun:
    """A crashed run is a failure, never a correct empty answer."""

    def test_failed_run_scores_zero_everywhere(self):
        m = score_dependency_run(make_results(lambda i: set(), failed_indices=range(32)))
        assert m.precision == pytest.approx(0.0)
        assert m.recall == pytest.approx(0.0)
        assert m.f1 == pytest.approx(0.0)
        assert m.vacuous_correct_count == 0

    def test_failed_run_cannot_earn_vacuous_credit(self):
        # even on non-dependency queries (E empty), a failure is 0, not 1.0
        m = score_dependency_run(make_results(lambda i: set(), failed_indices=range(13, 32)))
        assert m.precision_on_non_dependency_queries == pytest.approx(0.0)
        assert m.vacuous_correct_count == 0


class TestSanity:
    def test_perfect(self):
        m = score_dependency_run(make_results(lambda i: D if i < 13 else set()))
        assert m.precision == pytest.approx(1.0)
        assert m.recall == pytest.approx(1.0)
        assert m.f1 == pytest.approx(1.0)

    def test_hallucinator_gets_zero(self):
        # invents a dependency on every query, including the 19 with none
        m = score_dependency_run(make_results(lambda i: {"X"}))
        assert m.precision == pytest.approx(0.0)
        assert m.recall == pytest.approx(0.0)
        assert m.f1 == pytest.approx(0.0)

    def test_over_predictor_is_penalised(self):
        m = score_dependency_run(make_results(lambda i: (D | {"X"}) if i < 13 else set()))
        assert m.precision == pytest.approx((13 * (2 / 3) + 19) / 32)
        assert m.recall == pytest.approx(1.0)
        assert m.f1 == pytest.approx(0.8)

    def test_half_correct(self):
        m = score_dependency_run(make_results(lambda i: {"d1"} if i < 13 else set()))
        assert m.precision == pytest.approx(1.0)
        assert m.recall == pytest.approx(0.5)
        assert m.f1 == pytest.approx(2 / 3)
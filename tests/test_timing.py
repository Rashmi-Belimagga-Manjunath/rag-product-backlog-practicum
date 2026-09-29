import pytest

from src.experiments.timing import interleave_ab, median_of_three


class TestMedianOfThree:
    def test_median_after_warmup_discard(self):
        samples = [100.0, 2.0, 4.0, 8.0]  # first = warm-up (discarded)
        assert median_of_three(samples) == pytest.approx(4.0)

    def test_requires_four_samples(self):
        with pytest.raises(ValueError):
            median_of_three([1.0, 2.0, 3.0])

    def test_odd_trial_count_only(self):
        # exactly 1 + 3
        assert median_of_three([0.0, 1.0, 2.0, 3.0]) == pytest.approx(2.0)


class TestInterleaveAB:
    def test_alternates_systems(self):
        trials = interleave_ab(["Q1", "Q2"])
        assert trials == [("Q1", "bm25"), ("Q1", "rag"),
                          ("Q2", "bm25"), ("Q2", "rag")]

    def test_each_query_appears_twice(self):
        from collections import Counter

        trials = interleave_ab(["Q1", "Q2", "Q3"])
        counts = Counter(query_id for query_id, _ in trials)
        assert counts == {"Q1": 2, "Q2": 2, "Q3": 2}
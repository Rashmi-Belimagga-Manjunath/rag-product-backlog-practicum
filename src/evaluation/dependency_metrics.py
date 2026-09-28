from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Set


@dataclass(frozen=True)
class DependencyRunMetrics:
    """Aggregate dependency accuracy metrics (D-009).

    - ``precision`` is the macro-average over **all** queries that received a
      dependency judgement (every query in a run).
    - ``recall`` and ``f1`` are the macro-average over the queries with a
      non-empty expected dependency set only (the dependency-related queries).
    - ``precision_on_dependency_queries`` and ``precision_on_non_dependency_queries``
      report the split, so the population mix cannot hide behaviour.
    - ``vacuous_correct_count`` is how many queries contributed the 1.0
      vacuous-correct convention (accepted with a correct empty expectation).
    """

    precision: float
    recall: Optional[float]
    f1: Optional[float]
    precision_on_dependency_queries: float
    precision_on_non_dependency_queries: float
    vacuous_correct_count: int
    n_queries: int
    n_recall_queries: int


def score_dependency_run(
    query_results: Iterable[tuple[Set[str], Set[str], bool]],
) -> DependencyRunMetrics:
    """Score one run.

    Each element is ``(predicted, expected, failed)``. ``failed`` marks a query
    whose run failed outright (no retrieval output). The expected set is empty on
    non-dependency queries, which are precision-only by the applicability rule.

    The explicit zero-denominator convention (rationale in
    ``docs/evaluation_metrics.md`` §5):

    - ``predicted`` empty and ``expected`` empty -> correct vacuous prediction,
      precision contribution 1.0; recall/F1 undefined (not applicable).
    - ``predicted`` empty and ``expected`` non-empty -> misidentified every
      dependency, precision contribution 0.0 and recall 0.0.
    - ``predicted`` non-empty -> standard ``TP/(TP+FP)``.
    - any query **failed** -> contributes 0.0 to precision regardless of the
      expected set; it never earns the vacuous-correct 1.0, because a crashed
      run is a failure, not a correct empty answer.
    """

    n = 0
    n_recall = 0
    vacuous = 0
    precisions: list[float] = []
    precisions_dep: list[float] = []
    precisions_ndep: list[float] = []
    recalls: list[float] = []
    f1s: list[float] = []

    for predicted, expected, failed in query_results:
        if failed:
            p, r, f = 0.0, 0.0, 0.0
            vacuous_check = False
        else:
            tp = len(predicted & expected)
            fp = len(predicted - expected)
            fn = len(expected - predicted)

            if not predicted and not expected:
                p, r, f = 1.0, None, None
                vacuous_check = True
            elif not predicted:
                p, r, f = 0.0, 0.0, 0.0
                vacuous_check = False
            else:
                p = tp / (tp + fp)
                vacuous_check = False
                if expected:
                    r = tp / (tp + fn)
                    denom = 2 * tp + fp + fn
                    f = (2 * tp / denom) if denom else 0.0
                else:
                    r, f = None, None

        n += 1
        if vacuous_check:
            vacuous += 1
        precisions.append(p)
        if expected:
            n_recall += 1
            precisions_dep.append(p)
            if r is not None:
                recalls.append(r)
            if f is not None:
                f1s.append(f)
        else:
            precisions_ndep.append(p)

    mean = lambda xs: sum(xs) / len(xs) if xs else None
    return DependencyRunMetrics(
        precision=mean(precisions) if precisions else 0.0,
        recall=mean(recalls),
        f1=mean(f1s),
        precision_on_dependency_queries=(
            mean(precisions_dep) if precisions_dep else None
        ),
        precision_on_non_dependency_queries=(
            mean(precisions_ndep) if precisions_ndep else None
        ),
        vacuous_correct_count=vacuous,
        n_queries=n,
        n_recall_queries=n_recall,
    )
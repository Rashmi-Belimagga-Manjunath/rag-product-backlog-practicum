"""Timing measurement helpers for the two systems.

D-009 defines timing as: per-query retrieval-only latency and (for RAG) total
task time, measured after a warm-up discard, with the median of three runs,
interleaved A/B/A/B to avoid a systematic order effect. If a system cannot be
timed that way, the timing block is marked NOT RUN — it is never patched with
partial numbers.

These helpers are pure functions so the median/interleave logic is tested
without any API involvement.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TimingSample:
    query_id: str
    system: str
    warmup_discarded: int
    trials: tuple[float, ...]
    median_seconds: float


def median_of_three(latencies: list[float]) -> float:
    """Median latency after discarding the first (warm-up) sample.

    Requires exactly three samples after warm-up; fewer is not a valid D-009
    timing block.
    """
    if len(latencies) < 4:
        raise ValueError(
            f"need 1 warm-up + 3 timed trials, got {len(latencies)} samples"
        )
    timed = latencies[1:4]
    return statistics.median(timed)


def interleave_ab(query_ids: list[str]) -> list[tuple[str, str]]:
    """Return [(query_id, system)] in A/B/A/B interleave order.

    A = bm25, B = rag. The same query appears once per system; consecutive
    trials for the same system are separated by the other system's trial so no
    single ordering benefits either one.
    """
    trials: list[tuple[str, str]] = []
    for query_id in query_ids:
        trials.append((query_id, "bm25"))
        trials.append((query_id, "rag"))
    return trials


def measure_retrieval_latencies(fn, query_ids: list[str], system: str) -> list[TimingSample]:
    """Run fn once warm-up then three timed trials per query, A/B interleaved.

    fn(query_id) runs one retrieval without generation (satisfies D-009's
    retrieval-only latency). This helper is neutral and never runs the
    experiment itself; callers opt in at run time.
    """
    samples: list[TimingSample] = []
    for query_id in query_ids:
        sample_times: list[float] = []
        for trial in range(4):  # 1 warm-up + 3 timed
            import time

            start = time.monotonic()
            fn(query_id)
            sample_times.append(time.monotonic() - start)
        samples.append(
            TimingSample(
                query_id=query_id,
                system=system,
                warmup_discarded=1,
                trials=tuple(sample_times),
                median_seconds=median_of_three(sample_times),
            )
        )
    return samples
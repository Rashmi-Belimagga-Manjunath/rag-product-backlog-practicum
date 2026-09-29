"""Load experiment results for thesis packaging.

This module READS ONLY COMPUTED OUTPUT produced by src/experiments.runner
(processed/metrics_overall.json) and the per-query raw evidence. It never
computes a metric itself, so a report built from it cannot contain a number the
experiment did not measure. It validates the structure it finds and raises if
any expected field is missing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

EXPECTED_TOP_LEVEL = {"run_id", "bm25", "rag", "dependency_bm25", "dependency_rag", "classifications"}
EXPECTED_METRIC_KEYS = {
    "n_queries", "n_failed", "mean_precision", "mean_recall", "mean_mrr",
    "precision_by_category", "recall_by_category", "mrr_by_category",
    "precision_by_difficulty", "recall_by_difficulty",
    "precision_explicit", "recall_explicit", "precision_implicit", "recall_implicit",
}
EXPECTED_DEPENDENCY_KEYS = {"precision", "recall", "f1", "n_queries", "n_recall_queries"}


@dataclass(frozen=True)
class SystemMetrics:
    name: str
    n_queries: int
    n_failed: int
    mean_precision: float
    mean_recall: float
    mean_mrr: float
    precision_by_category: dict
    recall_by_category: dict
    mrr_by_category: dict
    precision_by_difficulty: dict
    recall_by_difficulty: dict
    precision_explicit: float
    recall_explicit: float
    precision_implicit: float
    recall_implicit: float
    per_query: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class DependencyMetrics:
    precision: float
    recall: float
    f1: float
    precision_on_dependency_queries: float
    precision_on_non_dependency_queries: float
    n_queries: int
    n_recall_queries: int
    vacuous_correct_count: int


@dataclass(frozen=True)
class ThesisResults:
    run_id: str
    bm25: SystemMetrics
    rag: SystemMetrics
    dependency_bm25: DependencyMetrics
    dependency_rag: DependencyMetrics
    classifications_bm25: list[dict]
    classifications_rag: list[dict]
    evidence_sources: str


def _validate_missing(mapping: dict, expected: set[str], label: str) -> None:
    missing = expected - set(mapping)
    if missing:
        raise ValueError(f"{label} missing fields: {sorted(missing)}")


def _load_system(name: str, payload: dict) -> SystemMetrics:
    _validate_missing(payload, EXPECTED_METRIC_KEYS, f"system metrics {name}")
    return SystemMetrics(
        name=name,
        n_queries=int(payload["n_queries"]),
        n_failed=int(payload["n_failed"]),
        mean_precision=float(payload["mean_precision"]),
        mean_recall=float(payload["mean_recall"]),
        mean_mrr=float(payload["mean_mrr"]),
        precision_by_category=payload["precision_by_category"],
        recall_by_category=payload["recall_by_category"],
        mrr_by_category=payload["mrr_by_category"],
        precision_by_difficulty=payload["precision_by_difficulty"],
        recall_by_difficulty=payload["recall_by_difficulty"],
        precision_explicit=float(payload["precision_explicit"]),
        recall_explicit=float(payload["recall_explicit"]),
        precision_implicit=float(payload["precision_implicit"]),
        recall_implicit=float(payload["recall_implicit"]),
        per_query=payload.get("per_query", []),
    )


def _load_dependency(label: str, payload: dict) -> DependencyMetrics:
    _validate_missing(payload, EXPECTED_DEPENDENCY_KEYS, f"dependency metrics {label}")
    return DependencyMetrics(
        precision=float(payload["precision"]),
        recall=float(payload["recall"]) if payload["recall"] is not None else None,
        f1=float(payload["f1"]) if payload["f1"] is not None else None,
        precision_on_dependency_queries=(
            float(payload["precision_on_dependency_queries"])
            if payload["precision_on_dependency_queries"] is not None else None
        ),
        precision_on_non_dependency_queries=(
            float(payload["precision_on_non_dependency_queries"])
            if payload["precision_on_non_dependency_queries"] is not None else None
        ),
        n_queries=int(payload["n_queries"]),
        n_recall_queries=int(payload["n_recall_queries"]),
        vacuous_correct_count=int(payload.get("vacuous_correct_count", 0)),
    )


def load_processed(processed_dir: str) -> ThesisResults:
    metrics_path = Path(processed_dir) / "metrics_overall.json"
    if not metrics_path.exists():
        raise FileNotFoundError(
            f"no metrics_overall.json at {metrics_path}; the experiment must be "
            "executed and evaluated before results packaging"
        )
    with open(metrics_path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)
    _validate_missing(raw, EXPECTED_TOP_LEVEL, "metrics_overall")
    classifications = raw["classifications"]
    return ThesisResults(
        run_id=str(raw["run_id"]),
        bm25=_load_system("bm25", raw["bm25"]),
        rag=_load_system("rag", raw["rag"]),
        dependency_bm25=_load_dependency("bm25", raw["dependency_bm25"]),
        dependency_rag=_load_dependency("rag", raw["dependency_rag"]),
        classifications_bm25=classifications["bm25"]["per_query"],
        classifications_rag=classifications["rag"]["per_query"],
        evidence_sources=str(raw.get("evidence_sources", "")),
    )
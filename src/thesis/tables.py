"""Thesis-ready tables, built strictly from computed results.

Each table is a CSV plus a sidecar tracing it to the evidence sources
(tables/<name>.evidence.json). The figures module and report both consume these
tables, so every figure/table is traceable back to the per-query evidence
(AGENTS.md §5, the "traceability" thesis requirement).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from src.embeddings.cache import matrix_sha256
from src.experiments.runner import RunPaths
from src.thesis.results import ThesisResults


def _write_csv(path: Path, headers: list[str], rows: list[list]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def _write_evidence_sidecar(path: Path, source: str) -> None:
    sidecar = {
        "table": path.name,
        "generated_from": source,
        "note": "Built only from computed experiment outputs; no estimates.",
    }
    with open(path.with_suffix(".evidence.json"), "w", encoding="utf-8") as handle:
        json.dump(sidecar, handle, indent=2, sort_keys=True)
        handle.write("\n")


def build_all_tables(run_paths: RunPaths, results: ThesisResults) -> list[Path]:
    """Write every required table; returns written paths."""
    written: list[Path] = []
    written.append(_overall_table(run_paths, results))
    written.append(_per_query_table(run_paths, results))
    written.append(_dependency_table(run_paths, results))
    written.append(_category_table(run_paths, results))
    written.append(_difficulty_table(run_paths, results))
    written.append(_explicitness_table(run_paths, results))
    written.append(_error_table(run_paths, results))
    return written


def _overall_table(run_paths: RunPaths, results: ThesisResults) -> Path:
    path = run_paths.tables_dir / "overall_metrics.csv"
    rows = [
        ["system", "precision@5", "recall@5", "mrr@5"],
        ["BM25", results.bm25.mean_precision, results.bm25.mean_recall, results.bm25.mean_mrr],
        ["RAG", results.rag.mean_precision, results.rag.mean_recall, results.rag.mean_mrr],
    ]
    _write_csv(path, rows[0], rows[1:])
    _write_evidence_sidecar(path, results.evidence_sources)
    return path


def _per_query_table(run_paths: RunPaths, results: ThesisResults) -> Path:
    path = run_paths.tables_dir / "per_query.csv"
    sources = results.bm25.per_query
    rag_by_query = {row["query_id"]: row for row in results.rag.per_query}
    headers = ["query_id", "category", "difficulty",
               "bm25_precision@5", "bm25_recall@5", "bm25_mrr",
               "rag_precision@5", "rag_recall@5", "rag_mrr"]
    rows: list[list] = []
    for row in sources:
        rag = rag_by_query[row["query_id"]]
        rows.append([row["query_id"], row["category"], row["difficulty"],
                     row["precision@5"], row["recall@5"], row["mrr"],
                     rag["precision@5"], rag["recall@5"], rag["mrr"]])
    _write_csv(path, headers, rows)
    _write_evidence_sidecar(path, results.evidence_sources)
    return path


def _dependency_table(run_paths: RunPaths, results: ThesisResults) -> Path:
    path = run_paths.tables_dir / "dependency_metrics.csv"
    headers = ["system", "precision", "recall", "f1",
               "precision_on_dependency_queries", "precision_on_non_dependency_queries"]
    rows = [
        ["BM25", results.dependency_bm25.precision, results.dependency_bm25.recall,
         results.dependency_bm25.f1, results.dependency_bm25.precision_on_dependency_queries,
         results.dependency_bm25.precision_on_non_dependency_queries],
        ["RAG", results.dependency_rag.precision, results.dependency_rag.recall,
         results.dependency_rag.f1, results.dependency_rag.precision_on_dependency_queries,
         results.dependency_rag.precision_on_non_dependency_queries],
    ]
    _write_csv(path, headers, rows)
    _write_evidence_sidecar(path, results.evidence_sources)
    return path


def _category_table(run_paths: RunPaths, results: ThesisResults) -> Path:
    path = run_paths.tables_dir / "category_metrics.csv"
    categories = sorted(set(results.bm25.precision_by_category) | set(results.rag.precision_by_category))
    headers = ["category", "bm25_precision@5", "bm25_recall@5", "bm25_mrr",
               "rag_precision@5", "rag_recall@5", "rag_mrr"]
    rows = [
        [category,
         results.bm25.precision_by_category.get(category, 0.0),
         results.bm25.recall_by_category.get(category, 0.0),
         results.bm25.mrr_by_category.get(category, 0.0),
         results.rag.precision_by_category.get(category, 0.0),
         results.rag.recall_by_category.get(category, 0.0),
         results.rag.mrr_by_category.get(category, 0.0)]
        for category in categories
    ]
    _write_csv(path, headers, rows)
    _write_evidence_sidecar(path, results.evidence_sources)
    return path


def _difficulty_table(run_paths: RunPaths, results: ThesisResults) -> Path:
    path = run_paths.tables_dir / "difficulty_metrics.csv"
    difficulties = sorted(set(results.bm25.precision_by_difficulty)
                          | set(results.rag.precision_by_difficulty))
    headers = ["difficulty", "bm25_precision@5", "bm25_recall@5",
               "rag_precision@5", "rag_recall@5"]
    rows = [
        [difficulty,
         results.bm25.precision_by_difficulty.get(difficulty, 0.0),
         results.bm25.recall_by_difficulty.get(difficulty, 0.0),
         results.rag.precision_by_difficulty.get(difficulty, 0.0),
         results.rag.recall_by_difficulty.get(difficulty, 0.0)]
        for difficulty in difficulties
    ]
    _write_csv(path, headers, rows)
    _write_evidence_sidecar(path, results.evidence_sources)
    return path


def _explicitness_table(run_paths: RunPaths, results: ThesisResults) -> Path:
    path = run_paths.tables_dir / "explicit_vs_implicit.csv"
    headers = ["explicitness", "bm25_precision@5", "bm25_recall@5",
               "rag_precision@5", "rag_recall@5"]
    rows = [
        ["explicit", results.bm25.precision_explicit, results.bm25.recall_explicit,
         results.rag.precision_explicit, results.rag.recall_explicit],
        ["implicit", results.bm25.precision_implicit, results.bm25.recall_implicit,
         results.rag.precision_implicit, results.rag.recall_implicit],
    ]
    _write_csv(path, headers, rows)
    _write_evidence_sidecar(path, results.evidence_sources)
    return path


def _error_table(run_paths: RunPaths, results: ThesisResults) -> Path:
    path = run_paths.tables_dir / "error_classifications.csv"
    headers = ["system", "judgement", "count"]
    counts_bm25 = _counts(results.classifications_bm25)
    counts_rag = _counts(results.classifications_rag)
    judgements = sorted(set(counts_bm25) | set(counts_rag))
    rows = [
        ["bm25", judgement, counts_bm25.get(judgement, 0)] for judgement in judgements
    ] + [
        ["rag", judgement, counts_rag.get(judgement, 0)] for judgement in judgements
    ]
    _write_csv(path, headers, rows)
    _write_evidence_sidecar(path, results.evidence_sources)
    return path


def _counts(classifications: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in classifications:
        counts[entry["judgement"]] = counts.get(entry["judgement"], 0) + 1
    return counts


def embedding_fingerprint_sidecar(run_paths: RunPaths) -> None:
    """Record the stored matrix hash so table sidecars can reference it."""
    try:
        fingerprint = matrix_sha256()
    except FileNotFoundError:
        fingerprint = "not-built-yet"
    with open(run_paths.processed_dir / "embedding_fingerprint.json", "w", encoding="utf-8") as handle:
        json.dump({"sha256": fingerprint}, handle, indent=2)
        handle.write("\n")
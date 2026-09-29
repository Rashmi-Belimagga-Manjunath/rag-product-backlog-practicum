"""Thesis figures, generated only from computed results.

Every figure is written from the same machine-readable inputs the tables use
(processed/metrics_overall.json), so a figure is always traceable to the
per-query evidence. matplotlib is imported lazily; when it is not installed the
generator raises a clear InstallRequirement error instead of silently producing
empty charts.
"""

from __future__ import annotations

from pathlib import Path

from src.experiments.runner import RunPaths
from src.thesis.results import ThesisResults


def _import_matplotlib():
    try:
        import matplotlib
        import matplotlib.pyplot as plt

        matplotlib.use("Agg")
        return matplotlib, plt
    except ImportError as error:
        raise RuntimeError(
            "matplotlib is required to build figures; install it and run again"
        ) from error


def _grouped_bar(path: Path, labels: list[str], bm25: list[float], rag: list[float],
                 title: str, ylabel: str) -> Path:
    _, plt = _import_matplotlib()
    _, ax = plt.subplots(figsize=(8, 4.5))
    import numpy as np

    x = np.arange(len(labels))
    width = 0.38
    ax.bar(x - width / 2, bm25, width, label="BM25")
    ax.bar(x + width / 2, rag, width, label="RAG")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.legend()
    ax.tick_params(axis="x", labelsize=8)
    ax.set_ylim(0, max(1.0, max(bm25 + rag + [0.05]) * 1.05))
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    figure = plt.gcf()
    figure.savefig(path, dpi=220)
    plt.close(figure)
    return path


def _simple_bar(path: Path, labels: list[str], values: list[float], title: str,
                ylabel: str) -> Path:
    _, plt = _import_matplotlib()
    _, ax = plt.subplots(figsize=(8, 4))
    ax.bar(labels, values)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, max(1.0, max(values + [0.05]) * 1.05))
    plt.tight_layout()
    figure = plt.gcf()
    figure.savefig(path, dpi=220)
    plt.close(figure)
    return path


def build_all_figures(run_paths: RunPaths, results: ThesisResults) -> list[Path]:
    written: list[Path] = []
    written.append(
        _grouped_bar(run_paths.figures_dir / "bm25_vs_rag_retrieval_metrics.png",
                     ["Precision@5", "Recall@5", "MRR@5"],
                     [results.bm25.mean_precision, results.bm25.mean_recall, results.bm25.mean_mrr],
                     [results.rag.mean_precision, results.rag.mean_recall, results.rag.mean_mrr],
                     "BM25 vs RAG retrieval metrics @5", "")
    )

    written.append(
        _simple_bar(run_paths.figures_dir / "dependency_metrics.png",
                    ["Precision", "Recall", "F1"],
                    [results.dependency_bm25.precision,
                     results.dependency_bm25.recall or 0.0,
                     results.dependency_bm25.f1 or 0.0],
                    "BM25 dependency metrics", "value")
    )
    written.append(
        _simple_bar(run_paths.figures_dir / "dependency_metrics_rag.png",
                    ["Precision", "Recall", "F1"],
                    [results.dependency_rag.precision,
                     results.dependency_rag.recall or 0.0,
                     results.dependency_rag.f1 or 0.0],
                    "RAG dependency metrics", "value")
    )

    written.append(
        _grouped_bar(
            run_paths.figures_dir / "category_comparison.png",
            sorted(set(results.bm25.precision_by_category)
                   | set(results.rag.precision_by_category)),
            [results.bm25.precision_by_category.get(c, 0.0) for c in sorted(
                set(results.bm25.precision_by_category) | set(results.rag.precision_by_category))],
            [results.rag.precision_by_category.get(c, 0.0) for c in sorted(
                set(results.bm25.precision_by_category) | set(results.rag.precision_by_category))],
            "Precision@5 by category", "precision@5",
        )
    )

    written.append(
        _grouped_bar(
            run_paths.figures_dir / "difficulty_comparison.png",
            sorted(set(results.bm25.precision_by_difficulty)
                   | set(results.rag.precision_by_difficulty)),
            [results.bm25.precision_by_difficulty.get(d, 0.0) for d in sorted(
                set(results.bm25.precision_by_difficulty) | set(results.rag.precision_by_difficulty))],
            [results.rag.precision_by_difficulty.get(d, 0.0) for d in sorted(
                set(results.bm25.precision_by_difficulty) | set(results.rag.precision_by_difficulty))],
            "Precision@5 by difficulty", "precision@5",
        )
    )

    written.append(
        _grouped_bar(
            run_paths.figures_dir / "explicit_vs_implicit.png",
            ["explicit", "implicit"],
            [results.bm25.precision_explicit, results.bm25.precision_implicit],
            [results.rag.precision_explicit, results.rag.precision_implicit],
            "Precision@5 explicit vs implicit", "precision@5",
        )
    )

    written.append(
        _simple_bar(run_paths.figures_dir / "error_distribution.png",
                    ["BM25 retrieval fail", "RAG retrieval fail", "RAG generation fail",
                     "RAG fabrication", "RAG mis-citation", "Review needed"],
                    [ _count(results.classifications_bm25, "RETRIEVAL_FAILURE"),
                      _count(results.classifications_rag, "RETRIEVAL_FAILURE"),
                      _count(results.classifications_rag, "GENERATION_FAILURE"),
                      _count(results.classifications_rag, "FABRICATION"),
                      _count(results.classifications_rag, "MIS_CITATION"),
                      _count(results.classifications_rag, "REQUIRE_MANUAL_REVIEW")],
                    "Error distribution", "query count",
                    )
    )
    return written


def _count(classifications: list[dict], judgement: str) -> int:
    return sum(1 for entry in classifications if entry["judgement"] == judgement)
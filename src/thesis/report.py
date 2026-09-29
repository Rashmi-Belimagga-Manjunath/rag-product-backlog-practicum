"""Factual experiment report (results/EXP-YYYYMMDD-NNN/experiment_report.md).

The report is assembled ONLY from:
  * the frozen configuration files (read verbatim), and
  * the computed results (ThesisResults from processed/metrics_overall.json).

It never states a measurement the experiment did not produce, and it never draws
conclusions. The final "Thesis Interpretation Inputs" section lists factual
observations the student can use when writing their own Discussion/Conclusion;
it is not a conclusion.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.thesis.results import ThesisResults

FROZEN_CONFIG_SOURCES = {
    "BM25": "experiments/configs/bm25_config.json",
    "Embeddings": "experiments/configs/embedding_config.json",
    "RAG": "experiments/configs/rag_config.json",
}


def _config_summary() -> dict:
    summary: dict[str, str] = {}
    for label, path in FROZEN_CONFIG_SOURCES.items():
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        if label == "BM25":
            summary["BM25 k1 / b / idf"] = (
                f"{raw['scoring']['k1']} / {raw['scoring']['b']} / {raw['scoring']['idf']}"
            )
        elif label == "Embeddings":
            summary["Embedding model"] = raw["model_name"]
            summary["Embedding dimension"] = str(raw["embedding_dimension"])
            summary["Vector store"] = (
                f"{raw['vector_store']['name']} {raw['vector_store']['version_verified']} "
                f"({raw['vector_store']['metric']})"
            )
        elif label == "RAG":
            summary["Generation model"] = raw["generation"]["model_name"]
            summary["Temperature / max_tokens"] = (
                f"{raw['generation']['temperature']} / {raw['generation']['max_tokens']}"
            )
            summary["Topk (retrieval)"] = str(raw["retrieval"]["top_k"])
    return summary


def build_report(run_paths, results: ThesisResults) -> Path:
    """Write experiment_report.md for the run."""
    config = _config_summary()
    path = run_paths.results_dir / "experiment_report.md"

    sections = [
        f"# Experiment Report — {results.run_id}",
        "",
        "This report is generated from the frozen methodology and the computed outputs",
        "of the executed experiment only. Every measurement below originates from the per-query",
        f"evidence at `{results.evidence_sources}`.",
        "",
        "## Experimental objective",
        "",
        "Compare the frozen BM25 baseline against the frozen RAG configuration over the same",
        "272 retrieval units, the same 32 benchmark queries, the same ground truth and the same",
        "top-5 cutoff (docs/evaluation_metrics.md D-009). The comparison isolates retrieval and,",
        "for RAG, the generation layer.",
        "",
        "## Corpus",
        "",
        "- Full frozen corpus: 272 retrieval units (one chunk per document, `data/corpus/`).",
        "- Doc types include PRDs, feature specs, PBIs, tickets, components, notes and decisions",
        "  (structurally heterogeneous; AGENTS.md §4).",
        "",
        "## Benchmark",
        "",
        "- 32 benchmark queries (slot-ordered).",
        "- 13 dependency-related queries (6 explicit, 7 implicit).",
        "- Frozen difficulty designations and category labels in `src/benchmark/query_spec.py`.",
        "- Ground truth derived from the benchmark resolutions (relevant documents mapped to their",
        "  frozen chunks); verified against the committed evidence workbook before this run.",
        "",
        "## System configuration",
    ]
    for label, value in config.items():
        sections.append(f"- {label}: {value}")
    sections += [
        "",
        "- Retrieval units: identical objects for both systems (`src/retrieval/units.py`).",
        "- BM25 implemented in-repo per bm25_config.json (Lucene non-negative IDF, k1/b as frozen,",
        "  `[\\w']+` tokeniser, no stemming/stopword removal, verbatim queries).",
        "- RAG uses Chroma cosine over the frozen embedding matrix and the frozen GPT-4o-mini",
        "  generation config with the frozen prompt (`rag_prompt.txt`).",
        "",
        "## Experimental procedure",
        "",
        f"- Run id: `{results.run_id}`.",
        f"- Raw per-query evidence: `{results.evidence_sources}`.",
        "- BM25 ran over the 32 queries; RAG retrieval used the same vectorstore then generated",
        "  answers. Failed queries were recorded with a reason and scored 0.0 (D-009).",
        "- No arbitrary demo/prototype query is part of this run.",
        "",
        "## Evaluation methodology",
        "",
        "- Metrics frozen in docs/evaluation_metrics.md: Precision@5, Recall@5, MRR@5, macro",
        "  averaged over the per-query values.",
        "- Dependency precision/recall/F1 over the expected vs derived-predicted dependency",
        "  sets (implementation disclosure: dependency evidence rule in",
        "  `src/evaluation/dependency_evidence.py`).",
        "- RAG error classifications are evidence-driven (retrieval failure, fabrication,",
        "  mis-citation, abstention-with-evidence, or REQUIRE_MANUAL_REVIEW).",
        "",
        "## Results",
        "",
        "### Overall (mean @5)",
        "",
        "| system | precision@5 | recall@5 | mrr@5 |",
        "|---|---|---|---|",
        f"| BM25 | {results.bm25.mean_precision:.4f} | {results.bm25.mean_recall:.4f} | {results.bm25.mean_mrr:.4f} |",
        f"| RAG | {results.rag.mean_precision:.4f} | {results.rag.mean_recall:.4f} | {results.rag.mean_mrr:.4f} |",
        "",
        "### Dependency accuracy",
        "",
        "| system | precision | recall | f1 |",
        "|---|---|---|---|",
        f"| BM25 | {results.dependency_bm25.precision:.4f} | {results.dependency_bm25.recall if results.dependency_bm25.recall is not None else 'n/a'} | "
        f"{results.dependency_bm25.f1 if results.dependency_bm25.f1 is not None else 'n/a'} |",
        f"| RAG | {results.dependency_rag.precision:.4f} | {results.dependency_rag.recall if results.dependency_rag.recall is not None else 'n/a'} | "
        f"{results.dependency_rag.f1 if results.dependency_rag.f1 is not None else 'n/a'} |",
        "",
        "### Error analysis",
        "",
        "- BM25 classified errors: see `tables/error_classifications.csv`.",
        "- RAG classified errors: see `tables/error_classifications.csv`.",
        "- IMPORTANT: answers whose chain could not be classified from evidence alone are recorded",
        "  as REQUIRE_MANUAL_REVIEW and must not be counted as correct or incorrect by the report.",
        "",
        "### Per-query, category, difficulty, explicit/implicit tables",
        "",
        "- `tables/per_query.csv`",
        "- `tables/category_metrics.csv`",
        "- `tables/difficulty_metrics.csv`",
        "- `tables/explicit_vs_implicit.csv`",
        "",
        "## Reproducibility",
        "",
        "- Frozen config hashes are recorded in `processed/run_metadata.json` and the FREEZE",
        "  manifest (data/manifest/FREEZE.json).",
        "- Embedding matrix fingerprint: see `processed/embedding_fingerprint.json`.",
        "- Git commit: recorded in run metadata.",
        "",
        "## Limitations",
        "",
        "- Retrieval metrics are computed at the top-5 cutoff only (frozen).",
        "- RAG generation correctness beyond citation/abstention rules is not automatically judged",
        "  (REQUIRE_MANUAL_REVIEW rows).",
        "- Dependency predictions are derived from retrieved evidence via a disclosed rule; the",
        "  rule itself is an operationalisation of D-009 and is documented in dependency_evidence.py.",
        "",
        "## Unresolved / deferred evaluation components",
        "",
        "- Human (supervisor) ratings of RAG answer correctness (Layer B) are deferred; the",
        "  automated pipeline stops at REQUIRE_MANUAL_REVIEW.",
        "",
        "## Thesis Interpretation Inputs",
        "",
        "Factual observations for the student's own Discussion/Conclusion (no conclusions drawn here):",
        "",
    ]
    sections += _interpretation_inputs(results)

    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(sections))
    return path


def _interpretation_inputs(results: ThesisResults) -> list[str]:
    """Concise factual observations; never interpretive claims."""
    bm25, rag = results.bm25, results.rag
    inputs = [
        "- Mean Precision@5: BM25 "
        f"{bm25.mean_precision:.4f} vs RAG {rag.mean_precision:.4f} "
        f"(difference {rag.mean_precision - bm25.mean_precision:+.4f}).",
        "- Mean Recall@5: BM25 "
        f"{bm25.mean_recall:.4f} vs RAG {rag.mean_recall:.4f} "
        f"(difference {rag.mean_recall - bm25.mean_recall:+.4f}).",
        "- Mean MRR@5: BM25 "
        f"{bm25.mean_mrr:.4f} vs RAG {rag.mean_mrr:.4f} "
        f"(difference {rag.mean_mrr - bm25.mean_mrr:+.4f}).",
        f"- Failed queries: BM25 {bm25.n_failed}, RAG {rag.n_failed} (must both be 0 on a clean run).",
        "- Dependency precision: BM25 "
        f"{results.dependency_bm25.precision:.4f} vs RAG {results.dependency_rag.precision:.4f}.",
        "- Dependency recall: "
        f"{results.dependency_bm25.recall if results.dependency_bm25.recall is not None else 'n/a'} "
        f"vs {results.dependency_rag.recall if results.dependency_rag.recall is not None else 'n/a'}.",
        "- RAG classification counts: "
        + ", ".join(f"{k}={_count(results.classifications_rag, k)}"
                    for k in ["RETRIEVAL_FAILURE", "GENERATION_FAILURE", "FABRICATION",
                              "MIS_CITATION", "REQUIRE_MANUAL_REVIEW"]),
    ]
    return inputs


def _count(classifications: list[dict], judgement: str) -> int:
    return sum(1 for entry in classifications if entry["judgement"] == judgement)
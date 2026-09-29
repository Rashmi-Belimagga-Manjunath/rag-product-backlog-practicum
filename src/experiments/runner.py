"""Run orchestration for the two systems.

Layers:
  * check  — validate all frozen inputs, create nothing. This is the only
             command permitted before checkpoint approval. It performs NO
             retrieval over the benchmark.
  * bm25   — run the frozen BM25 baseline over the 32 queries.
  * rag    — run retrieval + generation with the frozen RAG configuration.
  * all    — bm25 then rag.
  * evaluate — read a run's raw evidence, compute all metrics (D-009), write
             processed/json, tables/csv, figures and the report.

Every per-query record is written verbatim to experiments/runs/<run_id>/raw/<system>/
as JSON (AGENTS.md §5 raw/), and evaluation output goes to
results/EXP-YYYYMMDD-NNN/{processed,tables,figures}. A failed query is recorded
with its reason and still contributes 0.0 to every metric (D-009), never dropped.

No API key, token or secret is ever written to a log, a sidecar, a manifest or a
results file: the only key-related value recorded is the boolean
"api_key_available".
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from src.evaluation.classify import classify_bm25, classify_rag, RagClassificationInputs
from src.evaluation.dependency_evidence import build_dependency_index, dependency_run_inputs
from src.evaluation.dependency_metrics import score_dependency_run
from src.evaluation.retrieval_metrics import build_query_retrievals, score_run
from src.experiments.inputs import ExperimentInputs, load_experiment_inputs
from src.rag.citations import extract_citations, parse_all, supplied_citation_ids, validate
from src.rag.context import build_context
from src.rag.generator import generate

RUNS_ROOT = "experiments/runs"
RESULTS_ROOT = "results"


@dataclass(frozen=True)
class RunPaths:
    run_id: str
    run_dir: Path
    results_dir: Path
    raw_dir: Path
    processed_dir: Path
    tables_dir: Path
    figures_dir: Path

    @classmethod
    def for_run(cls, run_id: str, runs_root: str = RUNS_ROOT,
                results_root: str = RESULTS_ROOT, *, require_absent: bool = True) -> "RunPaths":
        run_dir = Path(runs_root) / run_id
        # Writers (run_bm25 / run_rag) must never append to an existing run;
        # evaluate_run reads an existing run's raw evidence and only creates the
        # results dir, so it opts out of this guard.
        if require_absent:
            assert not run_dir.exists(), f"run directory already exists: {run_dir}"
        results_dir = Path(results_root) / run_id
        raw_dir = run_dir / "raw"
        processed_dir = results_dir / "processed"
        tables_dir = results_dir / "tables"
        figures_dir = results_dir / "figures"
        return cls(
            run_id=run_id,
            run_dir=run_dir,
            results_dir=results_dir,
            raw_dir=raw_dir,
            processed_dir=processed_dir,
            tables_dir=tables_dir,
            figures_dir=figures_dir,
        )

    def create(self, *, raw: bool = True) -> None:
        # raw dirs are owned by the run writers (run_bm25 / run_rag); results
        # dirs are owned by evaluate_run. evaluate_run calls with raw=False
        # because the run dir already exists at that point.
        if raw:
            for path in (self.run_dir / "raw" / "bm25", self.run_dir / "raw" / "rag"):
                path.mkdir(parents=True, exist_ok=False)
        for path in (self.processed_dir, self.tables_dir, self.figures_dir):
            path.mkdir(parents=True, exist_ok=False)


def git_head_commit() -> str:
    """Committed hash used by the freeze manifest and run metadata."""
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        return "unknown"


def write_metadata(paths: RunPaths, inputs: ExperimentInputs) -> None:
    from src.embeddings.generate import api_key_available

    metadata = {
        "run_id": paths.run_id,
        "frozen_inputs": inputs.artifact_hashes,
        "git_commit": git_head_commit(),
        "api_key_available": api_key_available(),
        "embedding_artefact_fingerprint": None,
        "n_queries": inputs.benchmark.n_queries,
        "top_k": inputs.bm25_config.top_k,
    }
    with open(paths.run_dir / "metadata.json", "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
        handle.write("\n")
    with open(paths.processed_dir / "run_metadata.json", "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
        handle.write("\n")


def check(inputs: ExperimentInputs, run_id: str | None = None) -> dict:
    """Validation-only entry point. Creates NOTHING and scores no query."""
    from src.embeddings.generate import api_key_available

    run_id = run_id or inputs.run_id
    return {
        "status": "READY",
        "run_id": run_id,
        "n_queries": inputs.benchmark.n_queries,
        "top_k": inputs.bm25_config.top_k,
        "prompt_sha256": inputs.prompt_sha256[:16] + "...",
        "ground_truth_agreement": inputs.agreement,
        "frozen_config_hashes": inputs.artifact_hashes,
        "api_key_available_boolean_only": api_key_available(),
    }


def run_bm25(inputs: ExperimentInputs, paths: RunPaths) -> list[dict]:
    """Run the frozen BM25 baseline. Writes raw/bm25/<query_id>.json per query."""
    from src.bm25.retriever import BM25Index

    index = BM25Index(units=inputs.units, config=inputs.bm25_config)
    results: list[dict] = []
    for query_id in inputs.benchmark.query_ids:
        query_text = inputs.query_text(query_id)
        try:
            bm25_result = index.query(query_id=query_id, query_text=query_text)
            record = {
                "system": "bm25",
                "query_id": query_id,
                "query_text": query_text,
                "status": "ok",
                "retrieved": [hit.as_dict() for hit in bm25_result.hits],
            }
        except Exception as error:
            record = {
                "system": "bm25",
                "query_id": query_id,
                "query_text": query_text,
                "status": "failed",
                "failure_reason": f"{type(error).__name__}: {error}",
            }
        with open(paths.raw_dir / "bm25" / f"{query_id}.json", "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
            handle.write("\n")
        results.append(record)
    return results


def run_rag(inputs: ExperimentInputs, paths: RunPaths, client, embed_query,
            store) -> list[dict]:
    """Run retrieval + generation with the frozen config.

    Retrieval goes through the frozen Chroma store exactly like the BM25
    baseline (same units, same units-of-retrieval), then generation through the
    frozen prompt. embed_query(query_text) -> np.ndarray opens the same frozen
    embedding model for a single input at run time; it is supplied by the caller
    so this module stays API-free, and the store is supplied by the caller so a
    run deliberately reuses the frozen vectorstore artefact.

    Citation validation runs in the same record so raw evidence and validated
    citations sit side by side (AGENTS.md §3).
    """
    from src.rag.context import build_context

    if store.collection.count() == 0:
        raise RuntimeError(
            "vectorstore is empty; build it at the freeze step with "
            "VectorStore.build_from_loaded(loaded, units)"
        )

    results: list[dict] = []
    for query_id in inputs.benchmark.query_ids:
        query_text = inputs.query_text(query_id)
        try:
            query_embedding = embed_query(query_text)
            hits = store.search_topk(query_embedding, inputs.rag_config.top_k, inputs.units)
            context = build_context(query_text, hits, inputs.units, inputs.prompt_sha256)
            result = generate(client, inputs.rag_config, context)
            citation_texts = extract_citations(result.answer)
            citations, unknown_raw = parse_all(citation_texts)
            supplied = supplied_citation_ids([h.chunk_id for h in hits])
            citation_report = validate(citations, supplied)
            record = {
                "system": "rag",
                "query_id": query_id,
                "query_text": query_text,
                "status": "ok",
                "retrieved": [{"chunk_id": h.chunk_id, "rank": i + 1,
                               "score": h.score, "document_id": h.document_id}
                              for i, h in enumerate(hits)],
                "generated_answer": result.answer,
                "finish_reason": result.finish_reason,
                "model": result.model,
                "usage": result.usage,
                "latency_seconds_total": result.latency_seconds,
                "source_citations": [c.raw for c in citation_report.citations],
                "fabricated_citations": [c.raw for c in citation_report.fabricated],
                "unknown_citation_tokens": unknown_raw,
            }
        except Exception as error:
            record = {
                "system": "rag",
                "query_id": query_id,
                "query_text": query_text,
                "status": "failed",
                "failure_reason": f"{type(error).__name__}: {error}",
            }
        with open(paths.raw_dir / "rag" / f"{query_id}.json", "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
            handle.write("\n")
        results.append(record)
    return results


def _load_evidence(run_id: str, runs_root: str = RUNS_ROOT) -> tuple[list[dict], list[dict]]:
    """Read raw per-query JSON records for both systems from a run directory."""
    def load(system: str) -> list[dict]:
        path = Path(runs_root) / run_id / "raw" / system
        records = []
        for file in sorted(path.glob("*.json")):
            with open(file, "r", encoding="utf-8") as handle:
                records.append(json.load(handle))
        return records

    return load("bm25"), load("rag")


def retrieved_chunk_ids(record: dict) -> list[str]:
    return [row["chunk_id"] for row in record.get("retrieved", [])]


def evaluate_run(run_id: str, inputs: ExperimentInputs,
                 runs_root: str = RUNS_ROOT, results_root: str = RESULTS_ROOT) -> dict:
    """Compute D-009 metrics from a run's raw evidence, write results.

    Produces processed/metrics_<system>.json, processed/metrics_overall.json,
    tables/*.csv, and delegates figures/report to the thesis builders. Every
    number here is computed from the per-query records written by run_bm25 /
    run_rag; nothing is estimated.
    """
    bm25_records, rag_records = _load_evidence(run_id, runs_root)
    if not bm25_records or not rag_records:
        raise FileNotFoundError(f"missing raw evidence for run {run_id}")

    paths = RunPaths.for_run(run_id, runs_root=runs_root, results_root=results_root,
                             require_absent=False)
    paths.create(raw=False)
    write_metadata(paths, inputs)

    dep_index = build_dependency_index(inputs.model)
    retrieved_bm25 = {r["query_id"]: retrieved_chunk_ids(r) for r in bm25_records}
    retrieved_rag = {r["query_id"]: retrieved_chunk_ids(r) for r in rag_records}

    bm25_rows = build_query_retrievals(retrieved_bm25, inputs.ground_truth)
    rag_rows = build_query_retrievals(retrieved_rag, inputs.ground_truth)

    bm25_metrics = score_run("bm25", bm25_rows)
    rag_metrics = score_run("rag", rag_rows)

    bm25_classifications = [classify_bm25(list(r.retrieved_chunk_ids), inputs.ground_truth.entries[r.query_id])
                            for r in bm25_rows]
    rag_classifications = []
    rag_by_query = {r["query_id"]: r for r in rag_records}
    for row in rag_rows:
        record = rag_by_query[row.query_id]
        citations_texts = extract_citations(record.get("generated_answer", ""))
        citations, unknown = parse_all(citations_texts)
        supplied = supplied_citation_ids(list(row.retrieved_chunk_ids))
        report = validate(citations, supplied)
        rag_classifications.append(
            classify_rag(RagClassificationInputs(
                retrieved_chunk_ids=list(row.retrieved_chunk_ids),
                ground_truth=inputs.ground_truth.entries[row.query_id],
                citation_report=report,
                answer=record.get("generated_answer", ""),
            ))
        )

    dep_inputs = {
        "bm25": dependency_run_inputs(inputs.ground_truth, retrieved_bm25, inputs.units, dep_index),
        "rag": dependency_run_inputs(inputs.ground_truth, retrieved_rag, inputs.units, dep_index),
    }
    dep_bm25 = score_dependency_run(dep_inputs["bm25"])
    dep_rag = score_dependency_run(dep_inputs["rag"])

    result = {
        "run_id": run_id,
        "bm25": bm25_metrics.as_dict(),
        "rag": rag_metrics.as_dict(),
        "dependency_bm25": _dependency_as_dict(dep_bm25),
        "dependency_rag": _dependency_as_dict(dep_rag),
        "classifications": {
            "bm25": {"counts": _classification_counts(bm25_classifications),
                     "per_query": [c.__dict__ for c in bm25_classifications]},
            "rag": {"counts": _classification_counts(rag_classifications),
                    "per_query": [c.__dict__ for c in rag_classifications]},
        },
        "evidence_sources": f"experiments/runs/{run_id}/raw",
    }

    with open(paths.processed_dir / "metrics_overall.json", "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")

    # Thesis packaging: tables + figures + report, all from computed/results only.
    from src.thesis.figures import build_all_figures
    from src.thesis.report import build_report
    from src.thesis.results import load_processed
    from src.thesis.tables import build_all_tables, embedding_fingerprint_sidecar

    embedding_fingerprint_sidecar(paths)
    thesis_results = load_processed(str(paths.processed_dir))
    build_all_tables(paths, thesis_results)
    build_all_figures(paths, thesis_results)
    build_report(paths, thesis_results)

    return result


def _dependency_as_dict(metrics) -> dict:
    return {
        "precision": metrics.precision,
        "recall": metrics.recall,
        "f1": metrics.f1,
        "precision_on_dependency_queries": metrics.precision_on_dependency_queries,
        "precision_on_non_dependency_queries": metrics.precision_on_non_dependency_queries,
        "vacuous_correct_count": metrics.vacuous_correct_count,
        "n_queries": metrics.n_queries,
        "n_recall_queries": metrics.n_recall_queries,
    }


def _classification_counts(classifications) -> dict[str, int]:
    counts: dict[str, int] = {}
    for classification in classifications:
        counts[classification.judgement] = counts.get(classification.judgement, 0) + 1
    return counts


def cli(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or argv[0] == "--help":
        print(__doc__)
        return 0

    command = argv[0]
    try:
        if command == "check":
            print(json.dumps(check(load_experiment_inputs()), indent=2))
            return 0
        if command in ("bm25", "rag", "all"):
            raise RuntimeError(
                "experimental commands are locked until checkpoint approval"
            )
        if command == "evaluate":
            raise RuntimeError(
                "evaluation runs only after an approved experiment run"
            )
        print(f"unknown command {command!r}", file=sys.stderr)
        return 2
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(cli())
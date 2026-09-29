import json
from pathlib import Path

import pytest

from src.experiments.inputs import BenchmarkConfig, ExperimentInputs, load_experiment_inputs
from src.experiments.runner import (
    RunPaths,
    check,
    cli,
    evaluate_run,
    run_bm25,
)
from src.retrieval.units import RetrievalUnit, RetrievalUnitSet


def make_small_inputs(tmp_path):
    """A deliberately NON-benchmark ExperimentInputs (queries named DEMO-* only)."""
    a = RetrievalUnit(chunk_id="DOC-A-C0", document_id="DOC-A", chunk_index=0,
                      text="apple banana cake")
    b = RetrievalUnit(chunk_id="DOC-B-C0", document_id="DOC-B", chunk_index=0,
                      text="nothing relevant")
    units = RetrievalUnitSet(
        units=[a, b],
        by_id={"DOC-A-C0": a, "DOC-B-C0": b},
        by_document={"DOC-A": [a], "DOC-B": [b]},
    )

    from src.bm25.retriever import BM25Config
    from src.embeddings.generate import EmbeddingConfig
    from src.rag.generator import RAGConfig

    return ExperimentInputs(
        model=None,
        units=units,
        report=None,
        ground_truth=None,
        benchmark=BenchmarkConfig(
            query_ids=("DEMO-1", "DEMO-2"),
            query_texts={"DEMO-1": "apple banana", "DEMO-2": "banana cake"},
            n_queries=2,
        ),
        bm25_config=BM25Config.load(),
        embedding_config=EmbeddingConfig.load(),
        rag_config=RAGConfig.load(),
        prompt_sha256="fake-sha",
        agreement={"agreement": "PASS"},
        run_id="EXP-00000000-000",
        artifact_hashes={},
    )


class TestCliLocks:
    def test_check_returns_readily_and_creates_nothing(self, tmp_path):
        inputs = make_small_inputs(tmp_path)
        entry = check(inputs, run_id="EXP-20260101-001")
        assert entry["status"] == "READY"
        assert entry["n_queries"] == 2
        # validation must not scaffold run or result directories
        assert (tmp_path / "runs").exists() is False
        assert (tmp_path / "results").exists() is False

    def test_experimental_commands_are_blocked(self, capsys):
        for command in ["bm25", "rag", "all", "evaluate"]:
            assert cli([command]) == 3  # locked until checkpoint approval
        out = capsys.readouterr()
        assert "locked" in out.err


class TestRunBM25:
    def test_writes_per_query_json_records(self, tmp_path):
        inputs = make_small_inputs(tmp_path)
        paths = RunPaths.for_run("EXP-20260101-001",
                                 runs_root=str(tmp_path / "runs"),
                                 results_root=str(tmp_path / "results"))
        paths.create()
        records = run_bm25(inputs, paths)
        assert len(records) == 2
        for record in records:
            assert record["system"] == "bm25"
            assert record["status"] == "ok"
            assert "retrieved" in record
        file_1 = tmp_path / "runs" / "EXP-20260101-001" / "raw" / "bm25" / "DEMO-1.json"
        assert file_1.exists()

    def test_failed_query_is_recorded_not_dropped(self, tmp_path, monkeypatch):
        inputs = make_small_inputs(tmp_path)
        from src.bm25.retriever import BM25Index

        def boom(self, **kwargs):
            raise ValueError("injected failure")

        monkeypatch.setattr(BM25Index, "query", boom)
        paths = RunPaths.for_run("EXP-20260101-001",
                                 runs_root=str(tmp_path / "runs"),
                                 results_root=str(tmp_path / "results"))
        paths.create()
        records = run_bm25(inputs, paths)
        for record in records:
            assert record["status"] == "failed"
            assert "injected failure" in record["failure_reason"]

    def test_refuses_existing_run_dir(self, tmp_path):
        inputs = make_small_inputs(tmp_path)
        (tmp_path / "runs" / "EXP-20260101-001").mkdir(parents=True)
        with pytest.raises(AssertionError):
            RunPaths.for_run("EXP-20260101-001",
                             runs_root=str(tmp_path / "runs"),
                             results_root=str(tmp_path / "results"))


@pytest.fixture(scope="module")
def real_inputs():
    return load_experiment_inputs()


class TestEvaluatePipeline:
    def test_evaluate_produces_all_results(self, tmp_path, real_inputs):
        run_id = "EXP-20260101-001"
        runs_root = str(tmp_path / "runs")
        results_root = str(tmp_path / "results")

        # Synthetic (deliberately empty-retrieval) evidence for all 32 queries.
        # This is infrastructure testing only: no real retrieval is run, and the
        # numbers are all-zero placeholders, never reported elsewhere.
        for system in ("bm25", "rag"):
            raw_dir = Path(runs_root) / run_id / "raw" / system
            raw_dir.mkdir(parents=True)
            for query_id in real_inputs.benchmark.query_ids:
                record = {
                    "system": system, "query_id": query_id,
                    "query_text": real_inputs.query_text(query_id),
                    "status": "ok", "retrieved": [],
                }
                if system == "rag":
                    record["generated_answer"] = ""
                with open(raw_dir / f"{query_id}.json", "w", encoding="utf-8") as handle:
                    json.dump(record, handle)

        result = evaluate_run(run_id, real_inputs, runs_root=runs_root, results_root=results_root)
        assert result["run_id"] == run_id
        assert result["bm25"]["n_queries"] == 32
        assert result["rag"]["n_queries"] == 32

        results_dir = Path(results_root) / run_id
        assert (results_dir / "processed" / "metrics_overall.json").exists()
        assert (results_dir / "processed" / "run_metadata.json").exists()
        assert (results_dir / "processed" / "embedding_fingerprint.json").exists()
        for table in ["overall_metrics.csv", "per_query.csv", "dependency_metrics.csv",
                      "category_metrics.csv", "difficulty_metrics.csv",
                      "explicit_vs_implicit.csv", "error_classifications.csv"]:
            assert (results_dir / "tables" / table).exists(), table
        assert (results_dir / "experiment_report.md").exists()

        # figures require matplotlib (installed); error distribution etc.
        figures = list((results_dir / "figures").glob("*.png"))
        assert len(figures) >= 6

    def test_metadata_never_contains_secrets(self, tmp_path, real_inputs):
        run_id = "EXP-20260101-002"
        (Path(tmp_path) / "runs" / run_id / "raw" / "bm25").mkdir(parents=True)
        (Path(tmp_path) / "runs" / run_id / "raw" / "rag").mkdir(parents=True)
        for system in ("bm25", "rag"):
            path = Path(tmp_path) / "runs" / run_id / "raw" / system
            for query_id in real_inputs.benchmark.query_ids:
                with open(path / f"{query_id}.json", "w") as handle:
                    json.dump({"system": system, "query_id": query_id, "status": "ok",
                               "retrieved": [], "generated_answer": ""}, handle)

        evaluate_run(run_id, real_inputs,
                     runs_root=str(tmp_path / "runs"),
                     results_root=str(tmp_path / "results"))
        metadata_path = Path(tmp_path) / "results" / run_id / "processed" / "run_metadata.json"
        with open(metadata_path, encoding="utf-8") as handle:
            metadata = json.load(handle)
        joined = json.dumps(metadata)
        assert "sk-" not in joined
        assert "OPENAI" not in joined
        # the only api_* field is the documented boolean availability flag;
        # the key itself is fine, but it must never carry a key value.
        api_related = [key for key in metadata if "api_key" in key.lower()]
        assert api_related == ["api_key_available"]
        assert metadata["api_key_available"] in (True, False)
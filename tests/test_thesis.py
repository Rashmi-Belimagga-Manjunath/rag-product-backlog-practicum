import csv
import json
from pathlib import Path

import pytest

from src.experiments.runner import RunPaths
from src.thesis.figures import build_all_figures
from src.thesis.report import build_report
from src.thesis.results import EXPECTED_TOP_LEVEL, load_processed
from src.thesis.tables import build_all_tables


def metric_payload(run_id="EXP-20260101-001"):
    """Minimal but structurally-valid metrics_overall.json (synthetic numbers)."""
    def system(name):
        return {
            "system": name,
            "n_queries": 32,
            "n_failed": 0,
            "mean_precision": 0.5 if name == "bm25" else 0.6,
            "mean_recall": 0.4 if name == "bm25" else 0.45,
            "mean_mrr": 0.55 if name == "bm25" else 0.65,
            "precision_by_category": {"Information retrieval": 0.5, "Feature context": 0.5},
            "recall_by_category": {"Information retrieval": 0.4, "Feature context": 0.4},
            "mrr_by_category": {"Information retrieval": 0.5, "Feature context": 0.5},
            "precision_by_difficulty": {"easy": 0.6, "moderate": 0.5, "hard": 0.4},
            "recall_by_difficulty": {"easy": 0.6, "moderate": 0.5, "hard": 0.4},
            "precision_explicit": 0.5,
            "recall_explicit": 0.5,
            "precision_implicit": 0.5,
            "recall_implicit": 0.5,
            "per_query": [
                {"query_id": "Q-02", "category": "Feature context", "difficulty": "hard",
                 "retrieved_count": 5, "relevant_count": 2, "precision@5": 0.4,
                 "recall@5": 0.5, "mrr": 0.25, "failed": False},
                {"query_id": "Q-01", "category": "Information retrieval", "difficulty": "easy",
                 "retrieved_count": 5, "relevant_count": 1, "precision@5": 0.2,
                 "recall@5": 1.0, "mrr": 0.2, "failed": False},
            ],
        }

    def dep(name):
        return {
            "precision": 0.5, "recall": 0.4, "f1": 0.44,
            "precision_on_dependency_queries": 0.5,
            "precision_on_non_dependency_queries": 1.0,
            "vacuous_correct_count": 19, "n_queries": 32, "n_recall_queries": 13,
        }

    def classifications():
        return {
            "bm25": {"counts": {},
                     "per_query": [{"query_id": "Q-01", "system": "bm25",
                                    "judgement": "RETRIEVAL_FAILURE", "evidence": []}]},
            "rag": {"counts": {},
                    "per_query": [{"query_id": "Q-01", "system": "rag",
                                   "judgement": "REQUIRE_MANUAL_REVIEW", "evidence": []}]},
        }

    return {
        "run_id": run_id,
        "bm25": system("bm25"),
        "rag": system("rag"),
        "dependency_bm25": dep("bm25"),
        "dependency_rag": dep("rag"),
        "classifications": classifications(),
        "evidence_sources": f"experiments/runs/{run_id}/raw",
    }


@pytest.fixture
def run_paths(tmp_path):
    paths = RunPaths.for_run("EXP-20260101-001",
                             runs_root=str(tmp_path / "runs"),
                             results_root=str(tmp_path / "results"))
    paths.create()
    return paths


def write_processed(run_paths):
    payload = metric_payload()
    (run_paths.processed_dir / "metrics_overall.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


class TestLoadProcessed:
    def test_missing_file_raises_clear_error(self, tmp_path):
        with pytest.raises(FileNotFoundError) as exc:
            load_processed(str(tmp_path))
        assert "metrics_overall.json" in str(exc.value)

    def test_missing_field_raises(self, run_paths):
        (run_paths.processed_dir / "metrics_overall.json").write_text(
            json.dumps({"run_id": "x"}))
        with pytest.raises(ValueError):
            load_processed(str(run_paths.processed_dir))

    def test_load_returns_typed_results(self, run_paths):
        write_processed(run_paths)
        results = load_processed(str(run_paths.processed_dir))
        assert results.run_id == "EXP-20260101-001"
        assert results.bm25.name == "bm25"
        assert results.dependency_rag.recall == pytest.approx(0.4)


class TestTables:
    def test_all_tables_written(self, run_paths):
        write_processed(run_paths)
        results = load_processed(str(run_paths.processed_dir))
        written = build_all_tables(run_paths, results)
        names = [path.name for path in written]
        for expected in ["overall_metrics.csv", "per_query.csv", "dependency_metrics.csv",
                         "category_metrics.csv", "difficulty_metrics.csv",
                         "explicit_vs_implicit.csv", "error_classifications.csv"]:
            assert expected in names
            assert (run_paths.tables_dir / expected).exists()
            sidecar = run_paths.tables_dir / (expected.replace(".csv", "") + ".evidence.json")
            assert sidecar.exists()

    def test_tables_are_traceable(self, run_paths):
        write_processed(run_paths)
        results = load_processed(str(run_paths.processed_dir))
        build_all_tables(run_paths, results)
        sidecar = run_paths.tables_dir / "overall_metrics.evidence.json"
        content = json.loads(sidecar.read_text())
        assert "generated_from" in content
        assert content["generated_from"] == "experiments/runs/EXP-20260101-001/raw"

    def test_per_query_table_matches_payload_rows(self, run_paths):
        # per_query.csv must be populated from the processed payload (never
        # header-only) and preserve the payload's canonical row order.
        write_processed(run_paths)
        results = load_processed(str(run_paths.processed_dir))
        build_all_tables(run_paths, results)
        with open(run_paths.tables_dir / "per_query.csv") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == 2
        assert [row["query_id"] for row in rows] == ["Q-02", "Q-01"]
        assert float(rows[0]["bm25_precision@5"]) == pytest.approx(0.4)
        assert float(rows[0]["rag_precision@5"]) == pytest.approx(0.4)
        assert float(rows[0]["bm25_recall@5"]) == pytest.approx(0.5)
        assert float(rows[1]["bm25_mrr"]) == pytest.approx(0.2)
        assert float(rows[1]["rag_mrr"]) == pytest.approx(0.2)


class TestFigures:
    def test_figures_are_written(self, run_paths):
        pytest.importorskip("matplotlib")
        write_processed(run_paths)
        results = load_processed(str(run_paths.processed_dir))
        written = build_all_figures(run_paths, results)
        assert written  # at least one figure drawn
        for path in written:
            assert path.exists()
            assert path.suffix == ".png"


class TestReport:
    def test_report_contains_measured_sections(self, run_paths):
        write_processed(run_paths)
        results = load_processed(str(run_paths.processed_dir))
        path = build_report(run_paths, results)
        text = path.read_text()
        assert "Thesis Interpretation Inputs" in text
        assert "REQUIRE_MANUAL_REVIEW" in text
        assert "Precision@5" in text
        assert "0.6000" in text  # rag mean precision from payload

    def test_report_does_not_fabricate_conclusions(self, run_paths):
        write_processed(run_paths)
        results = load_processed(str(run_paths.processed_dir))
        path = build_report(run_paths, results)
        text = path.read_text()
        lower = text.lower()
        for banned in ["rag outperforms", "bm25 outperforms", "our results prove",
                       "conclusion:"]:
            assert banned not in lower
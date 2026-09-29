"""Single source of truth for a run: everything is validated up-front.

The runner calls load_experiment_inputs() once. It loads and validates the
frozen corpus units, the benchmark ground truth, the three frozen config files,
the frozen prompt hash, and proposes the run/result directory layout. Every
later step consumes this object, so a run cannot assemble its inputs
inconsistently (e.g. five-top for one system and six for another).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from src.benchmark.query_spec import SLOTS
from src.benchmark.validate_ground_truth import validate_ground_truth
from src.bm25.retriever import BM25Config
from src.data_generation.render_v1 import render_corpus
from src.data_generation.v1_full import build_final_corpus
from src.embeddings.generate import EmbeddingConfig
from src.evaluation.ground_truth import GroundTruthTable, derive_ground_truth, verify_agreement_with_export
from src.rag.citations import supplied_citation_ids
from src.rag.generator import RAGConfig, verify_frozen_prompt
from src.retrieval.units import RetrievalUnitSet, load_frozen_units

EVIDENCE_WORKBOOK = "data/exports/practicum_dataset_evidence.xlsx"


@dataclass(frozen=True)
class BenchmarkConfig:
    """The frozen per-query benchmark facts needed by a run."""

    query_ids: tuple[str, ...]
    query_texts: dict[str, str]
    # number of queries whose resolution yields >= 1 relevant document
    n_queries: int


def load_benchmark(ground_truth: GroundTruthTable) -> BenchmarkConfig:
    query_ids: list[str] = []
    query_texts: dict[str, str] = {}
    for slot in SLOTS:
        query_ids.append(slot.query_id)
        query_texts[slot.query_id] = slot.query_text
    return BenchmarkConfig(
        query_ids=tuple(query_ids),
        query_texts=query_texts,
        n_queries=len(query_ids),
    )


@dataclass(frozen=True)
class ExperimentInputs:
    model: object
    units: RetrievalUnitSet
    report: object
    ground_truth: GroundTruthTable
    benchmark: BenchmarkConfig
    bm25_config: BM25Config
    embedding_config: EmbeddingConfig
    rag_config: RAGConfig
    prompt_sha256: str
    agreement: dict
    run_id: str
    artifact_hashes: dict[str, str] = field(default_factory=dict)

    def query_text(self, query_id: str) -> str:
        return self.benchmark.query_texts[query_id]


def file_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact_hashes() -> dict[str, str]:
    """Frozen files whose hashes appear in run metadata for traceability."""
    paths = [
        "experiments/configs/bm25_config.json",
        "experiments/configs/embedding_config.json",
        "experiments/configs/rag_config.json",
        "experiments/configs/rag_prompt.txt",
        "data/corpus/v1/chunks/chunks.json",
        EVIDENCE_WORKBOOK,
    ]
    return {path: file_sha256(path) for path in paths}


def next_run_id(runs_root: str = "experiments/runs") -> str:
    """EXP-YYYYMMDD-NNN with NNN next available; creates nothing.

    AGENTS.md §5 defines the experiment id format. NNN counts existing run
    directories in experiments/runs (001, 002, ...).
    """
    from datetime import date

    root = Path(runs_root)
    root.mkdir(parents=True, exist_ok=True)
    prefix = f"EXP-{date.today():%Y%m%d}"
    existing = [p.name for p in root.iterdir() if p.is_dir() and p.name.startswith(prefix)]
    numbers = [int(name[len(prefix) + 1:]) for name in existing
               if name[len(prefix) + 1:].isdigit()]
    next_number = (max(numbers) + 1) if numbers else 1
    return f"{prefix}-{next_number:03d}"


def load_experiment_inputs(run_id: str | None = None) -> ExperimentInputs:
    """Assemble and validate everything a run needs.

    Raises on any frozen-file drift (prompt hash, ground-truth/chunk agreement,
    config parse). No API calls are made here.
    """
    verify_frozen_prompt()

    model = build_final_corpus()
    documents = render_corpus(model)
    report = validate_ground_truth(model=model, documents=documents, against_final=True)
    if not report.freezable:
        raise ValueError("ground-truth gate did not freeze; refusing to prepare a run")

    units = load_frozen_units()
    ground_truth = derive_ground_truth(units, report)
    agreement = verify_agreement_with_export(units, report, EVIDENCE_WORKBOOK)

    bm25_config = BM25Config.load()
    embedding_config = EmbeddingConfig.load()
    rag_config = RAGConfig.load()

    if bm25_config.top_k != rag_config.top_k:
        raise ValueError(
            f"bm25 top_k {bm25_config.top_k} != rag top_k {rag_config.top_k}; "
            "systems must rank the same k"
        )

    benchmark = load_benchmark(ground_truth)
    run_id = run_id or next_run_id()

    return ExperimentInputs(
        model=model,
        units=units,
        report=report,
        ground_truth=ground_truth,
        benchmark=benchmark,
        bm25_config=bm25_config,
        embedding_config=embedding_config,
        rag_config=rag_config,
        prompt_sha256=file_sha256("experiments/configs/rag_prompt.txt"),
        agreement=agreement,
        run_id=run_id,
        artifact_hashes=artifact_hashes(),
    )
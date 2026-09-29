"""Retrieval metrics: the frozen @5 measurements from docs/evaluation_metrics.md.

D-009 defines, at cutoff k=5:
  - Precision@5 = |retrieved ∩ relevant| / |retrieved|   (denominator = actually
    returned; a run whose top-5 comes up short uses the number actually returned,
    so precision can only be hurt by shortfall, never inflated)
  - Recall@5 = |retrieved ∩ relevant| / |relevant|
  - MRR = 1 / rank of the first relevant chunk, else 0

Queries with zero relevant chunks ("all-negative") are not valid benchmark rows:
per D-009 they abort the run rather than being scored as vacuous 1.0. Every one
of the frozen 32 queries resolves >= 1 relevant document, so this only guards
against a corrupted ground truth, and it is enforced here so a run cannot
silently include such a query.

One macro number per system over the full 32-query set, computed per query first
(then averaged), so a query with 1 relevant item cannot dominate one with 9.
Failed queries are kept in the denominator and score exactly 0.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.benchmark.query_spec import SLOTS, CATEGORY_LABEL


class ZeroRelevantError(ValueError):
    """Raised when a query has no relevant chunks; D-009 aborts on these."""


@dataclass(frozen=True)
class QueryRetrieval:
    query_id: str
    category: str
    difficulty: str
    retrieved_chunk_ids: tuple[str, ...]          # in rank order
    relevant_chunk_ids: frozenset[str]
    is_dependency_query: bool
    dependency_explicitness: str
    failed: bool = False                          # D-009: failed runs score exactly 0
    failure_reason: str = ""

    def precision_at_5(self) -> float:
        if self.failed:
            return 0.0
        if not self.retrieved_chunk_ids:
            return 0.0
        hits = sum(1 for cid in self.retrieved_chunk_ids if cid in self.relevant_chunk_ids)
        return hits / len(self.retrieved_chunk_ids)

    def recall_at_5(self) -> float:
        if self.failed:
            return 0.0
        if not self.relevant_chunk_ids:
            raise ZeroRelevantError(
                f"{self.query_id} has no relevant chunks; D-009 aborts on all-negative queries"
            )
        hits = sum(1 for cid in self.retrieved_chunk_ids if cid in self.relevant_chunk_ids)
        return hits / len(self.relevant_chunk_ids)

    def reciprocal_rank(self) -> float:
        if self.failed:
            return 0.0
        for rank, cid in enumerate(self.retrieved_chunk_ids, start=1):
            if cid in self.relevant_chunk_ids:
                return 1.0 / rank
        return 0.0


def build_query_retrievals(retrieved_by_query: dict[str, list[str]], ground_truth) -> list[QueryRetrieval]:
    """Pack raw retrieval output + derived ground truth into scored rows.

    retrieved_by_query: {query_id: [chunk_id in rank order]}.
    ground_truth: GroundTruthTable from src/evaluation/ground_truth.
    Rows follow the frozen SLOTS order (slot ascending).
    """
    entries = ground_truth.entries
    rows: list[QueryRetrieval] = []
    for slot in sorted(SLOTS, key=lambda s: s.slot):
        gt = entries[slot.query_id]
        rows.append(
            QueryRetrieval(
                query_id=slot.query_id,
                category=CATEGORY_LABEL[slot.category],
                difficulty=slot.difficulty,
                retrieved_chunk_ids=tuple(retrieved_by_query.get(slot.query_id, [])),
                relevant_chunk_ids=frozenset(gt.relevant_chunk_ids),
                is_dependency_query=gt.is_dependency_query,
                dependency_explicitness=gt.dependency_explicitness,
            )
        )
    return rows


@dataclass(frozen=True)
class AggregatedRetrieval:
    system: str
    n_queries: int
    n_failed: int
    mean_precision: float
    mean_recall: float
    mean_mrr: float
    precision_by_category: dict[str, float]
    recall_by_category: dict[str, float]
    mrr_by_category: dict[str, float]
    precision_by_difficulty: dict[str, float]
    recall_by_difficulty: dict[str, float]
    precision_explicit: float
    recall_explicit: float
    precision_implicit: float
    recall_implicit: float
    per_query: list[dict]

    def as_dict(self) -> dict:
        return {
            "system": self.system,
            "n_queries": self.n_queries,
            "n_failed": self.n_failed,
            "mean_precision": self.mean_precision,
            "mean_recall": self.mean_recall,
            "mean_mrr": self.mean_mrr,
            "precision_by_category": self.precision_by_category,
            "recall_by_category": self.recall_by_category,
            "mrr_by_category": self.mrr_by_category,
            "precision_by_difficulty": self.precision_by_difficulty,
            "recall_by_difficulty": self.recall_by_difficulty,
            "precision_explicit": self.precision_explicit,
            "recall_explicit": self.recall_explicit,
            "precision_implicit": self.precision_implicit,
            "recall_implicit": self.recall_implicit,
        }


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _group_mean(rows: list[QueryRetrieval], key: callable) -> dict[str, float]:
    grouped: dict[str, list[float]] = {}
    for row in rows:
        grouped.setdefault(str(key(row)), []).append(row.precision_at_5())
    return {label: _mean(values) for label, values in grouped.items()}


def score_run(system: str, rows: list[QueryRetrieval]) -> AggregatedRetrieval:
    """Compute the macro metrics over the full query set.

    All 32 rows take part in the averages (failed rows contribute 0.0). Zero
    relevant rows are rejected by recall_at_5 before any average can be taken.
    """
    precisions = [row.precision_at_5() for row in rows]
    recalls = [row.recall_at_5() for row in rows]
    mrrs = [row.reciprocal_rank() for row in rows]

    category_precision = _group_mean(rows, lambda r: r.category)
    category_recall = {label: _mean([r.recall_at_5() for r in rows if r.category == label])
                       for label in set(r.category for r in rows)}
    category_mrr = {label: _mean([r.reciprocal_rank() for r in rows if r.category == label])
                    for label in set(r.category for r in rows)}
    difficulty_precision = _group_mean(rows, lambda r: r.difficulty)
    difficulty_recall = {label: _mean([r.recall_at_5() for r in rows if r.difficulty == label])
                         for label in set(r.difficulty for r in rows)}

    explicit_rows = [r for r in rows if r.is_dependency_query and r.dependency_explicitness == "explicit"]
    implicit_rows = [r for r in rows if r.is_dependency_query and r.dependency_explicitness == "implicit"]

    per_query = [
        {
            "query_id": row.query_id,
            "category": row.category,
            "difficulty": row.difficulty,
            "retrieved_count": len(row.retrieved_chunk_ids),
            "relevant_count": len(row.relevant_chunk_ids),
            "precision@5": row.precision_at_5(),
            "recall@5": row.recall_at_5(),
            "mrr": row.reciprocal_rank(),
            "failed": row.failed,
        }
        for row in rows
    ]

    return AggregatedRetrieval(
        system=system,
        n_queries=len(rows),
        n_failed=sum(1 for r in rows if r.failed),
        mean_precision=_mean(precisions),
        mean_recall=_mean(recalls),
        mean_mrr=_mean(mrrs),
        precision_by_category=category_precision,
        recall_by_category=category_recall,
        mrr_by_category=category_mrr,
        precision_by_difficulty=difficulty_precision,
        recall_by_difficulty=difficulty_recall,
        precision_explicit=_mean([r.precision_at_5() for r in explicit_rows]),
        recall_explicit=_mean([r.recall_at_5() for r in explicit_rows]),
        precision_implicit=_mean([r.precision_at_5() for r in implicit_rows]),
        recall_implicit=_mean([r.recall_at_5() for r in implicit_rows]),
        per_query=per_query,
    )
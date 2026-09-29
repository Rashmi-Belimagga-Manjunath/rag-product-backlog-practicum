"""Runtime ground-truth resolution for evaluation.

The frozen ground truth lives in the benchmark: validate_ground_truth()
resolves each slot into a Resolution of document_ids. Evaluation relevant chunks
are then the frozen chunks of those documents, in frozen chunk_id_order. This
derivation is deterministic and mirrors exactly how the committed evidence
workbook builds its "QUERY GROUND TRUTH" sheet (export_evidence_workbook.py),
so the agreement check below proves the runtime harness uses the same labels the
student approved.

The module deliberately has no second source of ground truth. A chunk is
relevant if and only if its document is in the resolution for that query.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.benchmark.query_spec import SLOTS, Slot
from src.retrieval.units import RetrievalUnitSet


@dataclass(frozen=True)
class QueryGroundTruth:
    query_id: str
    slot: Slot
    relevant_document_ids: tuple[str, ...]
    relevant_chunk_ids: tuple[str, ...]
    expected_dependencies: tuple[str, ...]
    is_dependency_query: bool
    dependency_explicitness: str
    relevance_basis: str

    def as_dict(self) -> dict:
        return {
            "query_id": self.query_id,
            "relevant_document_ids": list(self.relevant_document_ids),
            "relevant_chunk_ids": list(self.relevant_chunk_ids),
            "expected_dependencies": list(self.expected_dependencies),
            "is_dependency_query": self.is_dependency_query,
            "dependency_explicitness": self.dependency_explicitness,
            "relevance_basis": self.relevance_basis,
        }


@dataclass(frozen=True)
class GroundTruthTable:
    entries: dict[str, QueryGroundTruth]

    def by_dependency(self) -> list[QueryGroundTruth]:
        return [entry for entry in self.entries.values() if entry.is_dependency_query]


def derive_ground_truth(units: RetrievalUnitSet, report) -> GroundTruthTable:
    """Derive per-query relevant sets from resolutions over the frozen units.

    report is the object returned by validate_ground_truth(..., against_final=True)
    which carries report.resolutions[query_id].document_ids. document_ids
    ordering is preserved from the resolution; chunk ids are in frozen
    chunk_id_order.
    """
    slot_by_id = {slot.query_id: slot for slot in SLOTS}
    entries: dict[str, QueryGroundTruth] = {}
    for slot in SLOTS:
        resolution = report.resolutions[slot.query_id]
        document_ids = tuple(resolution.document_ids)
        relevant = units.relevant_chunk_ids(list(document_ids))
        dependencies = tuple(resolution.expected_dependencies)
        entries[slot.query_id] = QueryGroundTruth(
            query_id=slot.query_id,
            slot=slot,
            relevant_document_ids=document_ids,
            relevant_chunk_ids=tuple(relevant),
            expected_dependencies=dependencies,
            is_dependency_query=bool(slot.dependency_explicitness),
            dependency_explicitness=slot.dependency_explicitness or "none",
            relevance_basis=resolution.relevance_basis,
        )
    return GroundTruthTable(entries=entries)


def load_export_query_ground_truth(workbook_path: str) -> dict[str, set[str]]:
    """Read the committed workbook's QUERY GROUND TRUTH sheet.

    Returns {query_id: set(relevant_chunk_id)} exactly as the committed evidence
    exports them. Used only to prove the runtime derivation agrees.
    """
    from openpyxl import load_workbook

    wb = load_workbook(workbook_path, read_only=True, data_only=True)
    sheet = wb["QUERY GROUND TRUTH"]
    rows = sheet.iter_rows(values_only=True)
    header = next(rows)
    qid_col = header.index("query_id")
    chunk_col = header.index("relevant_chunk_id")
    result: dict[str, set[str]] = {}
    for row in rows:
        if not row or row[qid_col] is None:
            continue
        query_id = str(row[qid_col])
        chunk_id = str(row[chunk_col])
        result.setdefault(query_id, set()).add(chunk_id)
    wb.close()
    return result


def verify_agreement_with_export(units: RetrievalUnitSet, report, workbook_path: str) -> dict:
    """Assert the runtime derivation matches the committed evidence workbook.

    Checks, per query:
      1. the set of relevant chunk ids is identical to the committed workbook;
      2. every relevant document id appears in the workbook rows for that query;
      3. no chunk id in the workbook is absent from the frozen units.

    Returns a report dict. Raises AssertionError with the first mismatch so a
    drift in ground-truth handling is caught before any experiment executes.
    """
    export_gt = load_export_query_ground_truth(workbook_path)
    runtime = derive_ground_truth(units, report)
    by_query_id = {u.query_id: u for u in runtime.entries.values()}

    mismatch: list[str] = []
    for query_id, runtime_entry in by_query_id.items():
        runtime_ids = set(runtime_entry.relevant_chunk_ids)
        export_ids = export_gt.get(query_id, set())
        if runtime_ids != export_ids:
            mismatch.append(
                f"{query_id}: runtime {len(runtime_ids)} chunks, "
                f"workbook {len(export_ids)} chunks; "
                f"diff runtime-only={sorted(runtime_ids - export_ids)[:5]}, "
                f"workbook-only={sorted(export_ids - runtime_ids)[:5]}"
            )

    known = set(units.by_id)
    for query_id, ids in export_gt.items():
        unknown = sorted(ids - known)
        if unknown:
            mismatch.append(f"{query_id}: workbook references unknown ids {unknown[:5]}")

    if mismatch:
        raise AssertionError(
            "runtime ground truth disagrees with committed evidence workbook:\n"
            + "\n".join(mismatch)
        )

    total_rows = sum(len(ids) for ids in export_gt.values())
    return {
        "queries_checked": len(by_query_id),
        "workbook_rows": total_rows,
        "agreement": "PASS",
    }
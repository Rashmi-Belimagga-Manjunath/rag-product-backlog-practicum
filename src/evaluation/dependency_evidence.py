"""Derive the predicted dependency set P(q) for a retrieval run.

D-009 §5 defines dependency accuracy at the retrieval layer for both systems and
scores (predicted, expected, failed) through score_dependency_run(). The
expected set E(q) is the benchmark resolution's expected_dependencies. The
predicted set is NOT reported by either system as text — it must be derived from
the retrieved evidence, and the derivation is an explicit operationalisation of
the frozen spec (disclosed to the supervisor at the checkpoint, per D-009's
'implementation issue' guidance).

Rule (documented, auditable, identical for BM25 and RAG):

For each dependency d with endpoints (from_id, to_id) and explicitness e:

  * explicit e: d is asserted by retrieved evidence iff the declaring document
    was retrieved — i.e. some retrieved unit has source_entity_id == from_id and
    to_id in its referenced entity set. A single chunk of the from-entity's own
    document carries the statement, so one declaration suffices.
  * implicit e: no document states d; a reader must combine documents that
    mention each endpoint. d is therefore asserted iff at least one retrieved
    unit covers from_id AND at least one retrieved unit covers to_id (the two
    can be the same unit, but are usually different documents).

P(q) is then every dependency asserted by the retrieved top-k evidence.
Precision therefore penalises off-topic dependency assertions (D-009's all-
negative predictor case), and recall depends on the evidence for E(q) actually
being retrieved.

Nothing in this derivation consults the ground truth: it uses only the retrieved
chunk set and the frozen model's declared dependency structure.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.evaluation.ground_truth import QueryGroundTruth
from src.retrieval.units import RetrievalUnitSet


@dataclass(frozen=True)
class DependencyIndex:
    """Frozen model dependency structure: dep_id -> (from_id, to_id, explicitness)."""

    by_id: dict[str, tuple[str, str, str]]


def build_dependency_index(model) -> DependencyIndex:
    entries: dict[str, tuple[str, str, str]] = {}
    for dep in model.dependencies:
        entries[dep.dependency_id] = (dep.from_id, dep.to_id, dep.explicitness)
    return DependencyIndex(by_id=entries)


def _retrieved_covers(retrieved_units) -> dict[str, set[str]]:
    """chunk_id -> set of entities the unit is provably about (source + references)."""
    return {unit.chunk_id: unit.entity_cover() for unit in retrieved_units}


def dependency_asserted(
    dep_id: str,
    metadata: tuple[str, str, str],
    covers: dict[str, set[str]],
) -> bool:
    from_id, to_id, explicitness = metadata
    if explicitness == "explicit":
        for cover in covers.values():
            if from_id in cover and to_id in cover:
                # explicit deps are stated by the from-entity's own document;
                # source_entity_id == from_id guarantees the declaring document.
                # A unit whose cover references both endpoints is that document.
                return True
        return False
    from_covered = any(from_id in cover for cover in covers.values())
    to_covered = any(to_id in cover for cover in covers.values())
    return from_covered and to_covered


def predicted_dependencies(
    ground_truth: QueryGroundTruth,
    retrieved_chunk_ids: list[str],
    units: RetrievalUnitSet,
    dep_index: DependencyIndex,
) -> set[str]:
    """The system's asserted dependency set, derived only from retrieved evidence."""
    retrieved_units = [units.by_id[cid] for cid in retrieved_chunk_ids if cid in units.by_id]
    covers = _retrieved_covers(retrieved_units)
    predicted: set[str] = set()
    for dep_id, metadata in dep_index.by_id.items():
        if dependency_asserted(dep_id, metadata, covers):
            predicted.add(dep_id)
    return predicted


def dependency_run_inputs(
    ground_truth_table,
    retrieved_by_query: dict[str, list[str]],
    units: RetrievalUnitSet,
    dep_index: DependencyIndex,
) -> list[tuple[set[str], set[str], bool]]:
    """Rows for score_dependency_run(): (predicted, expected, failed).

    Rows follow SLOTS order. failed is False for every real run (the runner
    records crashes separately); the field exists so score_dependency_run can be
    reused without change.
    """
    rows: list[tuple[set[str], set[str], bool]] = []
    for entry in ground_truth_table.entries.values():
        expected = set(entry.expected_dependencies)
        retrieved = retrieved_by_query.get(entry.query_id, [])
        predicted = predicted_dependencies(entry, retrieved, units, dep_index)
        rows.append((predicted, expected, False))
    return rows
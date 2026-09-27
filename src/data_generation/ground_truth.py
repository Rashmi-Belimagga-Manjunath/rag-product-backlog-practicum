"""
Ground-truth derivation FROM THE SOURCE MODEL.

This module is the reason the source model exists. Every evaluation label is a lookup
against structured data, never an inference from rendered prose.

The chain, for any query:

    query -> target entity in the model
          -> documents whose source_entity_id is that entity      (provenance)
          -> chunks whose parent document is one of those          (provenance)

Nothing in this file reads document text. If a label required reading the rendered
prose to produce, it would be a guess wearing a label, and it would not be independent
of the thing being graded.

Every function here returns a label plus the dependency/answer elements needed for
dependency-accuracy scoring, so retrieval quality and answer quality stay separately
scorable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .source_model import SourceModel
from .render import Document


@dataclass
class GroundTruth:
    """
    Ground truth for one query.

    `relevant_document_ids` and `relevant_chunk_ids` are separate because retrieval is
    scored at both levels: a system can surface the right document but the wrong part
    of it, and that is a different failure from missing the document entirely.
    """
    query_id: str
    query: str
    query_type: str
    lexical_difficulty: str
    target_entity_id: str

    relevant_document_ids: list[str] = field(default_factory=list)
    relevant_chunk_ids: list[str] = field(default_factory=list)
    expected_dependencies: list[str] = field(default_factory=list)
    expected_answer_elements: list[str] = field(default_factory=list)

    # Documents that are topically adjacent but NOT relevant. Used to check that a
    # system is not simply returning everything, and to report on distractor behaviour.
    distractor_document_ids: list[str] = field(default_factory=list)

    # Set when the query targets a superseded document, so results can be reported
    # separately on whether a system surfaces stale content.
    superseded_document_ids: list[str] = field(default_factory=list)


def documents_for_entity(documents: list[Document], entity_id: str) -> list[str]:
    """
    Which documents carry this entity, by provenance.

    Note what this does NOT do: it does not search for the entity's name in document
    text. Documents reference entities by ID, and chunking must propagate that
    reference. If it ever becomes necessary to search text to answer this function, the
    provenance chain has been broken somewhere and needs fixing, not working around.
    """
    return [d.document_id for d in documents if d.source_entity_id == entity_id]


def documents_referencing(documents: list[Document], entity_id: str) -> list[str]:
    """Documents that mention an entity without being primarily about it. Often the
    distractors, and often where a dependency is stated indirectly."""
    return [
        d.document_id
        for d in documents
        if entity_id in d.referenced_entity_ids and d.source_entity_id != entity_id
    ]


def expected_dependencies_for(
    model: SourceModel, entity_id: str, include_implicit: bool = True
) -> list[str]:
    """
    The dependency IDs a correct answer about this entity should surface.

    `include_implicit` exists because explicit and implicit dependencies are different
    kinds of finding. An explicit dependency is written in a document, so keyword search
    can reach it. An implicit one is not written anywhere, so it is only recoverable by
    reasoning across documents. Keeping them separable is what allows the write-up to
    say *where* semantic retrieval actually helps, instead of only whether it helped.
    """
    return [
        d.dependency_id
        for d in model.dependencies_for(entity_id)
        if include_implicit or d.is_explicit_in_docs
    ]


def build_ground_truth(
    query_id: str,
    query: str,
    query_type: str,
    lexical_difficulty: str,
    target_entity_id: str,
    model: SourceModel,
    documents: list[Document],
    expected_answer_elements: Optional[list[str]] = None,
    include_referenced_as_relevant: bool = False,
) -> GroundTruth:
    """
    Derive the full ground-truth record for one query from the model.

    `include_referenced_as_relevant` controls whether documents that merely *mention*
    the target count as relevant. For a dependency-identification query, they usually
    do, because the dependency is often stated in a neighbouring document rather than
    the subject's own. For a feature-context query they usually do not. This is a
    judgement call per query type, and it is made here explicitly rather than buried.
    """
    primary = documents_for_entity(documents, target_entity_id)
    secondary = documents_referencing(documents, target_entity_id)

    relevant = list(primary)
    if include_referenced_as_relevant:
        relevant += [d for d in secondary if d not in relevant]

    superseding = [d for d in documents if d.superseded_by_document_id]

    superseded_for_target = []
    for doc in documents:
        if doc.source_entity_id == target_entity_id and doc.superseded_by_document_id:
            superseded_for_target.append(doc.document_id)

    return GroundTruth(
        query_id=query_id,
        query=query,
        query_type=query_type,
        lexical_difficulty=lexical_difficulty,
        target_entity_id=target_entity_id,
        relevant_document_ids=relevant,
        # Chunk IDs are filled in after chunking, by propagating document provenance.
        # Left empty here deliberately — see ground_truth.attach_chunk_ids().
        relevant_chunk_ids=[],
        expected_dependencies=expected_dependencies_for(model, target_entity_id),
        expected_answer_elements=expected_answer_elements or [],
        distractor_document_ids=[d for d in secondary if d not in relevant],
        superseded_document_ids=superseded_for_target,
    )


def attach_chunk_ids(
    ground_truth: GroundTruth,
    document_to_chunk_ids: dict[str, list[str]],
) -> GroundTruth:
    """
    Populate `relevant_chunk_ids` once chunking has run.

    This is a pure lookup: a chunk is relevant iff its parent document is relevant.
    We never re-examine chunk text, because relevance was already decided at document
    level from the model. Deciding it twice, on different granularity, is how ground
    truth quietly drifts out of alignment with the corpus it describes.
    """
    chunks: list[str] = []
    for document_id in ground_truth.relevant_document_ids:
        chunks.extend(document_to_chunk_ids.get(document_id, []))
    ground_truth.relevant_chunk_ids = chunks
    return ground_truth


def verify_traceable(
    ground_truth: GroundTruth,
    model: SourceModel,
    documents: list[Document],
) -> list[str]:
    """
    Self-check: confirm every label traces back to the model in one hop.

    Returns a list of problems; empty means the record is sound. This runs as a test
    rather than being trusted, because a silently-broken provenance chain produces
    labels that look plausible and are wrong — which is worse than no labels at all,
    since they would be trusted.
    """
    problems: list[str] = []
    valid_ids = {d.document_id for d in documents}

    for document_id in ground_truth.relevant_document_ids:
        if document_id not in valid_ids:
            problems.append(f"{ground_truth.query_id}: unknown document {document_id}")

    if ground_truth.target_entity_id:
        known_entity = any(
            ground_truth.target_entity_id in {
                getattr(item, attr, None)
                for attr in ("feature_id", "pbi_id", "requirement_id", "component_id",
                             "ticket_id", "decision_id", "note_id", "runbook_id")
            }
            for collection in (
                model.features, model.pbis, model.requirements, model.components,
                model.tickets, model.decisions, model.meeting_notes, model.runbooks,
            )
            for item in collection
        )
        if not known_entity:
            problems.append(
                f"{ground_truth.query_id}: target entity "
                f"{ground_truth.target_entity_id} is not in the model"
            )

    known_dependencies = {d.dependency_id for d in model.dependencies}
    for dependency_id in ground_truth.expected_dependencies:
        if dependency_id not in known_dependencies:
            problems.append(
                f"{ground_truth.query_id}: unknown dependency {dependency_id}"
            )

    return problems

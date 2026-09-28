"""
Ground-truth schema and derivation.

INDEPENDENCE FROM THE SYSTEMS UNDER TEST
----------------------------------------
Every label here is read off the SourceModel. Nothing in this module imports, calls, or
knows about BM25, the vector store, or the LLM. Deriving a label from a system's output
would make the label a function of the thing being graded, and the comparison would be
circular. Per the approved decision, ground truth is never finalised using RAG or an LLM
after the systems have been run.

Each field required by the specification is present and named explicitly, so a missing
label is a visible absence rather than a silent default.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Literal, Optional

from ..data_generation.source_model import (
    doc_ids_from,
    DependencyExplicitness,
    LexicalDifficulty,
    QueryType,
    SourceModel,
)

# Stopwords for the difficulty measure. Fixed set, frozen with the query specification.
# Changing this list after seeing results would change the difficulty bands.
STOPWORDS = frozenset("""
a an the is are was were be been being of to in on at for with and or but if than then
so as by from it its this that these those which what who whom how why when where do does
did can could should would will shall may might i we they he she you not no any all more
most some such only own same too very s t just now have has had having there their them
""".split())

# Query identity. Q-SUP-1..3 are the approved version-reasoning queries; they are NOT
# additional to the 32, they occupy slots within information_retrieval and
# feature_context.
VersionQueryKind = Literal["recency", "provenance", "current_value"]


@dataclass
class QuerySpec:
    """A query slot, as approved. Wording is filled in at query-generation time."""
    query_id: str
    slot: int
    category: QueryType
    target_entity_id: str
    target_document_ids: list[str]           # documents that must be retrieved
    target_dependency_ids: list[str] = field(default_factory=list)
    dependency_explicitness: Optional[DependencyExplicitness] = None
    intended_difficulty: LexicalDifficulty = "easy"
    involves_version: bool = False
    version_query_kind: Optional[VersionQueryKind] = None
    distractors: list[str] = field(default_factory=list)   # document IDs
    notes: str = ""


@dataclass
class GroundTruth:
    """
    One query's full label set. Field names follow the approved specification exactly.
    """
    query_id: str
    query: str
    category: QueryType
    difficulty: LexicalDifficulty
    measured_overlap: float
    dependency_type: Optional[DependencyExplicitness]      # None if not dependency-related
    relevant_document_ids: list[str]
    relevant_chunk_ids: list[str] = field(default_factory=list)
    expected_dependencies: list[str] = field(default_factory=list)
    expected_answer_elements: list[str] = field(default_factory=list)
    relevance_basis: Literal["current", "superseded", "both"] = "current"
    distractor_document_ids: list[str] = field(default_factory=list)
    rationale: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Difficulty measure
# ---------------------------------------------------------------------------

def content_words(text: str) -> set[str]:
    """Lowercased, stopword-removed, length > 2. Frozen alongside the query set."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def lexical_overlap(query: str, relevant_text: str) -> float:
    """
    Benchmark-construction measure of lexical alignment between a query and the
    information that answers it.

    THIS IS NOT A PSYCHOLOGICAL OR COGNITIVE MEASURE OF TASK DIFFICULTY. "hard" means
    only that the query shares little vocabulary with its target. The measure exists to
    create controlled variation in lexical alignment; it says nothing about how demanding
    a question is for a person or a model.
    """
    q = content_words(query)
    if not q:
        return 0.0
    return len(q & content_words(relevant_text)) / len(q)


def band_for(overlap: float) -> LexicalDifficulty:
    """Bands frozen before any system is evaluated."""
    if overlap >= 0.40:
        return "easy"
    if overlap >= 0.20:
        return "moderate"
    return "hard"


# ---------------------------------------------------------------------------
# Derivation
# ---------------------------------------------------------------------------

def derive_ground_truth(spec: QuerySpec, query_text: str, model: SourceModel,
                        documents, chunks) -> GroundTruth:
    """
    Build the label set by LOOKUP on the model. No text analysis of rendered prose.
    """
    relevant_texts = [
        d.body for d in documents if d.document_id in spec.target_document_ids
    ]
    if not relevant_texts:
        raise KeyError(
            f"{spec.query_id}: no rendered document matches "
            f"{spec.target_document_ids}. The query spec is wrong, or the corpus does not "
            f"contain the target. Do not fall back to a best guess."
        )
    overlap = lexical_overlap(query_text, "\n".join(relevant_texts))

    # Chunk-level relevance by provenance propagation, never by re-reading chunk text.
    relevant_chunks = [
        c.chunk_id for c in chunks
        if c.document_id in spec.target_document_ids
    ]

    # Expected dependencies resolved from the model.
    expected = []
    answer_elements = []
    for dependency_id in spec.target_dependency_ids:
        dependency = next(
            (d for d in model.dependencies if d.dependency_id == dependency_id), None
        )
        if dependency is None:
            raise KeyError(
                f"{spec.query_id}: dependency '{dependency_id}' is not in the source "
                f"model. Ground truth must be derivable; a missing dependency is a data "
                f"error, not something to guess."
            )
        expected.append(dependency_id)
        answer_elements.append(
            f"{dependency.to_type} {dependency.to_id} "
            f"({dependency.dependency_type}, {dependency.explicitness})"
        )

    # What the target entity's own documents are allowed to be treated as.
    target_documents = [d for d in documents if d.document_id in spec.target_document_ids]
    versions = {d.version_status for d in target_documents}
    if versions == {"superseded"}:
        basis = "superseded"
    elif versions == {"current"}:
        basis = "current"
    else:
        basis = "both"

    return GroundTruth(
        query_id=spec.query_id,
        query=query_text,
        category=spec.category,
        difficulty=band_for(overlap),
        measured_overlap=round(overlap, 4),
        dependency_type=spec.dependency_explicitness,
        relevant_document_ids=list(spec.target_document_ids),
        relevant_chunk_ids=relevant_chunks,
        expected_dependencies=expected,
        expected_answer_elements=answer_elements,
        relevance_basis=basis,
        distractor_document_ids=list(spec.distractors),
        rationale=(
            f"Derived from the structured model. Target {spec.target_entity_id}; "
            f"documents {spec.target_document_ids} carry it via declared DocumentLinks. "
            f"Measured lexical overlap {overlap:.0%} -> {band_for(overlap)}."
        ),
    )


def verify_traceable(gt: GroundTruth, model: SourceModel) -> list[str]:
    """
    Confirm every label resolves in one hop against the model. Returns a list of problems;
    empty means traceable.
    """
    problems: list[str] = []
    known_documents = doc_ids_from(model)
    for dependency_id in gt.expected_dependencies:
        if not any(d.dependency_id == dependency_id for d in model.dependencies):
            problems.append(f"{gt.query_id}: dependency {dependency_id} not in model")
    for document_id in gt.relevant_document_ids:
        if document_id not in known_documents:
            problems.append(f"{gt.query_id}: document {document_id} not in corpus")
    if gt.dependency_type and not gt.expected_dependencies:
        problems.append(
            f"{gt.query_id}: labelled {gt.dependency_type} but expects no dependencies"
        )
    if gt.measured_overlap is not None and not 0.0 <= gt.measured_overlap <= 1.0:
        problems.append(f"{gt.query_id}: overlap {gt.measured_overlap} out of range")
    return problems

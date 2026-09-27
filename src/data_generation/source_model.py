"""
Structured source-of-truth model for the synthetic product-documentation corpus.

WHY THIS FILE EXISTS
--------------------
Ground-truth labels for the evaluation (relevant documents, relevant chunks, expected
dependencies) must be DERIVED FROM THIS MODEL, not by reading the rendered documents.

If labels were produced by reading generated prose, they would be the same kind of
artefact as the thing being graded, and the experiment would measure the generator
rather than retrieval. So the relationships are asserted here, in data, first. Documents
are rendered from this model afterwards. Queries are written against this model.
Ground truth is read straight off it.

Every entity has a stable, human-readable ID. Those IDs never change across runs, which
is what makes a result reproducible months later.

This file defines the schema only. It contains no data.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional
import json

# ---------------------------------------------------------------------------
# Controlled vocabularies
# ---------------------------------------------------------------------------
# These are closed sets on purpose. Free-text enums would let typos silently create
# categories that break the query/ground-truth joins later.

DocType = Literal[
    "prd",              # Product Requirements Document - long, formal, versioned
    "feature_spec",     # Technical specification of one feature
    "pbi",              # Product Backlog Item / user story - short, informal
    "ticket",           # Support ticket - customer language, symptom-oriented
    "decision_log",     # Records a decision and its reason
    "meeting_notes",    # Fragmentary, unlabelled, informal
    "runbook",          # Technical/operational documentation
]

FeatureStatus = Literal["discovered", "planned", "in_progress", "launched", "deprecated"]
PbiStatus = Literal["to_do", "in_progress", "in_review", "done"]

# Dependency types matter because they imply different difficulty.
#   blocks / depends_on -> an ordering constraint, usually findable
#   duplicates          -> near-identical scope, a classic source of wasted effort
#   conflicts_with      -> a genuine contradiction between two artefacts
#   informs             -> one document provides context for another
DependencyType = Literal[
    "blocks", "depends_on", "duplicates", "conflicts_with", "informs"
]

# Component types. Third-party components are included deliberately: dependencies the
# product team does not own are where a PM's context is most often missing.
ComponentType = Literal["service", "database", "queue", "third_party"]

# Documentation maturity. This is the field that operationalises CA2 section 3's
# design choice to contrast a formally-documented domain with an informal one.
DocumentationMaturity = Literal["formal", "informal"]

# Query categories, matching the task types named in CA1.
QueryType = Literal[
    "information_retrieval",
    "feature_context",
    "dependency_identification",
    "cross_document_reasoning",
    "conflict_identification",
    "backlog_analysis",
]

# Lexical difficulty. This is the experimental control described in DATA_DESIGN.md
# section 6. A query marked "hard" shares almost no vocabulary with its target document.
LexicalDifficulty = Literal["easy", "moderate", "hard"]


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

@dataclass
class Product:
    """A product whose documentation lives in this corpus."""
    product_id: str                      # e.g. "PROD-A"
    name: str
    domain: str
    documentation_maturity: DocumentationMaturity
    team_size: int
    # False means documents from this product may be superseded by newer versions
    # that remain in the repository. Real repositories are like this.
    maintains_version_history: bool = True


@dataclass
class Feature:
    """
    A product feature - the central entity queries will target.

    `formal_term` and `colloquial_terms` are the experimental control, not decoration.
    They let the same underlying concept appear under different vocabulary in different
    documents, and in yet another phrasing in the query. See DATA_DESIGN.md section 6.
    """
    feature_id: str                      # e.g. "FEAT-A-01"
    product_id: str
    name: str
    status: FeatureStatus
    priority: int                        # 1 = highest
    formal_term: str                     # precise technical vocabulary
    colloquial_terms: list[str]          # informal phrasings used in real prose
    summary: str                         # one-line factual description


@dataclass
class Requirement:
    """
    A PRD-level requirement. Rendered as a long, multi-section, versioned document.

    `is_normative` marks the document as authoritative when two documents disagree.
    This gives the corpus a real "which document wins" structure instead of leaving
    conflicts unresolvable.
    """
    requirement_id: str                  # e.g. "REQ-A-01"
    product_id: str
    title: str
    version: str
    author_role: str
    created_date: str                    # ISO date
    feature_ids: list[str]               # features this requirement governs
    is_normative: bool
    summary: str
    # Ordered section headings. Content is rendered per section, so section structure
    # is data, not a formatting decision buried in the renderer.
    sections: list[str]
    is_superseded: bool = False          # older version left in the repository
    supersedes_id: str = ""              # version lineage, so a stale doc is provably stale


@dataclass
class Ticket:
    """
    A support ticket. Rendered in customer language, symptom-oriented.

    Tickets exist so that the corpus contains the vocabulary a customer actually uses,
    which is typically far from the vocabulary in the PRD. This is one of the main
    sources of realistic lexical divergence.
    """
    ticket_id: str                       # e.g. "TKT-104"
    product_id: str
    feature_id: str
    related_component_id: str
    reported_symptom: str                # customer phrasing
    customer_segment: str
    severity: Literal["low", "medium", "high"]
    opened_date: str
    reporter_role: str


@dataclass
class DecisionRecord:
    """A recorded decision and the reason for it. Short and informal by nature."""
    decision_id: str                     # e.g. "DEC-03"
    product_id: str
    about_entity_id: str                 # feature / requirement / component
    decision: str
    rationale: str
    decided_date: str
    decided_by_role: str


@dataclass
class MeetingNote:
    """
    Fragmentary meeting notes.

    Modelled as structured bullet topics rather than free prose, so that even the
    messiest document type in the corpus still has every factual claim traceable to
    the model. Prose form comes from the renderer, not from invention.
    """
    note_id: str                         # e.g. "NOTE-07"
    product_id: str
    about_entity_ids: list[str]
    meeting_date: str
    attendees_role: list[str]
    topics: list[str]                    # ordered bullet topics


@dataclass
class Runbook:
    """Operational/technical documentation for a component."""
    runbook_id: str                      # e.g. "RBK-02"
    product_id: str
    component_id: str
    title: str
    steps: list[str]
    last_reviewed: str



@dataclass
class Pbi:
    """A Product Backlog Item / user story. Short, informal, often vague."""
    pbi_id: str                          # e.g. "PBI-A-014"
    product_id: str
    feature_id: str
    title: str
    description: str
    story_points: int
    status: PbiStatus
    created_date: str
    author_role: str
    formal_term: str
    colloquial_terms: list[str]


@dataclass
class TechnicalComponent:
    """A service, database, queue, or third-party dependency."""
    component_id: str                    # e.g. "COMP-07"
    name: str
    component_type: ComponentType
    owner_team: str
    notes: str = ""


@dataclass
class Dependency:
    """
    The core of the ground truth.

    `is_explicit_in_docs` is the distinction that makes a real finding possible:
      - explicit  -> some document states the relationship in words. Good keyword search
                     can find this.
      - implicit  -> the relationship follows from the model but no document states it.
                     Only semantic reasoning recovers it.
    Reporting the two separately is the most likely place a useful, honest result
    appears, because it says WHERE semantic retrieval actually pays off.
    """
    dependency_id: str                   # e.g. "DEP-031"
    from_type: Literal["feature", "pbi", "requirement", "component"]
    from_id: str
    to_type: Literal["feature", "pbi", "requirement", "component"]
    to_id: str
    dependency_type: DependencyType
    description: str
    is_explicit_in_docs: bool


@dataclass
class Conflict:
    """A genuine contradiction between two artefacts. Asserted by construction."""
    conflict_id: str                     # e.g. "CONF-04"
    product_id: str
    document_a_id: str
    document_b_id: str
    conflict_type: str                   # e.g. "incompatible_scope"
    description: str
    is_resolved: bool
    resolution_note: str = ""
    resolved_by_document_id: str = ""


@dataclass
class SourceModel:
    """The complete source of truth for one corpus version."""
    model_version: str                   # e.g. "v0-sample"
    seed: int
    created_date: str
    products: list[Product] = field(default_factory=list)
    features: list[Feature] = field(default_factory=list)
    requirements: list[Requirement] = field(default_factory=list)
    pbis: list[Pbi] = field(default_factory=list)
    components: list[TechnicalComponent] = field(default_factory=list)
    tickets: list[Ticket] = field(default_factory=list)
    decisions: list[DecisionRecord] = field(default_factory=list)
    meeting_notes: list[MeetingNote] = field(default_factory=list)
    runbooks: list[Runbook] = field(default_factory=list)
    dependencies: list[Dependency] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)

    # -- lookups -------------------------------------------------------------
    # These exist so that ground-truth derivation is a lookup, not a text-matching
    # exercise. If deriving a label required parsing prose, the label would not be
    # trustworthy.

    def get_feature(self, feature_id: str) -> Feature:
        return self._must_find(self.features, "feature_id", feature_id)

    def get_pbi(self, pbi_id: str) -> Pbi:
        return self._must_find(self.pbis, "pbi_id", pbi_id)

    def get_requirement(self, requirement_id: str) -> Requirement:
        return self._must_find(self.requirements, "requirement_id", requirement_id)

    def get_component(self, component_id: str) -> TechnicalComponent:
        return self._must_find(self.components, "component_id", component_id)

    def get_product(self, product_id: str) -> Product:
        return self._must_find(self.products, "product_id", product_id)


    def dependencies_for(self, entity_id: str) -> list[Dependency]:
        """Every dependency where this entity is either end. Used for dependency-accuracy
        ground truth."""
        return [
            d for d in self.dependencies
            if d.from_id == entity_id or d.to_id == entity_id
        ]

    def documents_for_entity(self, entity_id: str) -> list[str]:
        """Which rendered documents carry this entity. Populated after rendering, from
        document provenance - never by scanning document text."""
        return [
            doc.document_id
            for doc in getattr(self, "_rendered_documents", [])
            if doc.source_entity_id == entity_id
        ]

    @staticmethod
    def _must_find(items, attr, value):
        for item in items:
            if getattr(item, attr) == value:
                return item
        raise KeyError(
            f"No entity with {attr}='{value}'. This is a data error, not a runtime "
            f"condition to handle - fix the source model."
        )

    # -- serialisation -------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "model_version": self.model_version,
            "seed": self.seed,
            "created_date": self.created_date,
            "products": [asdict(p) for p in self.products],
            "features": [asdict(f) for f in self.features],
            "requirements": [asdict(r) for r in self.requirements],
            "pbis": [asdict(p) for p in self.pbis],
            "components": [asdict(c) for c in self.components],
            "tickets": [asdict(t) for t in self.tickets],
            "decisions": [asdict(d) for d in self.decisions],
            "meeting_notes": [asdict(m) for m in self.meeting_notes],
            "runbooks": [asdict(r) for r in self.runbooks],
            "dependencies": [asdict(d) for d in self.dependencies],
            "conflicts": [asdict(c) for c in self.conflicts],
        }

    def save(self, path) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.to_dict(), handle, indent=2, ensure_ascii=False)

"""
Structured source-of-truth model for the synthetic product-documentation corpus.

WHY THIS FILE EXISTS
--------------------
Ground-truth labels for the evaluation (relevant documents, relevant chunks, expected
dependencies) must be DERIVED FROM THIS MODEL, not by reading the rendered documents.

If labels were produced by reading generated prose, they would be the same kind of
artefact as the thing being graded, and the experiment would measure the generator rather
than retrieval. So the relationships are asserted here, in data, first. Documents are
rendered from this model afterwards. Queries are written against this model. Ground truth
is read straight off it.

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
    "component_doc",    # Architecture / technical component description
]

# Version lifecycle. `status` is explicit rather than inferred from dates, so that
# "which document is current" is answerable by a field lookup and not by inference.
VersionStatus = Literal["current", "superseded"]

FeatureStatus = Literal["discovered", "planned", "in_progress", "launched", "deprecated"]
PbiStatus = Literal["to_do", "in_progress", "in_review", "done"]

# Dependency types matter because they imply different difficulty.
#   blocks / depends_on -> an ordering constraint, usually findable
#   duplicates          -> near-identical scope, a classic source of wasted effort
#   conflicts_with      -> a genuine contradiction between two artefacts
#   informs             -> one document provides context for another
#   ordering            -> a stage/phase sequencing constraint (D-013 amendment).
#                          Represents the "order" the Q-11/Q-14/Q-20 selectors match on.
DependencyType = Literal[
    "blocks", "depends_on", "duplicates", "conflicts_with", "informs", "ordering"
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
#
# NOTE ON WORDING: "hard" refers ONLY to low lexical alignment between the query and its
# target information. It is a benchmark-construction label, not a validated psychological
# or cognitive measure of how demanding a task is. See docs/query_specification.md.
LexicalDifficulty = Literal["easy", "moderate", "hard"]

# Dependency explicitness, per approved decision Q5.
#
# This describes what the DOCUMENTS say, never what the model knows. An implicit
# dependency is always explicitly encoded here, so its ground truth is derivable.
# "Implicit" must never be used to license common-sense reasoning that a human then
# judges to be reasonable - that would make the label subjective.
DependencyExplicitness = Literal["explicit", "implicit"]

# Document link types. `contextualises` is what makes distractors declared rather than
# hoped-for: a D1/D2 distractor is a contextualises link to a nearby entity that is
# objectively NOT the answer.
LinkType = Literal[
    "defines",        # PRD or spec defines a feature
    "implements",     # PBI or ticket implements a feature
    "depends_on",     # a document-level dependency statement
    "supersedes",     # version lineage
    "contextualises", # nearby, shared vocabulary, NOT the answer
    "blocks",
]

LinkTargetType = Literal["product", "feature", "requirement", "pbi", "component"]


# ---------------------------------------------------------------------------
# Version lineage
# ---------------------------------------------------------------------------

@dataclass
class VersionedEntity:
    """
    Fields shared by every document type that can exist in more than one version.

    APPROVED SCHEMA CHANGE 1 - generalised version lineage. Previously only
    `Requirement` carried version fields, and `Feature` had none at all. Since 5 of the
    12 superseded documents are feature specs, the old schema could not represent the
    approved corpus at all.

    APPROVED SCHEMA CHANGE 2 - `is_current` is the single authoritative flag. The old
    schema expressed this negatively as `is_superseded`, which is easy to get wrong: an
    entity with the field left at its default reads as "not superseded" whether or
    anyone thought about it. A positive `is_current` plus `validate_version_lineage`
    makes the invariant checkable rather than assumed.

    Why `document_id` lives here rather than being assigned during rendering: the
    version chain needs each entity to name the *other* version's document, so document
    IDs cannot be allocated afterwards without a circular reference. Deriving them from
    (type, entity, version) makes them stable under any future edit to the corpus, which
    is what "stable document ID" has to mean if chunk IDs are to stay valid.
    """
    document_id: str                      # e.g. "DOC-FEAT-A-01-v1"
    version: str                          # e.g. "1.0"
    # Named `version_status`, NOT `status`. `Feature` already has a `status` field meaning
    # feature lifecycle (discovered/planned/launched/...). A base-class `status` would
    # shadow it, and the two meanings are unrelated, so sharing the name would make
    # `feature.status` ambiguous depending on which class you read it through.
    version_status: VersionStatus        # explicit, not derived from dates
    created_date: str                     # ISO date
    modified_date: str                    # ISO date
    superseded_by: str                    # document_id of the NEWER version; "" iff current
    supersedes: str                       # document_id of the PREVIOUS version; "" iff first
    is_current: bool                      # THE authoritative flag


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
class Feature(VersionedEntity):
    """
    A product feature - the central entity queries will target.

    `formal_term` and `colloquial_terms` are the experimental control, not decoration.
    They let the same underlying concept appear under different vocabulary in different
    documents, and in yet another phrasing in the query. See DATA_DESIGN.md section 6.

    APPROVED SCHEMA CHANGE 4 - `confusable_with` makes D1/D2 distractors reproducible.
    Declaring adjacency means a near-miss is a fact in the model whose non-relevance can
    be derived objectively, rather than something that happens to occur.
    """
    feature_id: str                      # e.g. "FEAT-A-01"
    product_id: str
    name: str
    status: FeatureStatus
    priority: int                        # 1 = highest
    formal_term: str                     # precise technical vocabulary
    colloquial_terms: list[str]          # informal phrasings used in real prose
    summary: str                         # one-line factual description
    confusable_with: list[str] = field(default_factory=list)  # other feature_ids
    # Which requirement governs this feature. Used by D2 distractors: a related feature
    # carrying a different requirement must be distinguishable from this one.
    requirement_id: str = ""
    # An approval limit or threshold stated by this feature specification, e.g. "$5,000".
    # Empty means the spec states no limit. Required for Q-SUP-3 (D-013 amendment): the
    # corpus must contain a v1/v2 pair whose stated limit CHANGED between versions.
    approval_limit: str = ""


@dataclass
class Prd(VersionedEntity):
    """
    A Product Requirements Document. One document, several requirements.

    A PRD is a *document* entity rather than a requirement entity because the approved
    corpus has 16 business requirements distributed across 10 PRDs. Modelling a
    requirement as a document would force the choice between 16 PRD documents and
    10 PRD documents, and the approved count is 10 (+7 superseded = 17).
    """
    prd_id: str                          # e.g. "PRD-A-01"
    product_id: str
    title: str
    author_role: str
    is_normative: bool                   # authoritative when two documents disagree
    summary: str
    sections: list[str]                  # ordered headings; content rendered per section
    requirement_ids: list[str] = field(default_factory=list)


@dataclass
class Requirement:
    """
    A PRD-level requirement. Lives INSIDE a Prd, and is not itself a document.

    `is_normative` marks the requirement as authoritative when two documents disagree.
    This gives the corpus a real "which document wins" structure instead of leaving
    conflicts unresolvable.
    """
    requirement_id: str                  # e.g. "REQ-A-01"
    prd_id: str                          # owning PRD document
    product_id: str
    title: str
    statement: str                       # the normative sentence, quoted verbatim in tests
    is_normative: bool = True


@dataclass
class Pbi:
    """
    A Product Backlog Item / user story. Short, informal, often vague.

    APPROVED SCHEMA CHANGE 5 - the duplicated `formal_term` / `colloquial_terms` fields
    have been REMOVED. They duplicated the owning Feature's fields, which meant two
    sources of truth for the lexical-divergence control. They would have drifted, and
    drift there is silent and would corrupt the central experimental result. A Pbi now
    inherits its vocabulary from its feature via `feature_id`.
    """
    pbi_id: str                          # e.g. "PBI-A-014"
    product_id: str
    feature_id: str
    title: str
    description: str
    story_points: int
    status: PbiStatus
    created_date: str
    author_role: str
    component_id: str                    # technical component this item touches


@dataclass
class TechnicalComponent:
    """A service, database, queue, or third-party dependency."""
    component_id: str                    # e.g. "COMP-07"
    name: str
    component_type: ComponentType
    owner_team: str
    notes: str = ""
    # APPROVED SCHEMA CHANGE 4 - adjacency is declared, not inferred. A component that is
    # adjacent but NOT a dependency is the D3 distractor type, and it only exists in the
    # corpus if the model says so.
    adjacent_component_ids: list[str] = field(default_factory=list)


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
    pbi_id: str
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
    messiest document type in the corpus still has every factual claim traceable to the
    model. Prose form comes from the renderer, not from invention.
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
class Dependency:
    """
    The core of the ground truth.

    `explicitness` is the distinction that makes a real finding possible:
      - explicit  -> some document states the relationship in words. Good keyword search
                     can find this.
      - implicit  -> the relationship follows from the model but no document states it.
                     Only semantic reasoning recovers it.
    Reporting the two separately is the most likely place a useful, honest result
    appears, because it says WHERE semantic retrieval actually pays off.

    Per approved Q5, an implicit dependency is ALWAYS encoded here. It is "implicit" with
    respect to what the documents say, never with respect to whether it is knowable.
    """
    dependency_id: str                   # e.g. "DEP-031"
    from_type: Literal["feature", "pbi", "requirement", "component"]
    from_id: str
    to_type: Literal["feature", "pbi", "requirement", "component"]
    to_id: str
    dependency_type: DependencyType
    description: str
    explicitness: DependencyExplicitness


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
class DocumentLink:
    """
    APPROVED SCHEMA CHANGE 3 - first-class cross-document reference.

    Previously cross-document references existed only as a by-product of rendering
    (`Document.referenced_entity_ids`), which made the ~435 approved reference edges a
    property of the renderer rather than of the model, and therefore not countable
    without rendering first.

    Making it an entity means the edge count is a model fact, and `contextualises` links
    are how D1/D2/D3 distractors are *declared*. A declared distractor has objectively
    derivable non-relevance, which is precisely what Q6 requires and what a
    judgement-based distractor set cannot provide.
    """
    link_id: str                         # e.g. "LNK-0001"
    from_document_id: str
    to_entity_type: LinkTargetType
    to_entity_id: str
    link_type: LinkType


@dataclass
class SourceModel:
    """The complete source of truth for one corpus version."""
    model_version: str                   # e.g. "v0-sample"
    seed: int
    created_date: str
    products: list[Product] = field(default_factory=list)
    features: list[Feature] = field(default_factory=list)
    prds: list[Prd] = field(default_factory=list)
    requirements: list[Requirement] = field(default_factory=list)
    pbis: list[Pbi] = field(default_factory=list)
    components: list[TechnicalComponent] = field(default_factory=list)
    tickets: list[Ticket] = field(default_factory=list)
    decisions: list[DecisionRecord] = field(default_factory=list)
    meeting_notes: list[MeetingNote] = field(default_factory=list)
    runbooks: list[Runbook] = field(default_factory=list)
    dependencies: list[Dependency] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    document_links: list[DocumentLink] = field(default_factory=list)

    # -- lookups -------------------------------------------------------------
    # These exist so that ground-truth derivation is a lookup, not a text-matching
    # exercise. If deriving a label required parsing prose, the label would not be
    # trustworthy.

    def _must_find_current(self, items, key, value, label):
        """
        Resolve a VERSIONED entity to its authoritative current version.

        A naive first-match lookup is wrong here: features and PRDs repeat the same
        business ID across versions, so the first match is usually the SUPERSEDED v1.
        That silently rendered stale content into documents whose references pointed at
        the current version. Callers asking for "the feature" always mean the current
        one, so this resolves to it, and refuses to guess when the model is ambiguous.
        """
        matches = [item for item in items if getattr(item, key) == value]
        if not matches:
            raise KeyError(
                f"{label} '{value}' is not in the source model. Refusing to guess."
            )
        current = [item for item in matches if item.is_current]
        if len(current) == 1:
            return current[0]
        if len(current) > 1:
            raise ValueError(
                f"{label} '{value}' has {len(current)} versions all marked current "
                f"({[c.version for c in current]}). Exactly one version may be current. "
                f"This is a data defect, not something to resolve by picking one."
            )
        versions = ", ".join(m.version for m in matches)
        raise ValueError(
            f"{label} '{value}' has no current version - all are superseded ({versions}). "
            f"Either the lineage is incomplete or the caller genuinely wants a historical "
                f"version and should use _must_find for the exact record."
        )

    def get_feature(self, feature_id: str) -> Feature:
        return self._must_find_current(self.features, "feature_id", feature_id, "Feature")

    def get_pbi(self, pbi_id: str) -> Pbi:
        return self._must_find(self.pbis, "pbi_id", pbi_id)

    def get_prd(self, prd_id: str) -> Prd:
        return self._must_find_current(self.prds, "prd_id", prd_id, "PRD")

    def get_requirement(self, requirement_id: str) -> Requirement:
        return self._must_find(self.requirements, "requirement_id", requirement_id)

    def get_component(self, component_id: str) -> TechnicalComponent:
        return self._must_find(self.components, "component_id", component_id)

    def get_product(self, product_id: str) -> Product:
        return self._must_find(self.products, "product_id", product_id)

    def all_versioned(self) -> list[VersionedEntity]:
        return [*self.prds, *self.features]

    def all_entity_ids(self) -> set[str]:
        return (
            {p.product_id for p in self.products}
            | {f.feature_id for f in self.features}
            | {r.requirement_id for r in self.requirements}
            | {p.pbi_id for p in self.pbis}
            | {c.component_id for c in self.components}
        )

    def is_known_entity(self, entity_id: str) -> bool:
        return entity_id in self.all_entity_ids()

    def documents_for_entity(self, entity_id: str) -> list[str]:
        """
        Which rendered documents carry this entity, derived from DECLARED DocumentLinks.

        APPROVED SCHEMA CHANGE 6 - the previous implementation read a dynamically
        attached `_rendered_documents` attribute through `getattr(..., [])`. That default
        meant an unset attribute silently produced an empty list rather than an error, so
        provenance could vanish with no signal at all. This version is a pure lookup over
        declared data, and raises for an entity that appears nowhere in the model.
        """
        if entity_id not in self.all_entity_ids():
            raise KeyError(
                f"Entity '{entity_id}' does not exist in the source model. This is a data "
                f"error, not a runtime condition to handle."
            )
        return sorted({
            link.from_document_id for link in self.document_links
            if link.to_entity_id == entity_id
        })

    def dependencies_for(self, entity_id: str) -> list[Dependency]:
        """Every dependency where this entity is either end. Used for dependency-accuracy
        ground truth."""
        return [
            d for d in self.dependencies
            if d.from_id == entity_id or d.to_id == entity_id
        ]

    def links_from(self, document_id: str) -> list[DocumentLink]:
        return [link for link in self.document_links
                if link.from_document_id == document_id]

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
            "prds": [asdict(p) for p in self.prds],
            "requirements": [asdict(r) for r in self.requirements],
            "pbis": [asdict(p) for p in self.pbis],
            "components": [asdict(c) for c in self.components],
            "tickets": [asdict(t) for t in self.tickets],
            "decisions": [asdict(d) for d in self.decisions],
            "meeting_notes": [asdict(m) for m in self.meeting_notes],
            "runbooks": [asdict(r) for r in self.runbooks],
            "dependencies": [asdict(d) for d in self.dependencies],
            "conflicts": [asdict(c) for c in self.conflicts],
            "document_links": [asdict(link) for link in self.document_links],
        }

    def save(self, path) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.to_dict(), handle, indent=2, ensure_ascii=False)


def entity_type_of(entity: object) -> str:
    if isinstance(entity, Prd):
        return "prd"
    if isinstance(entity, Feature):
        return "feature"
    raise TypeError(f"Unmapped versioned entity type: {type(entity).__name__}")


def entity_primary_id(entity: object) -> str:
    if isinstance(entity, Prd):
        return entity.prd_id
    if isinstance(entity, Feature):
        return entity.feature_id
    raise TypeError(f"Unmapped versioned entity type: {type(entity).__name__}")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    check_id: str
    description: str
    passed: bool
    detail: str = ""
    is_scale_target: bool = False

    def __str__(self) -> str:
        flag = "SCALE" if self.is_scale_target else "STRUCT"
        status = "PASS" if self.passed else ("N/A " if self.is_scale_target else "FAIL")
        line = f"[{flag}] {self.check_id:<4} {status}  {self.description}"
        if self.detail:
            line += f"\n            {self.detail}"
        return line


def validate_model(model: SourceModel, expected_scale: Optional[dict] = None) -> list[ValidationResult]:
    """
    Run every structural invariant, plus any scale targets supplied.

    The distinction matters. Structural invariants (V1-V8) are absolute: if any fails, the
    model is broken and ground truth cannot be trusted. Scale targets (V4, V9) describe
    the approved FULL corpus and are checked only when `expected_scale` is passed - a
    deliberately small sample is *supposed* to fail them, and treating that as a failure
    would mean the sample could never be validated at all.

    Returns results rather than raising, so that a report can be shown. Callers that
    require a hard failure should check `passed` on non-scale results.
    """
    results: list[ValidationResult] = []
    versioned = model.all_versioned()
    doc_ids = {e.document_id for e in versioned}

    # -- V1: exactly one current version per lineage group --------------------
    groups: dict[str, list] = {}
    for entity in versioned:
        groups.setdefault(entity_type_of(entity) + ":" + entity_primary_id(entity), []).append(entity)
    bad = [g for g, es in groups.items() if sum(e.is_current for e in es) != 1]
    results.append(ValidationResult(
        "V1", "Exactly one is_current=True per versioned entity",
        not bad,
        "" if not bad else f"offending groups: {bad}",
    ))

    # -- V2: superseded documents resolve through superseded_by ---------------
    unresolved = [
        e.document_id for e in versioned
        if not e.is_current and (not e.superseded_by or e.superseded_by not in doc_ids)
    ]
    results.append(ValidationResult(
        "V2", "Every superseded document resolves through superseded_by",
        not unresolved,
        "" if not unresolved else f"unresolved: {unresolved}",
    ))

    # -- V3: current documents have no superseded_by --------------------------
    wrong = [e.document_id for e in versioned if e.is_current and e.superseded_by]
    results.append(ValidationResult(
        "V3", "Every current document has empty superseded_by",
        not wrong,
        "" if not wrong else f"offending: {wrong}",
    ))

    # -- V3b: the two directions of the chain must agree -----------------------
    # `supersedes` on the newer document and `superseded_by` on the older one describe
    # the same edge. If they disagree, the chain is ambiguous, and a query about which
    # version is current would have no single derivable answer.
    inconsistent = []
    for entity in versioned:
        if entity.supersedes:
            older = next((e for e in versioned if e.document_id == entity.supersedes), None)
            if older is None or older.superseded_by != entity.document_id:
                inconsistent.append(entity.document_id)
    results.append(ValidationResult(
        "V3b", "supersedes and superseded_by agree in both directions",
        not inconsistent,
        "" if not inconsistent else f"offending: {inconsistent}",
    ))

    # -- V4: superseded document count (SCALE TARGET) -------------------------
    superseded = [e for e in versioned if not e.is_current]
    expected = (expected_scale or {}).get("superseded_documents")
    results.append(ValidationResult(
        "V4", f"Superseded document count == {expected if expected else 'n/a'}",
        expected is None or len(superseded) == expected,
        f"actual: {len(superseded)}",
        is_scale_target=expected is None,
    ))

    # -- V5: every DocumentLink endpoint resolves ----------------------------
    entity_ids = model.all_entity_ids()
    dangling = [
        link.link_id for link in model.document_links
        if link.from_document_id not in doc_ids_from(model)
        or link.to_entity_id not in entity_ids
    ]
    results.append(ValidationResult(
        "V5", "Every DocumentLink endpoint resolves to a real document and entity",
        not dangling,
        "" if not dangling else f"dangling: {dangling}",
    ))

    # -- V6: confusable_with targets are real, non-self, same-product --------
    feature_ids = {f.feature_id for f in model.features}
    bad_confusable = []
    for feature in model.features:
        for other in feature.confusable_with:
            if other not in feature_ids:
                bad_confusable.append(f"{feature.feature_id}->{other} (unknown)")
            elif other == feature.feature_id:
                bad_confusable.append(f"{feature.feature_id}->{other} (self)")
            else:
                target = model.get_feature(other)
                if target.product_id != feature.product_id:
                    bad_confusable.append(f"{feature.feature_id}->{other} (cross-product)")
    results.append(ValidationResult(
        "V6", "confusable_with targets are real, non-self and same-product",
        not bad_confusable,
        "" if not bad_confusable else f"offending: {bad_confusable}",
    ))

    # -- V6b: adjacent_component_ids resolve ---------------------------------
    component_ids = {c.component_id for c in model.components}
    bad_adjacent = [
        f"{c.component_id}->{other}" for c in model.components
        for other in c.adjacent_component_ids if other not in component_ids
    ]
    results.append(ValidationResult(
        "V6b", "adjacent_component_ids resolve to real components",
        not bad_adjacent,
        "" if not bad_adjacent else f"offending: {bad_adjacent}",
    ))

    # -- V7: no self-dependency ----------------------------------------------
    self_deps = [d.dependency_id for d in model.dependencies if d.from_id == d.to_id]
    results.append(ValidationResult(
        "V7", "No dependency has from_id == to_id",
        not self_deps,
        "" if not self_deps else f"offending: {self_deps}",
    ))

    # -- V8: every document has at least one outgoing link -------------------
    linked = {link.from_document_id for link in model.document_links}
    unlinked = sorted(doc_ids_from(model) - linked)
    results.append(ValidationResult(
        "V8", "Every document has at least one DocumentLink",
        not unlinked,
        "" if not unlinked else f"unlinked documents: {unlinked}",
    ))

    # -- V9: explicit / implicit dependency split (SCALE TARGET) -------------
    explicit = sum(1 for d in model.dependencies if d.explicitness == "explicit")
    implicit = sum(1 for d in model.dependencies if d.explicitness == "implicit")
    expected_exp = (expected_scale or {}).get("explicit_dependencies")
    results.append(ValidationResult(
        "V9", f"Explicit dependencies == {expected_exp if expected_exp else 'n/a'}",
        expected_exp is None or explicit == expected_exp,
        f"actual: {explicit} explicit, {implicit} implicit, {explicit + implicit} total",
        is_scale_target=expected_exp is None,
    ))

    return results


def doc_ids_from(model: SourceModel) -> set[str]:
    """Every document ID the model will produce. Includes versioned documents and the
    single-document entity types."""
    ids = {e.document_id for e in model.all_versioned()}
    ids |= {f"DOC-{p.pbi_id}" for p in model.pbis}
    ids |= {f"DOC-{c.component_id}" for c in model.components}
    ids |= {f"DOC-{t.ticket_id}" for t in model.tickets}
    ids |= {f"DOC-{d.decision_id}" for d in model.decisions}
    ids |= {f"DOC-{n.note_id}" for n in model.meeting_notes}
    ids |= {f"DOC-{r.runbook_id}" for r in model.runbooks}
    return ids

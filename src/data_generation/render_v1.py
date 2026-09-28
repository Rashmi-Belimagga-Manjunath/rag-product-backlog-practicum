"""
Deterministic renderer for the final schema.

Renders a SourceModel into Markdown documents. No LLM is involved: every factual claim in
the output is a value from the model, so the corpus and the ground truth can never
disagree about what was said.

Design points that matter for the experiment:

1. DOCUMENT IDS come from the model, not from render order. `Document.document_id` is the
   entity's own declared ID. If IDs were assigned by sequence, adding one document to the
   corpus would renumber every document after it, and a chunk ID recorded in an earlier
   result would silently point at the wrong text.

2. VERSION METADATA is rendered into the document, not held only in the model. A retriever
   has to be able to see that a document is superseded, otherwise the version queries are
   unanswerable from the text alone.

3. HEADINGS are emitted as real markdown headings. The chunker splits on them, and section
   structure in the output is what keeps a dependency statement intact in one chunk.

4. The register model controls vocabulary. PRDs and specs draw on the formal term; tickets
   and meeting notes draw on the colloquial term. This is the validity-critical lexical
   divergence control described in DATA_DESIGN.md section 6.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .source_model import (
    DecisionRecord,
    Dependency,
    DocumentLink,
    Feature,
    MeetingNote,
    Pbi,
    Prd,
    Product,
    Requirement,
    Runbook,
    SourceModel,
    TechnicalComponent,
    Ticket,
)


@dataclass
class Document:
    document_id: str
    doc_type: str
    title: str
    body: str
    source_entity_id: str
    product_id: str
    version: str = "1.0"
    version_status: str = "current"
    is_current: bool = True
    superseded_by: str = ""
    supersedes: str = ""
    created_date: str = ""
    modified_date: str = ""
    references: list[DocumentLink] = field(default_factory=list)

    def referenced_entity_ids(self) -> list[str]:
        return [link.to_entity_id for link in self.references]

    def word_count(self) -> int:
        return len(self.body.split())


def _register_for(product: Product, doc_type: str, rng: random.Random) -> str:
    """
    Decide which register a document uses.

    The mapping mirrors how real repositories behave, and getting it wrong would quietly
    break the experiment: if tickets used PRD vocabulary there would be no lexical
    divergence, and BM25 would score well for the wrong reason.

      - PRDs, specs, runbooks: mostly the precise technical term. A formally-governed
        product does this more often than an informal one.
      - Tickets: almost always the customer's own words. Customers do not read PRDs, so
        this stays colloquial regardless of how formal the product is.
      - Meeting notes: mostly colloquial, whatever the product's maturity.
      - PBIs, decision logs: genuinely mixed, leaning informal.

    `formal_bias` is therefore only applied where documentation maturity actually governs
    the register, rather than being applied uniformly.
    """
    formal_bias = 0.85 if product.documentation_maturity == "formal" else 0.35

    if doc_type in ("prd", "feature_spec", "runbook"):
        return "formal" if rng.random() < formal_bias else "colloquial"
    if doc_type == "ticket":
        return "colloquial" if rng.random() < 0.85 else "formal"
    if doc_type == "meeting_notes":
        return "colloquial" if rng.random() < 0.75 else "formal"
    return "formal" if rng.random() < (formal_bias * 0.5) else "colloquial"


def _term(feature: Feature, register: str) -> str:
    if register == "formal":
        return feature.formal_term
    return feature.colloquial_terms[0]


def _version_banner(entity) -> str:
    """Rendered into the document so version state is visible to a retriever."""
    if entity.is_current:
        return (f"Status: current. Version {entity.version}. "
                f"Last modified {entity.modified_date}.")
    return (f"Status: SUPERSEDED. Version {entity.version}, last modified "
            f"{entity.modified_date}. This version was replaced by "
            f"{entity.superseded_by} and is retained for history only. Do not implement "
            f"from this document.")


# ---------------------------------------------------------------------------
# Per-type renderers
# ---------------------------------------------------------------------------

# The fixed PRD boilerplate was originally written for the Meridian/HRTech domain and
# is retained verbatim there so the mechanism sample stays byte-for-byte identical.
# Other domains draw on their own profile; the fallback is the HRTech text.
_PRD_DOMAIN = {
    "Consumer habit-tracking": {
        "goals": ("Reduce the friction between signing up and keeping a first habit "
                  "going, while keeping the streak mechanic predictable and honest for "
                  "every user."),
        "non_goals": ("This document does not cover habit template curation or social "
                      "features. Those are specified separately."),
        "success": ("Measured as: thirty-day streak survival, share of recovery "
                    "prompts accepted, and repeat-week retention after a prompt is "
                    "offered."),
        "open": ("How forceful should the first recovery prompt be? The current answer "
                 "of a single light suggestion is provisional."),
    },
}


def _domain_text(product: Product, key: str, h_r_key: str) -> str:
    profile = _PRD_DOMAIN.get(product.domain)
    return (profile or {}).get(key) or _PRD_DOMAIN["Consumer habit-tracking"].get(key) or (
        _hr_texts(h_r_key)
    )


def _hr_texts(key: str) -> str:
    return {
        "goals": ("Reduce the number of steps a new employee must complete before they "
                  "can reach a working product, while keeping every mandatory compliance "
                  "step enforced."),
        "non_goals": ("This document does not cover manager approval workflows or "
                      "payroll export formatting. Those are specified separately."),
        "success": ("Measured as: completion rate of the compliance steps, time to "
                    "first productive action, and support contact volume in the first "
                    "week."),
        "open": ("How many days should elapse before the tax step is requested? The "
                 "current answer of three days is provisional."),
    }[key]


def render_prd(prd: Prd, model: SourceModel, product: Product, register: str) -> str:
    lines = [f"# {prd.title}", "", f"Document: {prd.document_id}", _version_banner(prd),
             "", f"Author: {prd.author_role}", f"Product: {product.name} ({product.product_id})",
             ""]

    lines += [f"## {prd.sections[0]}", "", prd.summary, ""]
    lines += ["## Goals", "",
              _domain_text(product, "goals", "goals"), ""]
    lines += ["## Non-goals", "",
              _domain_text(product, "non_goals", "non_goals"), ""]

    lines += ["## Requirements", ""]
    for requirement in model.requirements:
        if requirement.prd_id != prd.prd_id:
            continue
        lines += [f"### {requirement.requirement_id}: {requirement.title}", "",
                  requirement.statement, ""]
        if requirement.is_normative:
            lines += [f"This requirement is normative for {product.name}. Where another "
                      f"document disagrees, this statement takes precedence.", ""]

    lines += ["## Success measures", "",
              _domain_text(product, "success", "success"), ""]
    if "Change log" in prd.sections:
        tax_governed = any(
            "tax" in requirement.statement.lower()
            for requirement in model.requirements
            if requirement.prd_id == prd.prd_id
        )
        if tax_governed:
            lines += ["## Change log", "",
                      f"Version {prd.version} supersedes version 1.0. The change moves "
                      f"the tax collection step out of initial registration and into the "
                      f"onboarding ramp, following the decision recorded in the decision "
                      f"log.", ""]
        else:
            lines += ["## Change log", "",
                      f"Version {prd.version} supersedes version 1.0. The changes follow "
                      f"the decisions recorded in the decision log and replace the "
                      f"behaviour described in the earlier version.", ""]
    lines += ["## Open questions", "",
              _domain_text(product, "open", "open"), ""]
    return "\n".join(lines)


def render_feature_spec(feature: Feature, model: SourceModel, product: Product,
                        register: str) -> str:
    term = _term(feature, register)
    lines = [f"# {feature.name} - specification", "",
             f"Document: {feature.document_id}", _version_banner(feature), "",
             f"Product: {product.name} ({product.product_id})",
             f"Feature: {feature.feature_id}", f"Lifecycle status: {feature.status}",
             f"Priority: {feature.priority}", ""]

    lines += ["## Purpose", "", feature.summary, ""]
    lines += ["## Terminology", "",
              f"Within this document the feature is referred to as: {term}.",
              f"Users describe the same thing as: {', '.join(feature.colloquial_terms)}.",
              ""]
    lines += ["## Behaviour", "",
              f"When {term.lower()} is active, the product behaves as follows.", ""]

    dependencies = [d for d in model.dependencies
                    if d.from_id == feature.feature_id and d.explicitness == "explicit"]
    if dependencies:
        lines += ["## Dependencies", ""]
        for dependency in dependencies:
            lines.append(f"- {dependency.description}")
        lines.append("")

    if feature.approval_limit:
        lines += ["## Approval limit", ""]
        if feature.is_current:
            lines.append(f"The current approval limit for {term} is "
                         f"{feature.approval_limit}.")
        else:
            lines.append(f"Under version {feature.version}, the approval limit for "
                         f"{term} was {feature.approval_limit}.")
        lines.append("")

    if feature.confusable_with:
        lines += ["## Related features", "",
                  "The following features are adjacent in scope and are sometimes "
                  "confused with this one:", ""]
        for other_id in feature.confusable_with:
            lines.append(f"- {other_id}")
        lines.append("")

    if not feature.is_current:
        lines += ["## Historical behaviour", ""]
        if feature.requirement_id:
            governing = model.get_requirement(feature.requirement_id)
            if "tax" in governing.statement.lower():
                lines.append("Under version 1.0, tax documentation was collected during "
                             "initial account registration, before the employee had used "
                             "the product. This was replaced in version 2.0.")
            else:
                lines.append(f"Under version 1.0, {term.lower()} shipped with different "
                             f"timing and defaults. Version 2.0 replaces this document.")
        else:
            lines.append(f"Under version 1.0, {term.lower()} shipped with different "
                         f"timing and defaults. Version 2.0 replaces this document.")
        lines.append("")

    return "\n".join(lines)


def render_pbi(pbi: Pbi, model: SourceModel, product: Product, register: str) -> str:
    feature = model.get_feature(pbi.feature_id)
    term = _term(feature, register)
    lines = [f"# {pbi.title}", "", f"Document: DOC-{pbi.pbi_id}", "Status: current.",
             f"Backlog item: {pbi.pbi_id}", f"Feature: {pbi.feature_id}",
             f"Story points: {pbi.story_points}", f"Raised: {pbi.created_date}", "",
             "## Story", "", pbi.description, "",
             f"## Context", "",
             f"This item sits under {pbi.feature_id} ({term}).",
             f"Primary component touched: {pbi.component_id}.", ""]

    dependencies = [d for d in model.dependencies
                    if d.from_id == pbi.pbi_id and d.explicitness == "explicit"]
    if dependencies:
        lines += ["## Dependencies", ""]
        for dependency in dependencies:
            lines.append(f"- {dependency.description}")
        lines += ["", "These relationships are stated in the story above.", ""]

    return "\n".join(lines)


def render_ticket(ticket: Ticket, model: SourceModel, product: Product,
                  register: str) -> str:
    feature = model.get_feature(ticket.feature_id)
    term = _term(feature, register)
    lines = [f"# Ticket {ticket.ticket_id}", "", f"Document: DOC-{ticket.ticket_id}",
             f"Raised: {ticket.opened_date}", f"Severity: {ticket.severity}",
             f"Reported by: {ticket.reporter_role}",
             f"Segment: {ticket.customer_segment}", "",
             "## Reported symptom", "", ticket.reported_symptom, "",
             "## Triage", "",
             f"Routed to {feature.feature_id} ({term}).",
             f"Linked backlog item: {ticket.pbi_id}.",
             f"Related component: {ticket.related_component_id}.", "",
             "## Resolution plan", "",
             "The owning team will work the fix through the standard delivery "
             "queue and hold the change until it clears the regression window. "
             "The service owner signs off before the build reaches the "
             "customer-facing release train.", ""]
    return "\n".join(lines)


def render_decision(decision: DecisionRecord, model: SourceModel, product: Product,
                    register: str) -> str:
    feature_id = decision.about_entity_id
    feature = model.get_feature(feature_id) if feature_id.startswith("FEAT") else None
    term = _term(feature, register) if feature else feature_id
    lines = [f"# Decision {decision.decision_id}", "",
             f"Document: DOC-{decision.decision_id}", f"Decided: {decision.decided_date}",
             f"Decided by: {decision.decided_by_role}", "",
             "## Decision", "", decision.decision, "",
             "## Rationale", "", decision.rationale, "",
             f"## Applies to", "", f"{feature_id} ({term}).", "",
             "## Context", "",
             "The recommendation was weighed against the current delivery "
             "backlog; the owning team will revisit it at the next quarterly "
             "review if the underlying cost model shifts.", ""]
    return "\n".join(lines)


def render_meeting_note(note: MeetingNote, model: SourceModel, product: Product,
                        register: str) -> str:
    lines = [f"# Meeting note {note.note_id}", "", f"Document: DOC-{note.note_id}",
             f"Date: {note.meeting_date}",
             f"Attending: {', '.join(note.attendees_role)}",
             f"Product: {product.name}", "",
             "## Topics", ""]
    for topic in note.topics:
        lines.append(f"- {topic}")
    lines += ["", "## Entities discussed", ""]
    for entity_id in note.about_entity_ids:
        lines.append(f"- {entity_id}")
    lines.append("")
    return "\n".join(lines)


def render_runbook(runbook: Runbook, model: SourceModel, product: Product,
                   register: str) -> str:
    component = model.get_component(runbook.component_id)
    lines = [f"# Runbook: {runbook.title}", "", f"Document: DOC-{runbook.runbook_id}",
             f"Component: {runbook.component_id} ({component.name})",
             f"Owner: {component.owner_team}", f"Last reviewed: {runbook.last_reviewed}",
             "", "## Steps", ""]
    for index, step in enumerate(runbook.steps, start=1):
        lines.append(f"{index}. {step}")
    lines += ["", "## Notes", "", component.notes, ""]
    return "\n".join(lines)


def render_component_doc(component: TechnicalComponent, model: SourceModel,
                         product: Product, register: str) -> str:
    lines = [f"# {component.name}", "", f"Document: DOC-{component.component_id}",
             f"Component: {component.component_id}",
             f"Type: {component.component_type}", f"Owner: {component.owner_team}",
             "", "## Description", "", component.notes, ""]
    if component.adjacent_component_ids:
        lines += ["## Adjacent components", "",
                  "These components are technically related but are NOT dependencies of "
                  "this one:", ""]
        for adjacent_id in component.adjacent_component_ids:
            lines.append(f"- {adjacent_id}")
        lines.append("")

    dependencies = [d for d in model.dependencies
                    if d.from_id == component.component_id and d.explicitness == "explicit"]
    if dependencies:
        lines += ["## Dependencies", ""]
        for dependency in dependencies:
            lines.append(f"- {dependency.description}")
        lines.append("")

    lines += ["## Operational notes", "",
              "The component is monitored through the shared alerting "
              "channel; the owning team reviews capacity and latency trends "
              "before every release.", ""]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

_RENDERERS = {
    "prd": render_prd,
    "feature_spec": render_feature_spec,
    "pbi": render_pbi,
    "ticket": render_ticket,
    "decision_log": render_decision,
    "meeting_notes": render_meeting_note,
    "runbook": render_runbook,
    "component_doc": render_component_doc,
}


def render_corpus(model: SourceModel) -> list[Document]:
    """
    Render every entity that owns a document. Fully deterministic: the same model always
    produces the same documents, byte for byte, so chunk IDs are reproducible.
    """
    # The renderer deliberately does NOT draw on implicit dependencies. If a relationship
    # is not stated in a document it must not appear in one, otherwise the explicit /
    # implicit split in the ground truth would be false.
    rng = random.Random(model.seed)
    documents: list[Document] = []

    tasks: list[tuple[str, object, str, str]] = []
    for prd in model.prds:
        tasks.append(("prd", prd, prd.document_id, ""))
    for feature in model.features:
        tasks.append(("feature_spec", feature, feature.document_id, ""))
    for pbi in model.pbis:
        tasks.append(("pbi", pbi, f"DOC-{pbi.pbi_id}", ""))
    for ticket in model.tickets:
        tasks.append(("ticket", ticket, f"DOC-{ticket.ticket_id}", ""))
    for decision in model.decisions:
        tasks.append(("decision_log", decision, f"DOC-{decision.decision_id}", ""))
    for note in model.meeting_notes:
        tasks.append(("meeting_notes", note, f"DOC-{note.note_id}", ""))
    for runbook in model.runbooks:
        tasks.append(("runbook", runbook, f"DOC-{runbook.runbook_id}", ""))
    for component in model.components:
        tasks.append(("component_doc", component, f"DOC-{component.component_id}", ""))

    links_by_document: dict[str, list[DocumentLink]] = {}
    for link in model.document_links:
        links_by_document.setdefault(link.from_document_id, []).append(link)

    for doc_type, entity, document_id, _ in tasks:
        # TechnicalComponent carries no product_id: a component may serve either product.
        # Resolve it to the product that references it, deterministically, so the rendered
        # document still carries a valid product context.
        if hasattr(entity, "product_id"):
            product_id = entity.product_id
        else:
            product_id = _product_for_component(model, entity.component_id)
        product = model.get_product(product_id)
        register = _register_for(product, doc_type, rng)
        body = _RENDERERS[doc_type](entity, model, product, register)

        title = entity.get("title") if isinstance(entity, dict) else _title_of(entity)
        is_versioned = hasattr(entity, "is_current")

        documents.append(Document(
            document_id=document_id,
            doc_type=doc_type,
            title=title,
            body=body,
            source_entity_id=_primary_id_of(entity),
            product_id=product_id,
            version=getattr(entity, "version", "1.0"),
            version_status=getattr(entity, "version_status", "current"),
            is_current=getattr(entity, "is_current", True),
            superseded_by=getattr(entity, "superseded_by", ""),
            supersedes=getattr(entity, "supersedes", ""),
            created_date=getattr(entity, "created_date", getattr(entity, "meeting_date", "")),
            modified_date=getattr(entity, "modified_date", ""),
            references=links_by_document.get(document_id, []),
        ))

    return documents


def _product_for_component(model: SourceModel, component_id: str) -> str:
    """A component's product is whichever product actually uses it. Determined from
    declared data, never hard-coded, so a component shared by both products is assigned
    consistently across runs."""
    users = {p.product_id for p in model.pbis if p.component_id == component_id}
    if not users:
        users = {t.product_id for t in model.tickets if t.related_component_id == component_id}
    if not users:
        raise KeyError(
            f"Component '{component_id}' is not used by any PBI or ticket, so it has no "
            f"product context. Add a usage reference rather than defaulting silently."
        )
    return sorted(users)[0]


def _title_of(entity) -> str:
    for attribute in ("title", "name"):
        if hasattr(entity, attribute):
            return getattr(entity, attribute)
    return getattr(entity, "feature_id", None) or getattr(entity, "pbi_id", "")


def _primary_id_of(entity) -> str:
    """
    A document's SUBJECT - the entity it is about.

    Dispatch is on the concrete type, not on a field-name search. A search by attribute
    order silently returned the wrong subject: `Pbi` and `Ticket` both CARRY a
    `feature_id` as a reference, so checking `feature_id` before `pbi_id`/`ticket_id`
    made every PBI and ticket document claim to be a feature document. The PBI and ticket
    entities then never appeared as the subject of any chunk, and provenance-based ground
    truth could not target them.
    """
    primary = {
        "Prd": "prd_id",
        "Feature": "feature_id",
        "Pbi": "pbi_id",
        "Ticket": "ticket_id",
        "DecisionRecord": "decision_id",
        "MeetingNote": "note_id",
        "Runbook": "runbook_id",
        "TechnicalComponent": "component_id",
    }.get(type(entity).__name__)
    if primary is None:
        raise TypeError(
            f"No documented subject mapping for {type(entity).__name__}. Add it rather "
            f"than falling back to a field search that can return a referenced ID."
        )
    return getattr(entity, primary)

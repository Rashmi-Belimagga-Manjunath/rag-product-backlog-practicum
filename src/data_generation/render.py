"""
Deterministic template-based renderer: source model -> synthetic documents.

WHY TEMPLATES AND NOT AN LLM
----------------------------
Every document here is rendered from structured data. No language model writes the
corpus, and no language model writes the ground truth. If an LLM authored the documents,
the experiment would measure the generator rather than retrieval, and the "independent"
ground truth would not be independent of anything.

Natural variation comes from structured slots - sentence frames, section ordering,
formality register, document metadata - selected deterministically from a recorded seed.
So the corpus is reproducible: same seed and same model version gives byte-identical
documents and identical chunk IDs.

THE VOCABULARY REGISTER
-----------------------
The one thing that makes this corpus capable of testing the research question is
controlled vocabulary divergence (DATA_DESIGN.md section 6). The same concept appears
as:
  - `formal_term`      in PRDs, specs, runbooks
  - `colloquial_terms` in tickets, meeting notes, and informal PBIs
  - a third phrasing   in the query text
If documents and queries shared vocabulary, BM25 would score well and we would have
learned nothing about semantic retrieval.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import random

from .source_model import (
    SourceModel, Product, Feature, Requirement, Pbi, TechnicalComponent,
    Ticket, DecisionRecord, MeetingNote, Runbook,
)


# ---------------------------------------------------------------------------
# Rendered document
# ---------------------------------------------------------------------------

@dataclass
class Document:
    """
    One rendered document, carrying full provenance.

    `source_entity_id` is the single most important field. It is what allows
    ground-truth relevance labels to be derived by propagation (see
    ground_truth.py) rather than by reading text. Chunking must propagate it.
    """
    document_id: str
    source_entity_type: str
    source_entity_id: str
    doc_type: str
    title: str
    product_id: str
    created_date: str
    version: str
    ticket_ref: str
    body: str
    # IDs of other entities mentioned, for relationship queries.
    referenced_entity_ids: list[str] = field(default_factory=list)
    # If this document is an older version, the document that replaced it. Lets a
    # retrieval system be tested on whether it surfaces stale content.
    superseded_by_document_id: str = ""


# ---------------------------------------------------------------------------
# Terminology register
# ---------------------------------------------------------------------------

def _term_for_register(
    entity: Feature | Pbi, register: str, rng: random.Random
) -> str:
    """
    Pick the vocabulary for a concept given a document's register.

    register = "formal"    -> the precise technical term
    register = "colloquial"-> an informal phrasing, chosen deterministically
    """
    if register == "formal":
        return entity.formal_term
    return rng.choice(entity.colloquial_terms)


def _register_for(
    product: Product, doc_type: str, rng: random.Random
) -> str:
    """
    Decide which register a given document should use.

    The mapping mirrors how real repositories actually behave, and getting it wrong
    would quietly break the experiment: if tickets used PRD vocabulary, there would be
    no lexical divergence and BM25 would score well for the wrong reason.

      - PRDs, specs, runbooks: mostly the precise technical term. A formally-governed
        product does this more often than an informal one.
      - Tickets: almost always the customer's own words. Customers do not read PRDs,
        so this stays colloquial regardless of how formal the product is.
      - Meeting notes: mostly colloquial, whatever the product's maturity.
      - PBIs and decision logs: genuinely mixed, leaning informal.

    `formal_bias` is therefore only applied to the document types where documentation
    maturity is actually the governing factor.
    """
    formal_bias = 0.85 if product.documentation_maturity == "formal" else 0.35

    if doc_type in ("prd", "feature_spec", "runbook"):
        return "formal" if rng.random() < formal_bias else "colloquial"

    if doc_type == "ticket":
        return "colloquial" if rng.random() < 0.85 else "formal"

    if doc_type == "meeting_notes":
        return "colloquial" if rng.random() < 0.75 else "formal"

    # pbi, decision_log: mixed
    return "formal" if rng.random() < (formal_bias * 0.5) else "colloquial"


# ---------------------------------------------------------------------------
# Per-document-type renderers
# ---------------------------------------------------------------------------

def render_prd(
    req: Requirement, product: Product, model: SourceModel,
    rng: random.Random, doc_id: str,
) -> Document:
    """
    A PRD: long, multi-section, versioned.

    Section order comes from the model, not the renderer, so section structure is
    inspectable data. This is the document type that produces long chunks and is
    therefore the main test of the chunking configuration.
    """
    register = _register_for(product, "prd", rng)
    terms = {
        f.feature_id: _term_for_register(f, register, rng)
        for f in model.features if f.product_id == product.product_id
    }
    referenced = list(req.feature_ids)

    lines: list[str] = []
    header = f"# {req.title}"
    if req.is_superseded:
        header += "  [SUPERSEDED]"
    lines.append(header)
    lines.append("")
    lines.append(
        f"Document type: Product Requirements Document | Version: {req.version} | "
        f"Status: {'Superseded' if req.is_superseded else ('Authoritative' if req.is_normative else 'Draft')} | "
        f"Owner: {req.author_role} | Date: {req.created_date}"
    )
    lines.append("")
    lines.append(f"Summary: {req.summary}")
    lines.append("")

    for section in req.sections:
        lines.append(f"## {section}")
        lines.append("")
        if section.lower().startswith("background"):
            lines.append(
                f"{req.summary} This document was raised by {req.author_role} on "
                f"{req.created_date} and is version {req.version}."
            )
            if req.is_superseded:
                lines.append(
                    "Note: this version has been replaced. Do not use it for planning."
                )
        elif section.lower().startswith("goal"):
            for fid in req.feature_ids:
                feature = model.get_feature(fid)
                lines.append(
                    f"- Advance {terms[fid]} ({feature.name}), currently at status "
                    f"'{feature.status}', priority {feature.priority}."
                )
        elif section.lower().startswith("non-goal"):
            lines.append(
                "- Out of scope for this document: implementation detail, migration "
                "planning, and commercial packaging."
            )
        elif section.lower().startswith("requirement"):
            for fid in req.feature_ids:
                feature = model.get_feature(fid)
                lines.append(
                    f"- The system shall support {terms[fid]}. "
                    f"Status: {feature.status}. Priority: {feature.priority}."
                )
                linked_pbis = [p for p in model.pbis if p.feature_id == fid]
                for pbi in linked_pbis:
                    lines.append(
                        f"  - Tracked as {pbi.pbi_id} ({pbi.title}), "
                        f"{pbi.status}, {pbi.story_points} points."
                    )
        elif section.lower().startswith("depend") or section.lower().startswith("constraint"):
            for dep in model.dependencies_for(req.requirement_id):
                lines.append(f"- {dep.dependency_id}: {dep.description}")
            for fid in req.feature_ids:
                for dep in model.dependencies_for(fid):
                    lines.append(f"- {dep.dependency_id}: {dep.description}")
        elif section.lower().startswith("risk"):
            lines.append(
                "- Delivery risk is concentrated in the components listed under "
                "Dependencies. Third-party components are outside the product team's control."
            )
        else:
            lines.append(
                f"{req.summary} This section is maintained by {req.author_role}."
            )
        lines.append("")

    return Document(
        document_id=doc_id,
        source_entity_type="requirement",
        source_entity_id=req.requirement_id,
        doc_type="prd",
        title=req.title,
        product_id=product.product_id,
        created_date=req.created_date,
        version=req.version,
        ticket_ref="",
        body="\n".join(lines).strip(),
        referenced_entity_ids=referenced,
    )


def render_feature_spec(
    feature: Feature, product: Product, model: SourceModel,
    rng: random.Random, doc_id: str,
) -> Document:
    """A technical specification for one feature. Medium length, structured."""
    register = _register_for(product, "feature_spec", rng)
    term = _term_for_register(feature, register, rng)
    related_pbis = [p for p in model.pbis if p.feature_id == feature.feature_id]
    related_tickets = [t for t in model.tickets if t.feature_id == feature.feature_id]
    referenced = [p.pbi_id for p in related_pbis] + [t.ticket_id for t in related_tickets]

    lines = [
        f"# {feature.name} - Technical Specification",
        "",
        f"Feature ID: {feature.feature_id} | Status: {feature.status} | "
        f"Priority: {feature.priority} | Product: {product.name}",
        f"Owner: {product.name} product team | Product maturity: "
        f"{product.documentation_maturity}",
        "",
        f"Summary: {feature.summary}",
        "",
        "## Terminology",
        "",
        f"In this document the feature is referred to as '{term}'. Alternate phrasing "
        f"seen elsewhere in the repository includes: "
        f"{', '.join(feature.colloquial_terms if register == 'formal' else [feature.formal_term])}.",
        "",
        "## Behaviour",
        "",
        f"The system exposes {term} to the tenant administrator. Behaviour is governed "
        f"by the linked backlog items below.",
        "",
        "## Linked backlog items",
        "",
    ]
    for pbi in related_pbis:
        lines.append(
            f"- {pbi.pbi_id}: {pbi.title} - status {pbi.status}, "
            f"{pbi.story_points} points, raised {pbi.created_date} by {pbi.author_role}."
        )
    if not related_pbis:
        lines.append("- None recorded.")

    lines += ["", "## Reported issues", ""]
    for ticket in related_tickets:
        lines.append(
            f"- {ticket.ticket_id} ({ticket.severity}): {ticket.reported_symptom} "
            f"- reported by {ticket.reporter_role} on {ticket.opened_date}."
        )
    if not related_tickets:
        lines.append("- None recorded.")

    lines += ["", "## Technical dependencies", ""]
    for dep in model.dependencies_for(feature.feature_id):
        lines.append(f"- {dep.dependency_id}: {dep.description}")

    return Document(
        document_id=doc_id,
        source_entity_type="feature",
        source_entity_id=feature.feature_id,
        doc_type="feature_spec",
        title=f"{feature.name} - Technical Specification",
        product_id=product.product_id,
        created_date=max(p.created_date for p in related_pbis) if related_pbis else "",
        version="1.0",
        ticket_ref="",
        body="\n".join(lines).strip(),
        referenced_entity_ids=referenced,
    )


def render_pbi(
    pbi: Pbi, product: Product, model: SourceModel,
    rng: random.Random, doc_id: str,
) -> Document:
    """
    A backlog item. Short, informal, and often thin on detail - which is realistic,
    and which makes these documents hard to retrieve by keyword alone.
    """
    register = _register_for(product, "pbi", rng)
    term = _term_for_register(pbi, register, rng)
    feature = model.get_feature(pbi.feature_id)

    lines = [
        f"# {pbi.pbi_id}",
        "",
        f"Title: {pbi.title}",
        f"Status: {pbi.status} | Story points: {pbi.story_points} | "
        f"Raised: {pbi.created_date} | Raised by: {pbi.author_role}",
        f"Feature: {feature.name} ({feature.feature_id})",
        "",
        "## Description",
        "",
        pbi.description,
        "",
        f"This item sits under {term}.",
        "",
        "## Acceptance notes",
        "",
        f"- Works for the {product.domain} use case.",
        "- Confirmed with the product owner before build.",
    ]

    return Document(
        document_id=doc_id,
        source_entity_type="pbi",
        source_entity_id=pbi.pbi_id,
        doc_type="pbi",
        title=pbi.title,
        product_id=product.product_id,
        created_date=pbi.created_date,
        version="1.0",
        ticket_ref="",
        body="\n".join(lines).strip(),
        referenced_entity_ids=[pbi.feature_id],
    )


def render_ticket(
    ticket: Ticket, product: Product, model: SourceModel,
    rng: random.Random, doc_id: str,
) -> Document:
    """
    A support ticket, in customer language.

    This is the document type that carries the strongest lexical divergence: customers
    describe a symptom in their own words, which rarely match the PRD vocabulary.
    """
    feature = model.get_feature(ticket.feature_id)
    component = model.get_component(ticket.related_component_id)

    lines = [
        f"# {ticket.ticket_id} - {ticket.reported_symptom}",
        "",
        f"Severity: {ticket.severity} | Opened: {ticket.opened_date} | "
        f"Reported by: {ticket.reporter_role} | Segment: {ticket.customer_segment}",
        "",
        "## What the customer reported",
        "",
        ticket.reported_symptom,
        "",
        "## Engineering triage",
        "",
        f"Routed to {feature.name} ({feature.feature_id}). Suspected area: "
        f"{component.name} ({component.component_id}), owned by {component.owner_team}.",
        "",
        "## Linked backlog items",
        "",
    ]
    for pbi in [p for p in model.pbis if p.feature_id == ticket.feature_id]:
        lines.append(f"- {pbi.pbi_id}: {pbi.title}")

    return Document(
        document_id=doc_id,
        source_entity_type="ticket",
        source_entity_id=ticket.ticket_id,
        doc_type="ticket",
        title=f"{ticket.ticket_id} - {ticket.reported_symptom}",
        product_id=product.product_id,
        created_date=ticket.opened_date,
        version="1.0",
        ticket_ref=ticket.ticket_id,
        body="\n".join(lines).strip(),
        referenced_entity_ids=[ticket.feature_id, ticket.related_component_id],
    )


def render_decision_log(
    record: DecisionRecord, product: Product, model: SourceModel,
    rng: random.Random, doc_id: str,
) -> Document:
    """A decision and its reason. Short, informal, and frequently the only place a
    rationale exists at all."""
    lines = [
        f"# Decision record {record.decision_id}",
        "",
        f"Date: {record.decided_date} | Decided by: {record.decided_by_role} | "
        f"Product: {product.name}",
        "",
        "## Decision",
        "",
        record.decision,
        "",
        "## Why",
        "",
        record.rationale,
        "",
        f"Relates to: {record.about_entity_id}",
    ]

    return Document(
        document_id=doc_id,
        source_entity_type="decision",
        source_entity_id=record.decision_id,
        doc_type="decision_log",
        title=f"Decision {record.decision_id}",
        product_id=product.product_id,
        created_date=record.decided_date,
        version="1.0",
        ticket_ref="",
        body="\n".join(lines).strip(),
        referenced_entity_ids=[record.about_entity_id],
    )


def render_meeting_notes(
    note: MeetingNote, product: Product, model: SourceModel,
    rng: random.Random, doc_id: str,
) -> Document:
    """
    Fragmentary notes. The messiest document type in the corpus, and still fully
    model-controlled: the topics are data, the prose is a template.
    """
    lines = [
        f"# Notes - {note.meeting_date}",
        "",
        f"Attendees: {', '.join(note.attendees_role)} | Product: {product.name}",
        "",
        "## Notes",
        "",
    ]
    for topic in note.topics:
        lines.append(f"- {topic}")
    lines += ["", f"Relates to: {', '.join(note.about_entity_ids)}", ""]

    return Document(
        document_id=doc_id,
        source_entity_type="meeting_note",
        source_entity_id=note.note_id,
        doc_type="meeting_notes",
        title=f"Meeting notes {note.meeting_date}",
        product_id=product.product_id,
        created_date=note.meeting_date,
        version="1.0",
        ticket_ref="",
        body="\n".join(lines).strip(),
        referenced_entity_ids=list(note.about_entity_ids),
    )


def render_runbook(
    runbook: Runbook, product: Product, model: SourceModel,
    rng: random.Random, doc_id: str,
) -> Document:
    """Operational documentation for a component. Dense, technical, and mostly
    irrelevant to product queries - a useful distractor class."""
    component = model.get_component(runbook.component_id)
    lines = [
        f"# {runbook.title}",
        "",
        f"Component: {component.name} ({component.component_id}) | "
        f"Type: {component.component_type} | Owner: {component.owner_team} | "
        f"Last reviewed: {runbook.last_reviewed}",
        "",
        component.notes,
        "",
        "## Procedure",
        "",
    ]
    for index, step in enumerate(runbook.steps, start=1):
        lines.append(f"{index}. {step}")

    return Document(
        document_id=doc_id,
        source_entity_type="runbook",
        source_entity_id=runbook.runbook_id,
        doc_type="runbook",
        title=runbook.title,
        product_id=product.product_id,
        created_date=runbook.last_reviewed,
        version="1.0",
        ticket_ref="",
        body="\n".join(lines).strip(),
        referenced_entity_ids=[runbook.component_id],
    )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def render_corpus(model: SourceModel) -> list[Document]:
    """
    Render every document implied by the source model, in a deterministic order.

    Document IDs are assigned here, in a fixed sequence, so that the same model always
    produces the same DOC-xxxx identifiers. That stability is what lets a recorded
    result be checked against a later run.
    """
    rng = random.Random(model.seed)
    documents: list[Document] = []
    counter = 0

    def next_id() -> str:
        nonlocal counter
        counter += 1
        return f"DOC-{counter:04d}"

    for req in model.requirements:
        product = model.get_product(req.product_id)
        documents.append(render_prd(req, product, model, rng, next_id()))

    # Mark version lineage now that PRD ids exist.
    by_entity = {d.source_entity_id: d for d in documents}
    for req in model.requirements:
        if req.supersedes_id:
            newer = by_entity.get(req.requirement_id)
            older = by_entity.get(req.supersedes_id)
            if newer and older:
                older.superseded_by_document_id = newer.document_id

    for feature in model.features:
        product = model.get_product(feature.product_id)
        documents.append(render_feature_spec(feature, product, model, rng, next_id()))

    for pbi in model.pbis:
        product = model.get_product(pbi.product_id)
        documents.append(render_pbi(pbi, product, model, rng, next_id()))

    for ticket in model.tickets:
        product = model.get_product(ticket.product_id)
        documents.append(render_ticket(ticket, product, model, rng, next_id()))

    for record in model.decisions:
        product = model.get_product(record.product_id)
        documents.append(render_decision_log(record, product, model, rng, next_id()))

    for note in model.meeting_notes:
        product = model.get_product(note.product_id)
        documents.append(render_meeting_notes(note, product, model, rng, next_id()))

    for runbook in model.runbooks:
        product = model.get_product(runbook.product_id)
        documents.append(render_runbook(runbook, product, model, rng, next_id()))

    return documents


def summarise(documents: list[Document]) -> dict:
    """Counts per document type, for the dataset manifest."""
    counts: dict[str, int] = {}
    for doc in documents:
        counts[doc.doc_type] = counts.get(doc.doc_type, 0) + 1
    return {
        "total_documents": len(documents),
        "by_doc_type": counts,
        "total_words": sum(len(doc.body.split()) for doc in documents),
    }

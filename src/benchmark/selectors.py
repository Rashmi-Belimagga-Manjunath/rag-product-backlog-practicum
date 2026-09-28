"""
Slot selectors: resolve a query slot to concrete documents, dependencies and entities.

A selector is a PREDICATE over the structured model, not a hard-coded ID list. The final
272-document corpus has different IDs from the mechanism sample, so every selector must
resolve against both. A selector that matches nothing is reported UNRESOLVED and blocks the
freeze - it is never silently dropped, and never satisfied by a fallback pick.

Nothing here reads chunk text or calls a language model. Ground truth is derived from the
model, or it is not ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Resolution:
    """What a slot points at, resolved from the model."""
    selector: str
    document_ids: list = field(default_factory=list)
    entity_ids: list = field(default_factory=list)
    dependency_ids: list = field(default_factory=list)
    distractor_document_ids: list = field(default_factory=list)
    # Conflicts are a separate ID space from entities. A conflict_id placed in
    # entity_ids is a real error: it would resolve against no entity and silently pass a
    # lookup that should fail.
    conflict_ids: list = field(default_factory=list)
    relevance_basis: str = "current"
    expected_dependencies: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    @property
    def resolved(self) -> bool:
        return bool(self.document_ids)

    def problems(self, query_id: str) -> list:
        out = []
        if not self.document_ids:
            out.append(f"{query_id}: selector '{self.selector}' resolved to no document")
        if not (self.entity_ids or self.conflict_ids) and self.relevance_basis != "both":
            out.append(f"{query_id}: neither an entity nor a conflict resolved")
        return out


def _docs(documents, **conditions):
    out = []
    for d in documents:
        if all(getattr(d, k, None) == v for k, v in conditions.items()):
            out.append(d)
    return out


def _links_to(model, document_ids, entity_id):
    return [l for l in model.document_links
            if l.from_document_id in document_ids and l.to_entity_id == entity_id]


# ---------------------------------------------------------------------------
# Information retrieval
# ---------------------------------------------------------------------------

def current_prd(model, documents):
    d = _docs(documents, doc_type="prd", is_current=True)
    return Resolution("current_prd", [x.document_id for x in d],
                      [x.source_entity_id for x in d])


def runbook(model, documents):
    d = _docs(documents, doc_type="runbook")
    return Resolution("runbook", [x.document_id for x in d],
                      [x.source_entity_id for x in d])


def current_feature_spec(model, documents):
    d = _docs(documents, doc_type="feature_spec", is_current=True)
    return Resolution("current_feature_spec", [x.document_id for x in d],
                      [x.source_entity_id for x in d])


def decision_record(model, documents):
    d = _docs(documents, doc_type="decision_log")
    return Resolution("decision_record", [x.document_id for x in d],
                      [x.source_entity_id for x in d])


def informal_ticket(model, documents):
    informal_products = {p.product_id for p in model.products
                         if p.documentation_maturity == "informal"}
    d = [x for x in _docs(documents, doc_type="ticket")
         if x.product_id in informal_products]
    return Resolution("informal_ticket", [x.document_id for x in d],
                      [x.source_entity_id for x in d],
                      notes=["colloquial register; lowest lexical overlap target"])


def current_prd_with_superseded_sibling(model, documents):
    """Q-SUP-1. The superseded PRD is the D5 distractor; the answer is the current one."""
    current = _docs(documents, doc_type="prd", is_current=True)
    superseded = {d.superseded_by for d in documents if not d.is_current and d.superseded_by}
    picks = [d for d in current if d.document_id in superseded]
    if not picks:
        return Resolution("current_prd_with_superseded_sibling")
    chosen = picks[0]
    distractor = next(d.document_id for d in documents
                      if d.superseded_by == chosen.document_id)
    return Resolution(
        "current_prd_with_superseded_sibling",
        [chosen.document_id], [chosen.source_entity_id],
        distractor_document_ids=[distractor],
        notes=[f"D5 distractor: superseded predecessor {distractor}"])


# ---------------------------------------------------------------------------
# Feature context
# ---------------------------------------------------------------------------

def feature_summary(model, documents):
    d = _docs(documents, doc_type="feature_spec", is_current=True)
    return Resolution("feature_summary", [d[0].document_id], [d[0].source_entity_id])


def requirement_statement(model, documents):
    """Target the document that DEFINES a requirement, via the declared `defines` link."""
    defines = [l for l in model.document_links if l.link_type == "defines"
               and l.to_entity_type == "requirement"]
    if not defines:
        return Resolution("requirement_statement")
    requirement_id = defines[0].to_entity_id
    return Resolution("requirement_statement", [defines[0].from_document_id],
                      [requirement_id])


def ruled_out_option(model, documents):
    """A document that explicitly records an option being ruled out."""
    for d in documents:
        body = d.body.lower()
        if any(p in body for p in ("ruled out", "not in scope", "does not cover",
                                   "excluded", "alternative was considered")):
            return Resolution("ruled_out_option", [d.document_id], [d.source_entity_id])
    return Resolution("ruled_out_option")


def current_spec_with_approval_limit(model, documents):
    """
    Q-SUP-3. Needs a feature spec whose approval limit CHANGED between versions.

    Expected to be UNRESOLVED against the mechanism sample: no sample feature has a
    numeric approval limit, and none changed between versions. This is a recorded corpus
    REQUIREMENT, not a defect - the final corpus must supply it or Q-SUP-3 is invalid.
    """
    # An earlier version of this selector compared every number in the two documents and
    # called it an approval limit. It matched the VERSION numbers in the status banner
    # ("Version 1.0" vs "Version 2.0") and the document dates, so Q-SUP-3 falsely resolved
    # to a spec with no limit in it at all. A limit must be stated as a limit: the line
    # must mention a limit AND carry a value that is not a version, date or document ID.
    import re

    def stated_limits(body: str) -> set:
        found = set()
        for line in body.splitlines():
            low = line.lower()
            if "limit" not in low and "threshold" not in low and "cap" not in low:
                continue
            for token in re.findall(r"[A-Za-z]{0,6}\s?[0-9][0-9,.]*", line):
                cleaned = token.strip()
                if re.search(r"\d{4}-\d{2}-\d{2}", cleaned):      # a date
                    continue
                if re.fullmatch(r"v?\d+(\.\d+)?", cleaned) and len(cleaned) <= 5:
                    # a bare small number is usually a version or a step count; require a
                    # currency marker or a magnitude to accept it as a limit value
                    if not re.search(r"[\$£€]\s*" + re.escape(cleaned), line):
                        continue
                found.add(cleaned)
        return found

    superseded_ids = {d.superseded_by for d in documents if not d.is_current and d.superseded_by}
    candidates = [d for d in documents
                  if d.doc_type == "feature_spec" and d.document_id in superseded_ids]
    for current in candidates:
        prior = next(d for d in documents if d.superseded_by == current.document_id)
        now_limits, prior_limits = stated_limits(current.body), stated_limits(prior.body)
        if now_limits and prior_limits and now_limits != prior_limits:
            return Resolution(
                "current_spec_with_approval_limit", [current.document_id],
                [current.source_entity_id], relevance_basis="current",
                distractor_document_ids=[prior.document_id],
                notes=[f"historical limit {sorted(prior_limits)} differs from current "
                       f"{sorted(now_limits)} in {prior.document_id}"])
    return Resolution(
        "current_spec_with_approval_limit",
        notes=["UNRESOLVED: the corpus must contain a feature spec stating an approval "
               "limit or threshold whose VALUE CHANGED between v1 and v2. Absent from the "
               "mechanism sample. Matching on bare numbers would wrongly accept the "
               "version number in the status banner."])


def superseded_spec_with_current_successor(model, documents):
    """Q-SUP-2. The claim lives in a superseded spec; both documents are relevant."""
    superseded = [d for d in documents
                  if d.doc_type == "feature_spec" and not d.is_current and d.superseded_by]
    if not superseded:
        return Resolution("superseded_spec_with_current_successor")
    prior = superseded[0]
    current = next(d for d in documents if d.document_id == prior.superseded_by)
    return Resolution(
        "superseded_spec_with_current_successor",
        [prior.document_id, current.document_id], [current.source_entity_id],
        relevance_basis="both",
        notes=[f"claim stated in superseded {prior.document_id}; authoritative current "
               f"document is {current.document_id}"])


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

def _dep_selector(model, documents, selector, explicitness, predicate, note):
    matches = [d for d in model.dependencies
               if d.explicitness == explicitness and predicate(d)]
    if not matches:
        return Resolution(selector, notes=[f"no {explicitness} dependency matched"])
    dep = matches[0]
    entity_ids = [dep.from_id, dep.to_id]
    document_ids = sorted({
        l.from_document_id for l in model.document_links
        if l.to_entity_id in entity_ids
    })
    return Resolution(selector, document_ids, entity_ids,
                      expected_dependencies=[dep.dependency_id], notes=[note])


def explicit_dep_feature_to_component(model, documents):
    return _dep_selector(model, documents, "explicit_dep_feature_to_component",
                         "explicit",
                         lambda d: d.from_type == "feature" and d.to_type == "component",
                         "stated in prose in the feature specification")


def explicit_dep_component_to_component(model, documents):
    return _dep_selector(model, documents, "explicit_dep_component_to_component",
                         "explicit",
                         lambda d: d.from_type == "component" and d.to_type == "component",
                         "stated in the technical component document")


def explicit_dep_ordering(model, documents):
    return _dep_selector(model, documents, "explicit_dep_ordering", "explicit",
                         lambda d: "order" in d.dependency_type or
                                   "sequence" in d.dependency_type,
                         "explicit ordering constraint between stages")


def explicit_dep_third_party(model, documents):
    return _dep_selector(model, documents, "explicit_dep_third_party", "explicit",
                         lambda d: "external" in d.dependency_type or
                                   "third" in d.description.lower(),
                         "stated dependency on an external party")


def implicit_dep_component(model, documents):
    return _dep_selector(model, documents, "implicit_dep_component", "implicit",
                         lambda d: d.to_type == "component" and d.from_type == "feature",
                         "not stated in prose; encoded in the model, requires context")


def implicit_dep_ordering(model, documents):
    return _dep_selector(model, documents, "implicit_dep_ordering", "implicit",
                         lambda d: "order" in d.dependency_type or
                                   "sequence" in d.dependency_type,
                         "ordering implied by the model, not written down")


def implicit_dep_cross_feature(model, documents):
    return _dep_selector(model, documents, "implicit_dep_cross_feature", "implicit",
                         lambda d: d.from_type == "feature" and d.to_type == "feature",
                         "spans two features; only inferable from context")


def implicit_dep_via_runbook(model, documents):
    """Only textual evidence for the dependency sits in a runbook."""
    runs = [d for d in documents if d.doc_type == "runbook"]
    for d in model.dependencies:
        if d.explicitness != "implicit":
            continue
        if any(l.from_document_id in {r.document_id for r in runs}
               and l.to_entity_id in (d.from_id, d.to_id) for l in model.document_links):
            return Resolution("implicit_dep_via_runbook",
                              [r.document_id for r in runs],
                              [d.from_id, d.to_id],
                              expected_dependencies=[d.dependency_id],
                              notes=["evidence sits in a runbook, not in the feature prose"])
    return Resolution("implicit_dep_via_runbook",
                      notes=["no implicit dependency has runbook evidence"])


# ---------------------------------------------------------------------------
# Cross-document reasoning
# ---------------------------------------------------------------------------

def cdr_single_document(model, documents):
    return _dep_selector(model, documents, "cdr_single_document", "explicit",
                         lambda d: True,
                         "dependency and its target both inside one document")


def cdr_two_documents(model, documents):
    for d in model.dependencies:
        if d.explicitness != "explicit":
            continue
        docs_for = sorted({l.from_document_id for l in model.document_links
                           if l.to_entity_id in (d.from_id, d.to_id)})
        if len(docs_for) >= 2:
            return Resolution("cdr_two_documents", docs_for, [d.from_id, d.to_id],
                              expected_dependencies=[d.dependency_id],
                              notes=["target and dependency are in different documents"])
    return Resolution("cdr_two_documents", notes=["no dependency spans two documents"])


def cdr_meeting_notes(model, documents):
    notes = _docs(documents, doc_type="meeting_notes")
    for d in model.dependencies:
        if d.explicitness != "implicit":
            continue
        if any(l.from_document_id in {n.document_id for n in notes}
               and l.to_entity_id in (d.from_id, d.to_id) for l in model.document_links):
            return Resolution("cdr_meeting_notes", [n.document_id for n in notes],
                              [d.from_id, d.to_id],
                              expected_dependencies=[d.dependency_id],
                              notes=["relationship recoverable from meeting notes"])
    return Resolution("cdr_meeting_notes", notes=["no meeting-note evidence found"])


def cdr_prd_sequence(model, documents):
    _ = documents  # documents are traversed via declared links, not by document type
    for d in model.dependencies:
        if d.explicitness == "implicit" and "order" in d.dependency_type:
            docs_for = sorted({l.from_document_id for l in model.document_links
                               if l.to_entity_id in (d.from_id, d.to_id)})
            if docs_for:
                return Resolution("cdr_prd_sequence", docs_for, [d.from_id, d.to_id],
                                  expected_dependencies=[d.dependency_id],
                                  notes=["ordering inferred from PRD sequence"])
    # No implicit ordering dependency exists in this model. Return nothing rather than
    # substituting current PRDs: a fallback pick would make the slot look resolved and
    # hide a corpus requirement, which is exactly the failure this gate exists to catch.
    return Resolution("cdr_prd_sequence", [],
                      notes=["no implicit ordering dependency matched"])


def cdr_via_superseded_document(model, documents):
    superseded = [d.document_id for d in documents if not d.is_current]
    for d in model.dependencies:
        if d.explicitness != "implicit":
            continue
        docs_for = {l.from_document_id for l in model.document_links
                    if l.to_entity_id in (d.from_id, d.to_id)}
        overlap = docs_for & set(superseded)
        if overlap:
            return Resolution("cdr_via_superseded_document", sorted(docs_for),
                              [d.from_id, d.to_id],
                              expected_dependencies=[d.dependency_id],
                              distractor_document_ids=[],
                              notes=[f"evidence in superseded {sorted(overlap)}"])
    return Resolution("cdr_via_superseded_document",
                      notes=["no implicit dependency has superseded-document evidence"])


# ---------------------------------------------------------------------------
# Conflicts
# ---------------------------------------------------------------------------

def _conflict_selector(model, documents, selector, predicate, note):
    for c in model.conflicts:
        if predicate(c):
            docs = [c.document_a_id, c.document_b_id]
            if c.resolved_by_document_id:
                docs.append(c.resolved_by_document_id)
            return Resolution(selector, sorted(set(docs)),
                              conflict_ids=[c.conflict_id], notes=[note])
    return Resolution(selector, notes=[f"no conflict matched: {note}"])


def conflict_resolved(model, documents):
    return _conflict_selector(model, documents, "conflict_resolved",
                              lambda c: c.is_resolved, "resolved conflict")


def conflict_unresolved(model, documents):
    return _conflict_selector(model, documents, "conflict_unresolved",
                              lambda c: not c.is_resolved, "unresolved conflict")


def conflict_resolved_in_later_version(model, documents):
    return _conflict_selector(
        model, documents, "conflict_resolved_in_later_version",
        lambda c: c.is_resolved and c.resolved_by_document_id in
                  {d.superseded_by for d in documents if not d.is_current},
        "resolution recorded only in a later document version")


# ---------------------------------------------------------------------------
# Backlog analysis - documented rationale, requirements, priority/context.
# Deliberately NOT dependency selectors.
# ---------------------------------------------------------------------------

def backlog_prioritisation_decision(model, documents):
    d = _docs(documents, doc_type="decision_log")
    return Resolution("backlog_prioritisation_decision", [x.document_id for x in d],
                      [x.source_entity_id for x in d],
                      notes=["documented prioritisation decision, not a dependency question"])


def backlog_non_goal(model, documents):
    for x in documents:
        if "non-goal" in x.body.lower():
            return Resolution("backlog_non_goal", [x.document_id], [x.source_entity_id],
                              notes=["stated non-goal"])
    return Resolution("backlog_non_goal", notes=["no non-goal section found"])


def backlog_changed_decision_rationale(model, documents):
    superseded = [d for d in documents if not d.is_current and d.superseded_by]
    if superseded:
        prior = superseded[0]
        current = next(d for d in documents if d.document_id == prior.superseded_by)
        return Resolution("backlog_changed_decision_rationale",
                          [prior.document_id, current.document_id],
                          [current.source_entity_id], relevance_basis="both",
                          notes=["rationale behind a changed decision"])
    return Resolution("backlog_changed_decision_rationale",
                      notes=["no superseded document to compare"])


def backlog_deprioritised_rationale(model, documents):
    for d in model.pbis:
        if any(w in d.status.lower() for w in ("deprior", "later", "backlog", "hold")):
            return Resolution("backlog_deprioritised_rationale",
                              [f"DOC-{d.pbi_id}"], [d.pbi_id],
                              notes=[f"status '{d.status}' documents the deferral"])
    for x in _docs(documents, doc_type="decision_log"):
        if any(w in x.body.lower() for w in ("deprior", "not now", "later", "backlog")):
            return Resolution("backlog_deprioritised_rationale", [x.document_id],
                              [x.source_entity_id], notes=["deprioritisation documented"])
    return Resolution("backlog_deprioritised_rationale",
                      notes=["no deprioritisation rationale found"])


def backlog_synthesis(model, documents):
    specs = _docs(documents, doc_type="feature_spec", is_current=True)
    decisions = _docs(documents, doc_type="decision_log")
    if specs and decisions:
        return Resolution("backlog_synthesis",
                          [specs[0].document_id, decisions[0].document_id],
                          [specs[0].source_entity_id, decisions[0].source_entity_id],
                          notes=["synthesis across a feature and its decision record"])
    return Resolution("backlog_synthesis", notes=["insufficient documents"])


SELECTORS: dict = {f.__name__: f for f in (
    current_prd, runbook, current_feature_spec, decision_record, informal_ticket,
    current_prd_with_superseded_sibling,
    feature_summary, requirement_statement, ruled_out_option,
    current_spec_with_approval_limit, superseded_spec_with_current_successor,
    explicit_dep_feature_to_component, explicit_dep_component_to_component,
    explicit_dep_ordering, explicit_dep_third_party,
    implicit_dep_component, implicit_dep_ordering, implicit_dep_cross_feature,
    implicit_dep_via_runbook,
    cdr_single_document, cdr_two_documents, cdr_meeting_notes, cdr_prd_sequence,
    cdr_via_superseded_document,
    conflict_resolved, conflict_unresolved, conflict_resolved_in_later_version,
    backlog_prioritisation_decision, backlog_non_goal,
    backlog_changed_decision_rationale, backlog_deprioritised_rationale,
    backlog_synthesis,
)}


def resolve_slot(slot, model, documents) -> Resolution:
    selector = SELECTORS.get(slot.selector)
    if selector is None:
        return Resolution(slot.selector, notes=[f"no selector implementation "
                                               f"named '{slot.selector}'"])
    return selector(model, documents)

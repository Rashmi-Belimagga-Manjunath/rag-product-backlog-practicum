"""
D-013 amendments: ordering dependency vocabulary and approval-limit feature specs.

These three gates were unsatisfiable under the frozen `be92946` definitions and were the
reason final-corpus generation STOPPED:

- Q-11 / Q-14 selectors match `"order" in dependency_type or "sequence" in dependency_type`;
- Q-20's `cdr_prd_sequence` matches `"order" in dependency_type`;
- Q-SUP-3 needs a v1/v2 feature-spec pair whose stated approval limit CHANGED, but the
  schema had no limit field and the renderer emitted no limit text.

D-013 extends the vocabulary with `ordering` and gives `Feature` an `approval_limit`.
These tests prove each gate is now satisfiable by corpus content, without touching the
selectors or the 32-query spec. The mechanism sample is deliberately unchanged: it still
carries no ordering dependency and no approval limit.
"""

from __future__ import annotations

from typing import get_args

from src.benchmark.query_spec import Q_SUP_3, SLOTS
from src.benchmark.selectors import SELECTORS, resolve_slot
from src.data_generation.render_v1 import render_corpus
from src.data_generation.source_model import (
    Conflict,
    Dependency,
    DependencyType,
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
from src.data_generation.v1_sample import document_id_for


def _mini_products() -> dict[str, Product]:
    return {
        "M": Product(product_id="PROD-M", name="Meridian", domain="HRTech",
                     documentation_maturity="formal", team_size=14),
        "T": Product(product_id="PROD-T", name="Tally", domain="Habits",
                     documentation_maturity="informal", team_size=5),
    }


def _feature(fid: str, doc: str, version: str, is_current: bool,
             approval_limit: str = "") -> Feature:
    return Feature(
        feature_id=fid, product_id="PROD-M", name=f"{fid} feature", status="planned",
        priority=1, formal_term=f"{fid} formal term", colloquial_terms=["c1", "c2"],
        summary=f"{fid} summary fact.", confusable_with=[], requirement_id=f"REQ-{fid[5:]}",
        document_id=doc, version=version,
        version_status="current" if is_current else "superseded",
        created_date="2026-01-01", modified_date="2026-02-01",
        superseded_by="" if is_current else doc + "-v2",
        supersedes=doc + "-v1" if is_current else "", is_current=is_current,
        approval_limit=approval_limit,
    )


def _base_model() -> SourceModel:
    products = _mini_products()
    model = SourceModel(model_version="probe", seed=1, created_date="2026-01-01",
                        products=list(products.values()))
    return model


# ------------------------------------------------------------------- vocabulary

def test_dependency_type_vocabulary_gained_ordering():
    assert "ordering" in get_args(DependencyType)


def test_ordering_value_matches_every_frozen_ordering_selector():
    # The Q-11/Q-14 predicates and Q-20's cdr_prd_sequence predicate can now match.
    assert ("order" in "ordering") or ("sequence" in "ordering")
    assert "order" in "ordering"


# ---------------------------------------------------------------- Q-11 / Q-14

def _model_with_ordering(explicitness: str, feature_ids: list[str]) -> SourceModel:
    model = _base_model()
    m = model
    m.features = [_feature(fid, f"DOC-{fid}", "1.0", True) for fid in feature_ids]
    m.prds = [Prd(prd_id="PRD-M-01", product_id="PROD-M", title="t", author_role="PM",
                  is_normative=True, summary="s", sections=["Background", "Requirements"],
                  requirement_ids=[f"REQ-{fid[5:]}" for fid in feature_ids],
                  document_id="DOC-PRD-M-01", version="1.0", version_status="current",
                  created_date="2026-01-01", modified_date="2026-01-01",
                  superseded_by="", supersedes="", is_current=True)]
    m.requirements = [Requirement(requirement_id=f"REQ-{fid[5:]}", prd_id="PRD-M-01",
                                  product_id="PROD-M", title=f"req for {fid}",
                                  statement=f"{fid} requirement statement.", is_normative=True)
                      for fid in feature_ids]
    m.dependencies = [
        Dependency(dependency_id="DEP-501", from_type="feature", from_id=feature_ids[0],
                   to_type="feature", to_id=feature_ids[1], dependency_type="ordering",
                   description="Stage one must finish before stage two begins.",
                   explicitness=explicitness),
    ]
    m.conflicts = []
    links = []
    for p in m.prds:
        for rid in p.requirement_ids:
            links.append(DocumentLink(link_id=f"LNK-{len(links) + 1:04d}",
                                      from_document_id=p.document_id,
                                      to_entity_type="requirement", to_entity_id=rid,
                                      link_type="defines"))
    for f in m.features:
        links.append(DocumentLink(link_id=f"LNK-{len(links) + 1:04d}",
                                  from_document_id=f.document_id, to_entity_type="product",
                                  to_entity_id=f.product_id, link_type="defines"))
    # each feature must be the target of at least one link, or the dependency selectors
    # resolve the entity IDs to zero documents (they collect links targeting the entity)
    for f in m.features:
        links.append(DocumentLink(link_id=f"LNK-{len(links) + 1:04d}",
                                  from_document_id=f"DOC-PBI-{f.feature_id}",
                                  to_entity_type="feature", to_entity_id=f.feature_id,
                                  link_type="implements"))
    m.document_links = links
    return m


def test_explicit_ordering_dependency_resolves_q11():
    model = _model_with_ordering("explicit", ["FEAT-A-01", "FEAT-A-02"])
    docs = render_corpus(model)
    r = SELECTORS["explicit_dep_ordering"](model, docs)
    assert r.document_ids
    assert r.entity_ids == ["FEAT-A-01", "FEAT-A-02"]
    assert {s.query_id for s in SLOTS if s.selector == "explicit_dep_ordering"} == {"Q-11"}


def test_implicit_ordering_dependency_resolves_q14():
    model = _model_with_ordering("implicit", ["FEAT-A-01", "FEAT-A-02"])
    docs = render_corpus(model)
    r = SELECTORS["implicit_dep_ordering"](model, docs)
    assert r.document_ids
    assert r.entity_ids == ["FEAT-A-01", "FEAT-A-02"]


def test_implicit_ordering_dependency_resolves_q20():
    model = _model_with_ordering("implicit", ["FEAT-A-01", "FEAT-A-02"])
    docs = render_corpus(model)
    r = SELECTORS["cdr_prd_sequence"](model, docs)
    assert r.document_ids
    assert r.expected_dependencies == ["DEP-501"]


def test_ordering_gates_resolve_through_resolve_slot():
    for explicitness, query_id in (("explicit", "Q-11"), ("implicit", "Q-14")):
        model = _model_with_ordering(explicitness, ["FEAT-A-01", "FEAT-A-02"])
        docs = render_corpus(model)
        slot = next(s for s in SLOTS if s.query_id == query_id)
        r = resolve_slot(slot, model, docs)
        assert r.document_ids, f"{query_id} must resolve on corpus content"


# ------------------------------------------------------------ Q-SUP-3 approval limit

def _approval_limit_pair(low: str, high: str) -> SourceModel:
    model = _base_model()
    m = model
    v1 = _feature("FEAT-A-01", "DOC-FEAT-A-01", "1.0", False, approval_limit=low)
    v2 = _feature("FEAT-A-01", "DOC-FEAT-A-01-v2", "2.0", True, approval_limit=high)
    m.features = [v1, v2]
    m.prds = [Prd(prd_id="PRD-M-01", product_id="PROD-M", title="t", author_role="PM",
                  is_normative=True, summary="s", sections=["Background"],
                  requirement_ids=["REQ-A-01"], document_id="DOC-PRD-M-01", version="1.0",
                  version_status="current", created_date="2026-01-01",
                  modified_date="2026-01-01", superseded_by="", supersedes="", is_current=True)]
    m.requirements = [Requirement(requirement_id="REQ-A-01", prd_id="PRD-M-01",
                                  product_id="PROD-M", title="req",
                                  statement="requirement statement.", is_normative=True)]
    m.dependencies = []
    m.conflicts = []
    links = [
        DocumentLink(link_id="LNK-0001", from_document_id="DOC-PRD-M-01",
                     to_entity_type="requirement", to_entity_id="REQ-A-01",
                     link_type="defines"),
        DocumentLink(link_id="LNK-0002", from_document_id="DOC-FEAT-A-01",
                     to_entity_type="product", to_entity_id="PROD-M", link_type="defines"),
        DocumentLink(link_id="LNK-0003", from_document_id="DOC-FEAT-A-01-v2",
                     to_entity_type="product", to_entity_id="PROD-M", link_type="defines"),
    ]
    m.document_links = links
    return m


def test_approval_limit_pair_resolves_q_sup_3():
    model = _approval_limit_pair("$2,500", "$5,000")
    docs = render_corpus(model)
    by_id = docs_by_id = {d.document_id: d for d in docs}
    # both bodies must state a limit explicitly (the bare-number trap the selector rejects)
    assert "approval limit" in by_id["DOC-FEAT-A-01"].body.lower()
    assert "$2,500" in by_id["DOC-FEAT-A-01"].body
    assert "$5,000" in by_id["DOC-FEAT-A-01-v2"].body
    r = SELECTORS["current_spec_with_approval_limit"](model, docs)
    assert r.document_ids == ["DOC-FEAT-A-01-v2"]
    assert docs_by_id["DOC-FEAT-A-01"].document_id in r.distractor_document_ids
    assert Q_SUP_3 == "What is the current approval limit?"


def test_approval_limit_only_renders_when_corpus_states_one():
    model = _base_model()
    f = _feature("FEAT-A-01", "DOC-FEAT-A-01", "1.0", True)
    model.features = [f]
    model.prds = [Prd(prd_id="PRD-M-01", product_id="PROD-M", title="t", author_role="PM",
                      is_normative=True, summary="s", sections=["Background"],
                      requirement_ids=["REQ-A-01"], document_id="DOC-PRD-M-01", version="1.0",
                      version_status="current", created_date="2026-01-01",
                      modified_date="2026-01-01", superseded_by="", supersedes="",
                      is_current=True)]
    model.requirements = [Requirement(requirement_id="REQ-A-01", prd_id="PRD-M-01",
                                      product_id="PROD-M", title="req",
                                      statement="requirement statement.", is_normative=True)]
    model.dependencies = []
    model.conflicts = []
    model.document_links = [
        DocumentLink(link_id="LNK-0001", from_document_id="DOC-PRD-M-01",
                     to_entity_type="requirement", to_entity_id="REQ-A-01",
                     link_type="defines"),
        DocumentLink(link_id="LNK-0002", from_document_id="DOC-FEAT-A-01",
                     to_entity_type="product", to_entity_id="PROD-M", link_type="defines"),
    ]
    docs = render_corpus(model)
    assert "Approval limit" not in docs[0].body
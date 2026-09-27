"""
A SMALL sample source model, for design review only.

This is NOT the final corpus. It exists so the schema, the rendering behaviour, and the
ground-truth derivation can be inspected and agreed before anything is generated at
scale. Decisions D6 (corpus scale) and D7 (query distribution) are still open and depend
on what this sample reveals.

The sample is deliberately built to exercise every feature the design depends on:
  - one formal product and one informal product (CA2 section 3 contrast)
  - a superseded PRD version left in the repository (stale distractor)
  - explicit and implicit dependencies (the split that makes a real finding possible)
  - a resolved conflict and an unresolved one
  - a duplicate PBI pair (a classic real-world waste of effort)
  - a third-party component, i.e. a dependency the team does not control
  - every document type in the proposed mix
"""

from __future__ import annotations

from .source_model import (
    SourceModel, Product, Feature, Requirement, Pbi, TechnicalComponent,
    Ticket, DecisionRecord, MeetingNote, Runbook, Dependency, Conflict,
)

SEED = 20260927
TODAY = "2026-09-27"


def build_sample_model() -> SourceModel:
    """Construct the small sample. Every value below is data, not prose - the renderer
    turns it into documents."""

    products = [
        Product(
            product_id="PROD-A",
            name="Meridian",
            domain="B2B workforce analytics",
            documentation_maturity="formal",
            team_size=24,
        ),
        Product(
            product_id="PROD-B",
            name="Tally",
            domain="consumer habit tracking",
            documentation_maturity="informal",
            team_size=4,
        ),
    ]

    features = [
        Feature(
            feature_id="FEAT-A-01",
            product_id="PROD-A",
            name="Progressive Profiling",
            status="in_progress",
            priority=1,
            formal_term="Progressive Profiling",
            # These informal phrasings are the lexical-divergence control. They are what
            # a ticket or a meeting will say instead of the formal term.
            colloquial_terms=["onboarding ramp", "new-user activation", "first-run setup"],
            summary=(
                "Collect profile attributes across the first several sessions instead of "
                "requesting everything on the first screen."
            ),
        ),
        Feature(
            feature_id="FEAT-A-02",
            product_id="PROD-A",
            name="Bulk Timesheet Approval",
            status="planned",
            priority=2,
            formal_term="Bulk Timesheet Approval",
            colloquial_terms=["batch timesheet sign-off", "approving hours in bulk"],
            summary=(
                "Let an administrator approve many submitted timesheets in a single action."
            ),
        ),
        Feature(
            feature_id="FEAT-B-01",
            product_id="PROD-B",
            name="Streak Rescue",
            status="in_progress",
            priority=1,
            formal_term="Streak Recovery Suggestion Engine",
            colloquial_terms=["streak saver", "saving a broken streak", "losing a streak"],
            summary=(
                "Detect a streak that is about to break and offer the user a way to keep it."
            ),
        ),
    ]

    requirements = [
        # An older version, deliberately left in the repository. Its presence is what
        # lets us test whether a retrieval system surfaces stale content.
        Requirement(
            requirement_id="REQ-A-01",
            product_id="PROD-A",
            title="Progressive Profiling for New Tenants",
            version="1.0",
            author_role="Group Product Manager",
            created_date="2026-02-11",
            feature_ids=["FEAT-A-01"],
            is_normative=False,
            is_superseded=True,
            supersedes_id="",
            summary=(
                "Reduce time-to-value for new tenants by deferring non-essential profile "
                "questions out of the first session."
            ),
            sections=[
                "Background", "Goals", "Non-goals", "Requirements",
                "Dependencies", "Risks",
            ],
        ),
        Requirement(
            requirement_id="REQ-A-02",
            product_id="PROD-A",
            title="Progressive Profiling for New Tenants",
            version="2.0",
            author_role="Group Product Manager",
            created_date="2026-06-30",
            feature_ids=["FEAT-A-01"],
            is_normative=True,
            is_superseded=False,
            supersedes_id="REQ-A-01",
            summary=(
                "Reduce time-to-value for new tenants by deferring non-essential profile "
                "questions out of the first session, and capture partial progress so it is "
                "not lost when a user abandons a session."
            ),
            sections=[
                "Background", "Goals", "Non-goals", "Requirements",
                "Dependencies", "Risks", "Open questions",
            ],
        ),
        Requirement(
            requirement_id="REQ-B-01",
            product_id="PROD-B",
            title="Streak Recovery Policy",
            version="1.0",
            author_role="Product Owner",
            created_date="2026-05-18",
            feature_ids=["FEAT-B-01"],
            is_normative=True,
            is_superseded=False,
            supersedes_id="",
            summary=(
                "A user who has already lost a streak may restore it once per calendar "
                "month at no cost."
            ),
            sections=["Background", "Policy", "Requirements", "Dependencies"],
        ),
    ]

    pbis = [
        Pbi(
            pbi_id="PBI-A-011", product_id="PROD-A", feature_id="FEAT-A-01",
            title="Ask for tax details during the first session",
            description=(
                "Currently we ask for tax details before anyone has seen any value, and "
                "people bounce. Move the question later in the ramp."
            ),
            story_points=5, status="in_progress", created_date="2026-07-14",
            author_role="Product Owner",
            formal_term="Deferred Tax Detail Capture",
            colloquial_terms=["tax question too early", "asking for tax details up front"],
        ),
        Pbi(
            pbi_id="PBI-A-012", product_id="PROD-A", feature_id="FEAT-A-01",
            title="Save partial profile when a user abandons the session",
            description=(
                "If someone leaves halfway through the ramp we throw their answers away. "
                "Keep them and pick up where they left off."
            ),
            story_points=8, status="to_do", created_date="2026-08-02",
            author_role="Product Owner",
            formal_term="Partial Profile Persistence",
            colloquial_terms=["losing answers", "throw away what they typed"],
        ),
        Pbi(
            pbi_id="PBI-A-013", product_id="PROD-A", feature_id="FEAT-A-02",
            title="Approve 20 or more timesheets in one action",
            description=(
                "Managers are approving timesheets one at a time. Needs a bulk action."
            ),
            story_points=3, status="to_do", created_date="2026-08-19",
            author_role="Product Owner",
            formal_term="Bulk Timesheet Approval",
            colloquial_terms=["approving hours in bulk", "batch sign-off"],
        ),
        Pbi(
            pbi_id="PBI-B-021", product_id="PROD-B", feature_id="FEAT-B-01",
            title="Offer a freeze before a streak breaks",
            description=(
                "Show an option to hold the streak when it is about to lapse."
            ),
            story_points=3, status="in_review", created_date="2026-06-08",
            author_role="Product Owner",
            formal_term="Streak Freeze Offer",
            colloquial_terms=["saving a broken streak", "streak saver"],
        ),
        Pbi(
            pbi_id="PBI-B-022", product_id="PROD-B", feature_id="FEAT-B-01",
            title="Let people restore a streak they already lost",
            description=(
                "One free restore per month, per the written policy."
            ),
            story_points=5, status="to_do", created_date="2026-07-30",
            author_role="Product Owner",
            formal_term="Streak Restoration",
            colloquial_terms=["get my streak back", "undo a lost streak"],
        ),
    ]

    components = [
        TechnicalComponent(
            component_id="COMP-A-01", name="Identity Service",
            component_type="service", owner_team="Platform Team",
            notes="Handles authentication and session issuance for all tenants.",
        ),
        TechnicalComponent(
            component_id="COMP-A-02", name="Tenant Config Store",
            component_type="database", owner_team="Platform Team",
            notes="Stores per-tenant configuration, including which profile questions are pending.",
        ),
        TechnicalComponent(
            component_id="COMP-B-01", name="Push Relay",
            component_type="third_party", owner_team="Vendor Team",
            notes="Third-party push notification relay. Delivery is not guaranteed by our SLA.",
        ),
        TechnicalComponent(
            component_id="COMP-B-02", name="Event Bus",
            component_type="queue", owner_team="Platform Team",
            notes="Internal event backbone.",
        ),
    ]

    tickets = [
        Ticket(
            ticket_id="TKT-104", product_id="PROD-A", feature_id="FEAT-A-01",
            related_component_id="COMP-A-01",
            reported_symptom=(
                "New signups get asked for tax details straight away and a lot of them "
                "never come back."
            ),
            customer_segment="mid-market HR teams", severity="high",
            opened_date="2026-08-25", reporter_role="Customer Success Manager",
        ),
        Ticket(
            ticket_id="TKT-109", product_id="PROD-B", feature_id="FEAT-B-01",
            related_component_id="COMP-B-01",
            reported_symptom=(
                "People are upset that they cannot get a streak back after it already broke. "
                "They did not know there was a freeze."
            ),
            customer_segment="consumer app reviews", severity="medium",
            opened_date="2026-08-11", reporter_role="Support Agent",
        ),
    ]

    decisions = [
        DecisionRecord(
            decision_id="DEC-01", product_id="PROD-A", about_entity_id="FEAT-A-01",
            decision=(
                "We will not ask for optional profile attributes in the first session."
            ),
            rationale=(
                "Analytics from the first quarter showed abandonment concentrated on the "
                "first-run setup screen, and optional attributes were the largest contributor."
            ),
            decided_date="2026-06-24", decided_by_role="Group Product Manager",
        ),
        DecisionRecord(
            decision_id="DEC-02", product_id="PROD-B", about_entity_id="FEAT-B-01",
            decision=(
                "A freeze is offered proactively, not only after the streak has broken."
            ),
            rationale=(
                "Post-hoc restore reads as a penalty. Offering it in advance does not."
            ),
            decided_date="2026-06-01", decided_by_role="Product Owner",
        ),
    ]

    meeting_notes = [
        MeetingNote(
            note_id="NOTE-01", product_id="PROD-A",
            about_entity_ids=["FEAT-A-01", "PBI-A-012"],
            meeting_date="2026-08-28",
            attendees_role=["Product Owner", "Tech Lead", "Designer"],
            topics=[
                "losing answers when someone drops out of the ramp is the top complaint",
                "decided to persist partial profile rather than re-ask",
                "still open: how long do we keep a partial profile before discarding it",
            ],
        ),
        MeetingNote(
            note_id="NOTE-02", product_id="PROD-B",
            about_entity_ids=["FEAT-B-01", "PBI-B-021", "PBI-B-022"],
            meeting_date="2026-08-15",
            attendees_role=["Product Owner", "Engineer"],
            topics=[
                "two tickets look like the same thing, need to check before we build twice",
                "push relay is flaky, cannot rely on it for time-critical messages",
            ],
        ),
    ]

    runbooks = [
        Runbook(
            runbook_id="RBK-01", product_id="PROD-B", component_id="COMP-B-01",
            title="Push Relay delivery failure runbook",
            steps=[
                "Check relay status page for an active incident.",
                "Confirm the tenant's device token is still valid in the config store.",
                "If the relay is degraded, fall back to in-app messaging.",
                "Record the incident window for the weekly reliability review.",
            ],
            last_reviewed="2026-07-30",
        ),
    ]

    dependencies = [
        # Explicit: stated in a document, so keyword search can find it.
        Dependency(
            dependency_id="DEP-001",
            from_type="feature", from_id="FEAT-A-01",
            to_type="component", to_id="COMP-A-01",
            dependency_type="depends_on",
            description=(
                "Progressive Profiling depends on the Identity Service for session-scoped "
                "tenant context."
            ),
            is_explicit_in_docs=True,
        ),
        # Implicit: follows from the model, but no document spells it out. Only
        # semantic reasoning recovers this. This is where a real finding is most likely.
        Dependency(
            dependency_id="DEP-002",
            from_type="pbi", from_id="PBI-A-011",
            to_type="component", to_id="COMP-A-02",
            dependency_type="depends_on",
            description=(
                "PBI-A-011 depends on the Tenant Config Store, because deferring the tax "
                "question requires persisting which questions are still pending per tenant."
            ),
            is_explicit_in_docs=False,
        ),
        Dependency(
            dependency_id="DEP-003",
            from_type="requirement", from_id="REQ-A-02",
            to_type="component", to_id="COMP-A-01",
            dependency_type="depends_on",
            description=(
                "REQ-A-02 depends on the Identity Service for per-session tenant context."
            ),
            is_explicit_in_docs=True,
        ),
        Dependency(
            dependency_id="DEP-004",
            from_type="pbi", from_id="PBI-A-013",
            to_type="feature", to_id="FEAT-A-01",
            dependency_type="depends_on",
            description=(
                "Bulk Timesheet Approval depends on Progressive Profiling, because the "
                "approval screen shows profile completeness and cannot be built before "
                "the ramp exists."
            ),
            is_explicit_in_docs=False,
        ),
        Dependency(
            dependency_id="DEP-005",
            from_type="pbi", from_id="PBI-B-021",
            to_type="component", to_id="COMP-B-01",
            dependency_type="depends_on",
            description=(
                "PBI-B-021 depends on the Push Relay, which is a third party and outside "
                "the product team's control."
            ),
            is_explicit_in_docs=True,
        ),
        # A duplicate pair. Real teams genuinely build the same thing twice.
        Dependency(
            dependency_id="DEP-006",
            from_type="pbi", from_id="PBI-B-022",
            to_type="pbi", to_id="PBI-B-021",
            dependency_type="duplicates",
            description=(
                "PBI-B-022 and PBI-B-021 substantially duplicate each other. Both concern "
                "recovering a broken streak, and they may be the same work."
            ),
            is_explicit_in_docs=True,
        ),
        Dependency(
            dependency_id="DEP-007",
            from_type="pbi", from_id="PBI-B-022",
            to_type="component", to_id="COMP-B-02",
            dependency_type="depends_on",
            description=(
                "PBI-B-022 depends on the Event Bus to publish a streak-restored event."
            ),
            is_explicit_in_docs=False,
        ),
    ]

    conflicts = [
        Conflict(
            conflict_id="CONF-01",
            product_id="PROD-A",
            document_a_id="REQ-A-01",
            document_b_id="REQ-A-02",
            conflict_type="superseded_version",
            description=(
                "REQ-A-01 v1.0 and REQ-A-02 v2.0 describe the same feature with different "
                "scope. v1.0 omits partial-progress capture."
            ),
            is_resolved=True,
            resolution_note="REQ-A-02 v2.0 is authoritative.",
            resolved_by_document_id="REQ-A-02",
        ),
        # Unresolved on purpose. An unresolved conflict is a harder query type and
        # tests whether a system can distinguish "these disagree" from "this is wrong".
        Conflict(
            conflict_id="CONF-02",
            product_id="PROD-B",
            document_a_id="REQ-B-01",
            document_b_id="PBI-B-022",
            conflict_type="scope_mismatch",
            description=(
                "REQ-B-01 states a one-free-restore-per-month policy. PBI-B-022 describes "
                "restoration without stating the monthly limit, and PBI-B-021 describes a "
                "freeze that the policy does not mention."
            ),
            is_resolved=False,
            resolution_note="",
            resolved_by_document_id="",
        ),
    ]

    return SourceModel(
        model_version="v0-sample",
        seed=SEED,
        created_date=TODAY,
        products=products,
        features=features,
        requirements=requirements,
        pbis=pbis,
        components=components,
        tickets=tickets,
        decisions=decisions,
        meeting_notes=meeting_notes,
        runbooks=runbooks,
        dependencies=dependencies,
        conflicts=conflicts,
    )

"""
Structured source-of-truth SAMPLE for the final schema.

WHAT THIS IS
------------
A deliberately small model whose only job is to exercise every mechanism in the approved
final schema, so that the schema can be verified before scaling to 272 documents. It is
NOT a preview of the full corpus and its counts mean nothing.

It deliberately includes:
  - a formally-documented and an informally-documented product (the CA2 section 3 control)
  - a superseded PRD and superseded feature specs, exercising is_current / superseded_by
  - the exact version scenario Q-SUP-2 turns on: an OLD spec says tax is collected at
    first login, the CURRENT spec says it is collected later
  - explicit AND implicit dependencies
  - declared distractor relationships (confusable_with, adjacent_component_ids,
    contextualises links) so D1/D2/D3 are facts in the model rather than coincidences
  - one resolved and one unresolved conflict
  - all eight document types
  - all six link types
"""

from __future__ import annotations

from .source_model import (
    Conflict,
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

CREATED = "2026-09-28"


def document_id_for(primary_id: str, version: str = "") -> str:
    """Stable document ID derived from entity identity, never from render order.

    Version 1 renders as DOC-<primary_id>; later versions append -v<N>. Because the ID is
    a function of identity, adding or reordering a document cannot renumber anything, so
    a chunk ID recorded in an earlier result still resolves.
    """
    if version and version != "1.0":
        return f"DOC-{primary_id}-v{version.split('.')[0]}"
    return f"DOC-{primary_id}"


def build_mechanism_sample() -> SourceModel:
    products = [
        Product(
            product_id="PROD-A", name="Meridian", domain="HRTech",
            documentation_maturity="formal", team_size=14,
        ),
        Product(
            product_id="PROD-B", name="Tally", domain="Consumer habit-tracking",
            documentation_maturity="informal", team_size=5,
        ),
    ]

    # -- features (versioned: each renders one feature_spec document) ----------
    # FEAT-A-01 has a v1 and a v2, so the lineage and the Q-SUP-2 scenario are both
    # present in the sample rather than only in the specification.
    features = [
        Feature(
            feature_id="FEAT-A-01", product_id="PROD-A",
            name="Progressive Profiling", status="launched", priority=1,
            formal_term="Progressive Profiling",
            colloquial_terms=["onboarding ramp", "new-user activation", "first-run setup"],
            summary="Collects additional employee details progressively after first login "
                    "rather than in a single mandatory form.",
            confusable_with=["FEAT-A-02", "FEAT-A-04"],
            requirement_id="REQ-A-01",
            document_id=document_id_for("FEAT-A-01", "1.0"),
            version="1.0", version_status="superseded",
            created_date="2026-02-10", modified_date="2026-02-10",
            superseded_by=document_id_for("FEAT-A-01", "2.0"),
            supersedes="", is_current=False,
        ),
        Feature(
            feature_id="FEAT-A-01", product_id="PROD-A",
            name="Progressive Profiling", status="launched", priority=1,
            formal_term="Progressive Profiling",
            colloquial_terms=["onboarding ramp", "new-user activation", "first-run setup"],
            summary="Collects additional employee details progressively after first login "
                    "rather than in a single mandatory form.",
            confusable_with=["FEAT-A-02", "FEAT-A-04"],
            requirement_id="REQ-A-01",
            document_id=document_id_for("FEAT-A-01", "2.0"),
            version="2.0", version_status="current",
            created_date="2026-02-10", modified_date="2026-07-22",
            superseded_by="", supersedes=document_id_for("FEAT-A-01", "1.0"),
            is_current=True,
        ),
        Feature(
            feature_id="FEAT-A-02", product_id="PROD-A",
            name="Identity Verification Window", status="launched", priority=2,
            formal_term="Identity Verification Window",
            colloquial_terms=["ID check stage", "KYC prompt", "the verification pop-up"],
            summary="Requires identity document verification before an employee can be "
                    "granted payment privileges.",
            confusable_with=["FEAT-A-01", "FEAT-A-03"],
            requirement_id="REQ-A-02",
            document_id=document_id_for("FEAT-A-02"),
            version="1.0", version_status="current", created_date="2026-03-04", modified_date="2026-03-04",
            superseded_by="", supersedes="", is_current=True,
        ),
        Feature(
            feature_id="FEAT-A-03", product_id="PROD-A",
            name="Bulk Timesheet Approval", status="in_progress", priority=3,
            formal_term="Bulk Timesheet Approval",
            colloquial_terms=["batch timesheet sign-off", "approving hours in bulk"],
            summary="Allows a manager to approve multiple submitted timesheets in a "
                    "single action.",
            confusable_with=["FEAT-A-02", "FEAT-A-04"],
            requirement_id="REQ-A-03",
            document_id=document_id_for("FEAT-A-03"),
            version="1.0", version_status="current", created_date="2026-04-18", modified_date="2026-04-18",
            superseded_by="", supersedes="", is_current=True,
        ),
        Feature(
            feature_id="FEAT-A-04", product_id="PROD-A",
            name="Payroll Export Scheduling", status="planned", priority=4,
            formal_term="Payroll Export Scheduling",
            colloquial_terms=["automated payroll file", "scheduled payslip dump"],
            summary="Schedules recurring export of payroll data to third-party payroll "
                    "providers in a fixed file format.",
            confusable_with=["FEAT-A-01", "FEAT-A-03"],
            requirement_id="REQ-A-04",
            document_id=document_id_for("FEAT-A-04"),
            version="1.0", version_status="current", created_date="2026-05-30", modified_date="2026-05-30",
            superseded_by="", supersedes="", is_current=True,
        ),
        Feature(
            feature_id="FEAT-B-02", product_id="PROD-B",
            name="Habit Template Marketplace", status="planned", priority=2,
            formal_term="Habit Template Marketplace",
            colloquial_terms=["browse habit packs", "ready-made routines"],
            summary="Lets users adopt a pre-built template of habits instead of creating "
                    "each habit from scratch.",
            # Sibling of FEAT-B-01 within the same product. Declared adjacency is what
            # makes this a D1 distractor with objectively derivable non-relevance rather
            # than a coincidence the renderer happened to produce.
            confusable_with=["FEAT-B-01"],
            requirement_id="REQ-B-01",
            document_id=document_id_for("FEAT-B-02"),
            version="1.0", version_status="current", created_date="2026-07-02",
            modified_date="2026-07-02", superseded_by="", supersedes="", is_current=True,
        ),
        Feature(
            feature_id="FEAT-B-01", product_id="PROD-B",
            name="Streak Recovery Suggestion Engine", status="launched", priority=1,
            formal_term="Streak Recovery Suggestion Engine",
            colloquial_terms=["streak saver", "saving a broken streak", "losing a streak"],
            summary="Suggests a reduced-effort alternative habit when a user is about to "
                    "break a multi-week streak.",
            confusable_with=["FEAT-B-02"],
            requirement_id="REQ-B-01",
            document_id=document_id_for("FEAT-B-01", "1.0"),
            version="1.0", version_status="current", created_date="2026-06-11", modified_date="2026-06-11",
            superseded_by=document_id_for("FEAT-B-01", "2.0"),
            supersedes="", is_current=False,
        ),
        Feature(
            feature_id="FEAT-B-01", product_id="PROD-B",
            name="Streak Recovery Suggestion Engine", status="launched", priority=1,
            formal_term="Streak Recovery Suggestion Engine",
            colloquial_terms=["streak saver", "saving a broken streak", "losing a streak"],
            summary="Suggests a reduced-effort alternative habit when a user is about to "
                    "break a multi-week streak.",
            confusable_with=["FEAT-B-02"],
            requirement_id="REQ-B-01",
            document_id=document_id_for("FEAT-B-01", "2.0"),
            version="2.0", version_status="current", created_date="2026-06-11", modified_date="2026-08-02",
            superseded_by="", supersedes=document_id_for("FEAT-B-01", "1.0"),
            is_current=True,
        ),
    ]

    # No post-hoc mutation of `status` is needed: the base class now uses
    # `version_status`, so `Feature.status` unambiguously means feature lifecycle and the
    # two concepts cannot be confused.
    for entity in features:
        entity.version_status = "current" if entity.is_current else "superseded"

    # -- PRDs (versioned) ----------------------------------------------------
    prds = [
        Prd(
            prd_id="PRD-A-01", product_id="PROD-A",
            title="Meridian employee onboarding and payroll readiness",
            author_role="Senior Product Manager", is_normative=True,
            summary="Defines how a new employee becomes payroll-ready, including the "
                    "progressive collection of tax and banking details.",
            sections=["Background", "Goals", "Non-goals", "Requirements",
                      "Success measures", "Open questions"],
            requirement_ids=["REQ-A-01", "REQ-A-02"],
            document_id=document_id_for("PRD-A-01", "1.0"),
            version="1.0", version_status="current", created_date="2026-02-02", modified_date="2026-02-02",
            superseded_by=document_id_for("PRD-A-01", "2.0"),
            supersedes="", is_current=False,
        ),
        Prd(
            prd_id="PRD-A-01", product_id="PROD-A",
            title="Meridian employee onboarding and payroll readiness",
            author_role="Senior Product Manager", is_normative=True,
            summary="Defines how a new employee becomes payroll-ready, including the "
                    "progressive collection of tax and banking details.",
            sections=["Background", "Goals", "Non-goals", "Requirements",
                      "Success measures", "Open questions", "Change log"],
            requirement_ids=["REQ-A-01", "REQ-A-02"],
            document_id=document_id_for("PRD-A-01", "2.0"),
            version="2.0", version_status="current", created_date="2026-02-02", modified_date="2026-07-18",
            superseded_by="", supersedes=document_id_for("PRD-A-01", "1.0"),
            is_current=True,
        ),
        Prd(
            prd_id="PRD-A-02", product_id="PROD-A",
            title="Meridian manager approval and payroll export",
            author_role="Product Manager", is_normative=True,
            summary="Covers bulk timesheet approval and recurring payroll file export to "
                    "external payroll providers.",
            sections=["Background", "Goals", "Non-goals", "Requirements",
                      "Success measures", "Risks"],
            requirement_ids=["REQ-A-03", "REQ-A-04"],
            document_id=document_id_for("PRD-A-02"),
            version="1.0", version_status="current", created_date="2026-04-10", modified_date="2026-04-10",
            superseded_by="", supersedes="", is_current=True,
        ),
    ]

    prds.append(Prd(
        prd_id="PRD-B-01", product_id="PROD-B",
        title="Tally streak retention",
        author_role="Founder", is_normative=True,
        summary="Covers reducing user churn when an established streak is about to break.",
        sections=["Background", "Goals", "Requirements", "Open questions"],
        requirement_ids=["REQ-B-01"],
        document_id=document_id_for("PRD-B-01"),
        version="1.0", version_status="current", created_date="2026-06-15",
        modified_date="2026-06-15", superseded_by="", supersedes="", is_current=True,
    ))

    for prd in prds:
        prd.version_status = "current" if prd.is_current else "superseded"

    requirements = [
        Requirement(
            requirement_id="REQ-A-01", prd_id="PRD-A-01", product_id="PROD-A",
            title="Tax details are collected progressively",
            statement="Tax documentation must be collected after the employee's first "
                      "successful login, not as part of initial account registration.",
            is_normative=True,
        ),
        Requirement(
            requirement_id="REQ-A-02", prd_id="PRD-A-01", product_id="PROD-A",
            title="Identity is verified before payment privileges",
            statement="An employee must not be granted payment privileges until identity "
                      "verification has succeeded.",
            is_normative=True,
        ),
        Requirement(
            requirement_id="REQ-A-03", prd_id="PRD-A-02", product_id="PROD-A",
            title="Managers approve timesheets in bulk",
            statement="A manager must be able to approve multiple timesheets in one "
                      "action where all selected timesheets are complete.",
            is_normative=True,
        ),
        Requirement(
            requirement_id="REQ-A-04", prd_id="PRD-A-02", product_id="PROD-A",
            title="Payroll exports follow a fixed schedule",
            statement="Payroll exports must run on a fixed, pre-configured schedule and "
                      "must not be triggered ad hoc by end users.",
            is_normative=True,
        ),
        Requirement(
            requirement_id="REQ-B-01", prd_id="PRD-B-01", product_id="PROD-B",
            title="Streak loss is mitigated before it occurs",
            statement="The product must offer a reduced-effort alternative before a user "
                      "breaks an established streak.",
            is_normative=True,
        ),
    ]

    components = [
        TechnicalComponent(
            component_id="COMP-01", name="Verisign ID Verification API",
            component_type="third_party", owner_team="external vendor",
            notes="Third-party identity document verification. Team does not own this "
                  "service; failures surface only as a timeout.",
            adjacent_component_ids=["COMP-02", "COMP-05"],
        ),
        TechnicalComponent(
            component_id="COMP-02", name="Stripe Payments Gateway",
            component_type="third_party", owner_team="external vendor",
            notes="Handles payment instrument tokenisation.",
            adjacent_component_ids=["COMP-01", "COMP-03"],
        ),
        TechnicalComponent(
            component_id="COMP-03", name="Payroll Ledger Database",
            component_type="database", owner_team="platform",
            notes="System of record for approved hours and payroll totals.",
            adjacent_component_ids=["COMP-02", "COMP-04"],
        ),
        TechnicalComponent(
            component_id="COMP-04", name="Digest Notification Worker",
            component_type="service", owner_team="platform",
            notes="Builds and sends scheduled email digests.",
            adjacent_component_ids=["COMP-03", "COMP-05"],
        ),
        TechnicalComponent(
            component_id="COMP-05", name="Domain Event Bus",
            component_type="queue", owner_team="platform",
            notes="Carries domain events between services.",
            adjacent_component_ids=["COMP-01", "COMP-04"],
        ),
        TechnicalComponent(
            component_id="COMP-06", name="TaxBand Rate Service",
            component_type="third_party", owner_team="external vendor",
            notes="Resolves tax bands for a given jurisdiction. Rate-limited, 20 calls/min.",
            adjacent_component_ids=["COMP-02", "COMP-05"],
        ),
    ]

    pbis = [
        Pbi(pbi_id="PBI-A-011", product_id="PROD-A", feature_id="FEAT-A-01",
            title="Ask for tax details on day three",
            description="As a new starter I want to be asked for my tax details a few days "
                        "after I sign up, so that I am not stuck on a long form before I "
                        "have even seen the product.",
            story_points=3, status="done", created_date="2026-03-02",
            author_role="Product Owner", component_id="COMP-06"),
        Pbi(pbi_id="PBI-A-012", product_id="PROD-A", feature_id="FEAT-A-01",
            title="Show the ramp checklist after first login",
            description="As a new starter I want to see what information will be asked of "
                        "me over the next week, so I know what is coming.",
            story_points=2, status="done", created_date="2026-03-05",
            author_role="Product Owner", component_id="COMP-05"),
        Pbi(pbi_id="PBI-A-013", product_id="PROD-A", feature_id="FEAT-A-02",
            title="Block payment privileges until ID check passes",
            description="As a payroll admin I want payment privileges blocked until the "
                        "ID check has come back, so that we never pay an unverified person.",
            story_points=5, status="done", created_date="2026-03-12",
            author_role="Product Owner", component_id="COMP-01"),
        Pbi(pbi_id="PBI-A-014", product_id="PROD-A", feature_id="FEAT-A-03",
            title="Select-all approve on the timesheet grid",
            description="As a manager I want to select all timesheets and approve them in "
                        "one go, rather than approving each row separately.",
            story_points=5, status="in_progress", created_date="2026-05-02",
            author_role="Product Owner", component_id="COMP-03"),
        Pbi(pbi_id="PBI-A-015", product_id="PROD-A", feature_id="FEAT-A-03",
            title="Reject the whole batch with one reason",
            description="As a manager I want to reject a whole batch with a single reason, "
                        "because writing the same note twenty times is pointless.",
            story_points=3, status="to_do", created_date="2026-05-06",
            author_role="Product Owner", component_id="COMP-03"),
        Pbi(pbi_id="PBI-A-016", product_id="PROD-A", feature_id="FEAT-A-04",
            title="Nightly payroll export job",
            description="As a payroll admin I want the payroll file exported every night at "
                        "a fixed time, so my provider always has today's data.",
            story_points=5, status="to_do",
            created_date="2026-06-01", author_role="Product Owner", component_id="COMP-03"),
        Pbi(pbi_id="PBI-A-017", product_id="PROD-A", feature_id="FEAT-A-02",
            title="Hide the payment tab until verification clears",
            description="As a new starter I want the payment area hidden until my ID has "
                        "been checked, so that I do not try to add a card and get "
                        "rejected later.",
            story_points=2, status="done", created_date="2026-03-20",
            author_role="Product Owner", component_id="COMP-02"),
        Pbi(pbi_id="PBI-B-021", product_id="PROD-B", feature_id="FEAT-B-01",
            title="Offer a lighter habit before the streak breaks",
            description="As a user I want to be offered an easier version of my habit "
                        "before I break my streak, so I do not lose weeks of progress.",
            story_points=3, status="done", created_date="2026-06-20",
            author_role="Founder", component_id="COMP-05"),
        Pbi(pbi_id="PBI-B-022", product_id="PROD-B", feature_id="FEAT-B-01",
            title="Explain why the suggestion appeared",
            description="As a user I want the app to say why it is suggesting something "
                        "easier, instead of it just appearing out of nowhere.",
            story_points=2, status="in_progress", created_date="2026-07-14",
            author_role="Founder", component_id="COMP-04"),
    ]

    tickets = [
        Ticket(
            ticket_id="TKT-A-101", product_id="PROD-A", feature_id="FEAT-A-01",
            related_component_id="COMP-06", pbi_id="PBI-A-011",
            reported_symptom="I set up my account on Monday and it wanted my tax details "
                             "straight away. I only wanted to look around first.",
            customer_segment="new starter", severity="medium",
            opened_date="2026-03-18", reporter_role="Support agent",
        ),
        Ticket(
            ticket_id="TKT-A-102", product_id="PROD-A", feature_id="FEAT-A-03",
            related_component_id="COMP-03", pbi_id="PBI-A-014",
            reported_symptom="I have got forty hours to sign off on and I have to click "
                             "approve on every single row. Please add a select all.",
            customer_segment="line manager", severity="high",
            opened_date="2026-05-20", reporter_role="Support agent",
        ),
    ]

    decisions = [
        DecisionRecord(
            decision_id="DEC-A-01", product_id="PROD-A", about_entity_id="FEAT-A-01",
            decision="Move tax collection to day three of the onboarding ramp rather than "
                     "requiring it during sign-up.",
            rationale="Early testing showed the long sign-up form caused abandonment in the "
                      "first session. Asking later, once the user has seen value, raised "
                      "completion of the tax step from 54% to 88%.",
            decided_date="2026-07-16", decided_by_role="Senior Product Manager",
        ),
        DecisionRecord(
            decision_id="DEC-B-01", product_id="PROD-B", about_entity_id="FEAT-B-01",
            decision="Ship the streak saver prompt only in the evening, not on waking.",
            rationale="Morning prompts were being dismissed unread. Evening is when people "
                      "are already opening the app.",
            decided_date="2026-08-01", decided_by_role="Founder",
        ),
    ]

    meeting_notes = [
        MeetingNote(
            note_id="NOTE-A-01", product_id="PROD-A",
            about_entity_ids=["FEAT-A-03", "PBI-A-014"],
            meeting_date="2026-05-08",
            attendees_role=["Product Manager", "Engineering lead"],
            topics=[
                "Managers are approving roughly forty rows at a time, so the per-row click "
                "is the bottleneck",
                "Not doing partial-batch approval this quarter, it complicates the audit "
                "trail",
                "Need to check the ledger is not the slow part before committing to a date",
            ],
        ),
        MeetingNote(
            note_id="NOTE-B-01", product_id="PROD-B",
            about_entity_ids=["FEAT-B-01"],
            meeting_date="2026-07-20",
            attendees_role=["Founder"],
            topics=[
                "The saver prompt fires too early in the day and people swipe it away",
                "Trying evening only for a fortnight",
            ],
        ),
    ]

    runbooks = [
        Runbook(
            runbook_id="RBK-A-01", product_id="PROD-A", component_id="COMP-06",
            title="TaxBand rate service: handling rate-limit responses",
            steps=[
                "A 429 from the rate service means the 20 calls/minute budget is exhausted.",
                "Back off for 30 seconds, then retry the single call. Do not retry the batch.",
                "If three consecutive batches fail, raise an operations alert; the tax "
                "step cannot complete without resolved rates.",
            ],
            last_reviewed="2026-08-05",
        ),
    ]

    dependencies = [
        # EXPLICIT: stated in words in at least one rendered document.
        Dependency(
            dependency_id="DEP-001", from_type="feature", from_id="FEAT-A-02",
            to_type="component", to_id="COMP-01", dependency_type="depends_on",
            description="Identity Verification Window calls the third-party identity "
                        "verification service. Stated in the feature specification.",
            explicitness="explicit",
        ),
        Dependency(
            dependency_id="DEP-002", from_type="feature", from_id="FEAT-A-03",
            to_type="component", to_id="COMP-03", dependency_type="depends_on",
            description="Bulk Timesheet Approval reads and writes approved hours in the "
                        "payroll ledger. Stated in the feature specification.",
            explicitness="explicit",
        ),
        Dependency(
            dependency_id="DEP-003", from_type="feature", from_id="FEAT-A-04",
            to_type="component", to_id="COMP-03", dependency_type="depends_on",
            description="Payroll Export Scheduling reads payroll totals from the ledger. "
                        "Stated in the feature specification.",
            explicitness="explicit",
        ),
        Dependency(
            dependency_id="DEP-004", from_type="feature", from_id="FEAT-A-02",
            to_type="feature", to_id="FEAT-A-01", dependency_type="depends_on",
            description="Payment privileges are granted only once the employee is payroll-"
                        "ready, so this follows from the first PRD. Stated in that PRD.",
            explicitness="explicit",
        ),
        Dependency(
            dependency_id="DEP-005", from_type="pbi", from_id="PBI-A-016",
            to_type="component", to_id="COMP-03", dependency_type="depends_on",
            description="The nightly export job reads totals from the ledger. Stated in the "
                        "PBI description.",
            explicitness="explicit",
        ),
        # IMPLICIT: encoded here, stated in no document. Recoverable only by reasoning
        # across documents. Per Q5 these are never left to common sense.
        Dependency(
            dependency_id="DEP-006", from_type="feature", from_id="FEAT-A-01",
            to_type="component", to_id="COMP-06", dependency_type="depends_on",
            description="Progressive Profiling cannot resolve a tax band without the rate "
                        "service. No document states this; it follows from the feature "
                        "collecting tax details and from the runbook describing that "
                        "service as the only source of resolved rates.",
            explicitness="implicit",
        ),
        Dependency(
            dependency_id="DEP-007", from_type="feature", from_id="FEAT-A-01",
            to_type="feature", to_id="FEAT-A-02", dependency_type="depends_on",
            description="A new employee reaches the tax step only after identity "
                        "verification. No document states the ordering; it follows from the "
                        "onboarding sequence in PRD-A-01 v2.",
            explicitness="implicit",
        ),
        Dependency(
            dependency_id="DEP-008", from_type="pbi", from_id="PBI-A-014",
            to_type="pbi", to_id="PBI-A-015", dependency_type="blocks",
            description="Select-all approve cannot ship before batch rejection exists, "
                        "because approving a whole batch with no way to reject part of it "
                        "is not shippable. Stated nowhere.",
            explicitness="implicit",
        ),
        Dependency(
            dependency_id="DEP-009", from_type="feature", from_id="FEAT-A-04",
            to_type="component", to_id="COMP-05", dependency_type="depends_on",
            description="The scheduled export is driven by a recurring domain event rather "
                        "than a cron, so it needs the event bus. Not stated in any document.",
            explicitness="implicit",
        ),
        Dependency(
            dependency_id="DEP-010", from_type="feature", from_id="FEAT-B-01",
            to_type="component", to_id="COMP-04", dependency_type="depends_on",
            description="The evening prompt is dispatched by the digest worker. Not stated "
                        "in any document.",
            explicitness="implicit",
        ),
    ]

    conflicts = [
        Conflict(
            conflict_id="CONF-01", product_id="PROD-A",
            document_a_id=document_id_for("PRD-A-01", "1.0"),
            document_b_id=document_id_for("FEAT-A-01", "1.0"),
            conflict_type="stale_requirement",
            description="PRD-A-01 v1 and the Progressive Profiling v1 spec both require tax "
                        "details during initial registration. DEC-A-01 later moved the "
                        "tax step to day three, but v1 of the PRD was never reissued.",
            is_resolved=True,
            resolution_note="Resolved by PRD-A-01 v2, which is normative. Both v1 documents "
                            "remain in the repository and are now stale.",
            resolved_by_document_id=document_id_for("PRD-A-01", "2.0"),
        ),
        Conflict(
            conflict_id="CONF-02", product_id="PROD-B",
            document_a_id=document_id_for("FEAT-B-01", "1.0"),
            document_b_id=document_id_for("FEAT-B-01", "2.0"),
            conflict_type="inconsistent_claim",
            description="Streak Recovery v1 states the prompt fires on waking. v2 states it "
                        "fires in the evening. Both versions are still in the repository "
                        "and the v1 spec has not been annotated.",
            is_resolved=False,
            resolution_note="",
            resolved_by_document_id="",
        ),
    ]

    # -- cross-document links -------------------------------------------------
    links: list[DocumentLink] = []
    counter = [0]

    def link(from_doc: str, to_type: str, to_id: str, link_type: str) -> None:
        counter[0] += 1
        links.append(DocumentLink(
            link_id=f"LNK-{counter[0]:04d}", from_document_id=from_doc,
            to_entity_type=to_type, to_entity_id=to_id, link_type=link_type,
        ))

    # version lineage
    for prd in prds:
        if prd.supersedes:
            link(prd.document_id, "product", prd.product_id, "supersedes")
        for requirement_id in prd.requirement_ids:
            link(prd.document_id, "requirement", requirement_id, "defines")
    for feature in features:
        if feature.supersedes:
            link(feature.document_id, "product", feature.product_id, "supersedes")
        link(feature.document_id, "product", feature.product_id, "defines")

    # implementation links
    for pbi in pbis:
        doc = f"DOC-{pbi.pbi_id}"
        link(doc, "feature", pbi.feature_id, "implements")
        link(doc, "component", pbi.component_id, "implements")
    for ticket in tickets:
        doc = f"DOC-{ticket.ticket_id}"
        link(doc, "feature", ticket.feature_id, "implements")
        link(doc, "component", ticket.related_component_id, "depends_on")
    for note in meeting_notes:
        doc = f"DOC-{note.note_id}"
        for entity_id in note.about_entity_ids:
            link(doc, "feature" if entity_id.startswith("FEAT") else "pbi",
                 entity_id, "contextualises")
    for runbook in runbooks:
        link(f"DOC-{runbook.runbook_id}", "component", runbook.component_id, "defines")
    for decision in decisions:
        link(f"DOC-{decision.decision_id}", "feature", decision.about_entity_id,
             "contextualises")
    for component in components:
        doc = f"DOC-{component.component_id}"
        for adjacent in component.adjacent_component_ids:
            link(doc, "component", adjacent, "contextualises")

    # BLOCKING relationship. Exercises the sixth and final link type, `blocks`, which
    # the other five do not cover. Blocking is a real backlog relationship and is also the
    # kind of constraint a query must be able to distinguish from an ordinary dependency:
    # A blocks B, but A does not depend on B.
    link("DOC-PBI-A-017", "pbi", "PBI-A-016", "blocks")

    # DECLARED DISTRACTORS. These are D1/D2/D3 in the model, not coincidences: each is
    # objectively not the answer, because it points at a different entity.
    for feature in features:
        if not feature.is_current:
            continue
        for other in feature.confusable_with:
            link(feature.document_id, "feature", other, "contextualises")

    return SourceModel(
        model_version="v1-schema-sample",
        seed=20260928,
        created_date=CREATED,
        products=products,
        features=features,
        prds=prds,
        requirements=requirements,
        pbis=pbis,
        components=components,
        tickets=tickets,
        decisions=decisions,
        meeting_notes=meeting_notes,
        runbooks=runbooks,
        dependencies=dependencies,
        conflicts=conflicts,
        document_links=links,
    )

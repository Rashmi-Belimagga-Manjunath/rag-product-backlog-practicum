"""
Final 272-document corpus generator (frozen methodology, post-D-013).

WHAT THIS IS
------------
The approved source of truth for the final corpus: 260 current documents plus 12
superseded documents, two products, 24 features, 10 PRDs, 16 requirements, 18 components,
120 PBIs, 40 tickets, 16 decisions, 24 meeting notes, 8 runbooks, 208 dependencies
(104 explicit / 104 implicit), 12 conflicts (7 resolved / 5 unresolved), and ~540
declared cross-document links.

Every count below is a TARGET measured and asserted, not a free parameter. The builder
asserts them, so a drift is a code failure rather than a silent slip. Determinism is
guaranteed by construction: the model is built from fixed lists and index arithmetic,
never from os.environ, file ordering, or clock reads.

The corpus is designed so every one of the 32 selector slots resolves (that gate is run
separately as `--against-final`): the seven former corpus requirements now have real
content - Tally tickets (Q-05), an approval-limit pair (Q-SUP-3), Meridian
component-to-component dependencies (Q-10), ordering dependencies (Q-11/Q-14/Q-20),
meeting-note evidence (Q-19), runbook evidence (Q-16), and superseded-document evidence
(Q-21).

DELIBERATE MECHANISM DESIGN
---------------------------
- Dependency lists are ORDERED so that first-match selectors land on the dependency whose
  story they are meant to test (e.g. the first implicit dependency is the runbook-evidenced
  one for Q-13/Q-16, and the ordering candidate for Q-14/Q-20 sits first among implicit
  ordering dependencies).
- "Explicit" always means "stated in at least one rendered document": feature specs render
  their outgoing explicit dependencies, component documents render theirs, and PBI
  documents render theirs. "Implicit" means encoded in the model only, stated in no
  rendered document. Nothing is labelled explicit unless prose states it.
- All versioned content uses the same `document_id_for` convention as the mechanism
  sample, so document and chunk IDs stay stable under later edits.
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
from .v1_sample import document_id_for

CREATED = "2026-09-28"

MER = "PROD-M"
TAL = "PROD-T"

M_COMP = [f"COMP-M-{i:02d}" for i in range(1, 11)]
T_COMP = [f"COMP-T-{i:02d}" for i in range(1, 9)]


def _fid(feature_id: str, version: str) -> str:
    """Document ID for a feature-spec version."""
    return document_id_for(feature_id, version)


def _pid(prd_id: str, version: str) -> str:
    """Document ID for a PRD version."""
    return document_id_for(prd_id, version)


# ---------------------------------------------------------------------------
# Feature catalogue (24: 12 Meridian, 12 Tally)
# ---------------------------------------------------------------------------

FEATURE_SPECS: list[dict] = [
    # --- Meridian (HRTech, formal) -------------------------------------------
    dict(id="FEAT-M-01", product=MER, name="Progressive Profiling", status="launched",
         priority=1, formal="Progressive Profiling",
         colloquial=["onboarding ramp", "new-user activation", "first-run setup"],
         summary="Collects additional employee details progressively after first login "
                 "rather than in a single mandatory form.",
         req="REQ-M-01", comp="COMP-M-06", confusable=["FEAT-M-02", "FEAT-M-08"],
         versioned=True, approval_limit="$5,000", approval_limit_v1="$2,500"),
    dict(id="FEAT-M-02", product=MER, name="Identity Verification Window",
         status="launched", priority=2, formal="Identity Verification Window",
         colloquial=["ID check stage", "KYC prompt", "the verification pop-up"],
         summary="Requires identity document verification before an employee can be "
                 "granted payment privileges.",
         req="REQ-M-02", comp="COMP-M-01", confusable=["FEAT-M-01", "FEAT-M-03"]),
    dict(id="FEAT-M-03", product=MER, name="Bulk Timesheet Approval",
         status="in_progress", priority=3, formal="Bulk Timesheet Approval",
         colloquial=["batch timesheet sign-off", "approving hours in bulk"],
         summary="Allows a manager to approve multiple submitted timesheets in a single "
                 "action.",
         req="REQ-M-03", comp="COMP-M-02", confusable=["FEAT-M-02", "FEAT-M-04"]),
    dict(id="FEAT-M-04", product=MER, name="Payroll Export Scheduling", status="planned",
         priority=4, formal="Payroll Export Scheduling",
         colloquial=["automated payroll file", "scheduled payslip dump"],
         summary="Schedules recurring export of payroll data to third-party payroll "
                 "providers in a fixed file format.",
         req="REQ-M-04", comp="COMP-M-02", confusable=["FEAT-M-03", "FEAT-M-05"],
         versioned=True),
    dict(id="FEAT-M-05", product=MER, name="Approved Hours Reporting",
         status="planned", priority=5, formal="Approved Hours Reporting",
         colloquial=["hours ledger", "approved hours report"],
         summary="Reports approved hours and payroll totals from the ledger for finance "
                 "reconciliation.",
         req="REQ-M-05", comp="COMP-M-02", confusable=["FEAT-M-04", "FEAT-M-09"]),
    dict(id="FEAT-M-06", product=MER, name="Manager Approval Console",
         status="launched", priority=3, formal="Manager Approval Console",
         colloquial=["approval console", "manager view"],
         summary="Presents pending timesheets and approvals to a manager in one console.",
         req="REQ-M-03", comp="COMP-M-03", confusable=["FEAT-M-03", "FEAT-M-09"]),
    dict(id="FEAT-M-07", product=MER, name="Benefits Enrolment Portal",
         status="planned", priority=6, formal="Benefits Enrolment Portal",
         colloquial=["perks hub", "benefits page"],
         summary="Lets an employee enrol in and review benefits packages through a "
                 "self-service portal.",
         req="REQ-M-06", comp="COMP-M-09", confusable=["FEAT-M-08", "FEAT-M-01"]),
    dict(id="FEAT-M-08", product=MER, name="Tax Band Adjustments", status="launched",
         priority=7, formal="Tax Band Adjustments",
         colloquial=["tax code changes", "payroll bracket update"],
         summary="Resolves and applies tax band adjustments for individual employees.",
         req="REQ-M-06", comp="COMP-M-06", confusable=["FEAT-M-07", "FEAT-M-01"]),
    dict(id="FEAT-M-09", product=MER, name="Self-Serve Payslips", status="in_progress",
         priority=8, formal="Self-Serve Payslips",
         colloquial=["payslip viewer", "payslip download"],
         summary="Lets an employee view and download generated payslips from a "
                 "self-service area.",
         req="REQ-M-07", comp="COMP-M-07", confusable=["FEAT-M-05", "FEAT-M-12"]),
    dict(id="FEAT-M-10", product=MER, name="Overtime Scheduling", status="planned",
         priority=9, formal="Overtime Scheduling",
         colloquial=["extra hours log", "overtime entry"],
         summary="Captures planned and worked overtime hours ahead of approval.",
         req="REQ-M-08", comp="COMP-M-02", confusable=["FEAT-M-03", "FEAT-M-11"]),
    dict(id="FEAT-M-11", product=MER, name="Leaver Processing", status="launched",
         priority=10, formal="Leaver Processing",
         colloquial=["offboarding flow", "exit processing"],
         summary="Finalises pay, benefits and access for departing employees.",
         req="REQ-M-08", comp="COMP-M-02", confusable=["FEAT-M-10", "FEAT-M-08"]),
    dict(id="FEAT-M-12", product=MER, name="Audit Trail Export", status="in_progress",
         priority=11, formal="Audit Trail Export",
         colloquial=["compliance log", "audit file export"],
         summary="Exports an audit trail of approval and payroll actions for compliance.",
         req="REQ-M-09", comp="COMP-M-10", confusable=["FEAT-M-05", "FEAT-M-09"]),

    # --- Tally (Consumer habit-tracking, informal) ---------------------------
    dict(id="FEAT-T-01", product=TAL, name="Streak Recovery Suggestion Engine",
         status="launched", priority=1, formal="Streak Recovery Suggestion Engine",
         colloquial=["streak saver", "saving a broken streak", "losing a streak"],
         summary="Suggests a reduced-effort alternative habit when a user is about to "
                 "break a multi-week streak.",
         req="REQ-T-01", comp="COMP-T-02", confusable=["FEAT-T-02", "FEAT-T-10"],
         versioned=True),
    dict(id="FEAT-T-02", product=TAL, name="Habit Template Marketplace",
         status="planned", priority=2, formal="Habit Template Marketplace",
         colloquial=["browse habit packs", "ready-made routines"],
         summary="Lets users adopt a pre-built template of habits instead of creating "
                 "each habit from scratch.",
         req="REQ-T-02", comp="COMP-T-06", confusable=["FEAT-T-01", "FEAT-T-06"]),
    dict(id="FEAT-T-03", product=TAL, name="Evening Reminder Builder",
         status="launched", priority=3, formal="Evening Reminder Builder",
         colloquial=["nightly nudge", "reminder settings"],
         summary="Builds personalised evening reminder schedules per habit.",
         req="REQ-T-03", comp="COMP-T-05", confusable=["FEAT-T-10", "FEAT-T-04"],
         versioned=True),
    dict(id="FEAT-T-04", product=TAL, name="Recurring Habit Scheduling",
         status="in_progress", priority=4, formal="Recurring Habit Scheduling",
         colloquial=["weekly plan", "repeat schedule"],
         summary="Defines recurring schedules so a habit can repeat on chosen days.",
         req="REQ-T-04", comp="COMP-T-01", confusable=["FEAT-T-03", "FEAT-T-05"]),
    dict(id="FEAT-T-05", product=TAL, name="Streak Freeze Tokens", status="planned",
         priority=5, formal="Streak Freeze Tokens",
         colloquial=["streak shield", "freeze a streak"],
         summary="Lets a user protect an established streak with a limited number of "
                 "freeze tokens.",
         req="REQ-T-05", comp="COMP-T-02", confusable=["FEAT-T-01", "FEAT-T-04"],
         versioned=True),
    dict(id="FEAT-T-06", product=TAL, name="Achievement Badges", status="launched",
         priority=6, formal="Achievement Badges",
         colloquial=["badges", "milestone icons"],
         summary="Awards badges for milestone streaks and completion counts.",
         req="REQ-T-06", comp="COMP-T-01", confusable=["FEAT-T-07", "FEAT-T-02"]),
    dict(id="FEAT-T-07", product=TAL, name="Habit Sharing Board", status="planned",
         priority=7, formal="Habit Sharing Board",
         colloquial=["share plans", "friend streaks"],
         summary="Allows users to share habits and compare streaks with friends.",
         req="REQ-T-07", comp="COMP-T-07", confusable=["FEAT-T-12", "FEAT-T-06"]),
    dict(id="FEAT-T-08", product=TAL, name="Reflection Prompts", status="in_progress",
         priority=8, formal="Reflection Prompts",
         colloquial=["check-in questions", "daily reflections"],
         summary="Opens a short reflective check-in while a user logs a habit.",
         req="REQ-T-04", comp="COMP-T-01", confusable=["FEAT-T-04", "FEAT-T-10"]),
    dict(id="FEAT-T-09", product=TAL, name="User Data Export", status="planned",
         priority=9, formal="User Data Export",
         colloquial=["export my data", "take my logs"],
         summary="Exports a user's habit history in a portable format on request.",
         req="REQ-T-07", comp="COMP-T-08", confusable=["FEAT-T-07", "FEAT-T-08"]),
    dict(id="FEAT-T-10", product=TAL, name="Gentle Escalation Flow", status="launched",
         priority=2, formal="Gentle Escalation Flow",
         colloquial=["coaching nudges", "compassionate reminders"],
         summary="Escalates recovery prompts gently before a streak is written off.",
         req="REQ-T-01", comp="COMP-T-05", confusable=["FEAT-T-01", "FEAT-T-03"]),
    dict(id="FEAT-T-11", product=TAL, name="Habit Breaking Support", status="planned",
         priority=10, formal="Habit Breaking Support",
         colloquial=["quit a habit", "stop tracking"],
         summary="Guides a user through deliberately ending a habit without losing "
                 "account history.",
         req="REQ-T-06", comp="COMP-T-01", confusable=["FEAT-T-06", "FEAT-T-09"]),
    dict(id="FEAT-T-12", product=TAL, name="Team Challenges", status="in_progress",
         priority=11, formal="Team Challenges",
         colloquial=["group streaks", "challenge a friend"],
         summary="Runs time-boxed habit challenges shared with a friend or group.",
         req="REQ-T-07", comp="COMP-T-07", confusable=["FEAT-T-07", "FEAT-T-02"]),
]

VERSIONED_FEATURES = {s["id"] for s in FEATURE_SPECS if s.get("versioned")}

# ---------------------------------------------------------------------------
# Requirements (16) and PRDs (10)
# ---------------------------------------------------------------------------

REQUIREMENT_SPECS: list[dict] = [
    dict(id="REQ-M-01", prd="PRD-M-01", product=MER,
         title="Tax details are collected progressively",
         statement="Tax documentation must be collected after the employee's first "
                   "successful login, not as part of initial account registration."),
    dict(id="REQ-M-02", prd="PRD-M-01", product=MER,
         title="Identity is verified before payment privileges",
         statement="An employee must not be granted payment privileges until identity "
                   "verification has succeeded."),
    dict(id="REQ-M-03", prd="PRD-M-02", product=MER,
         title="Managers approve timesheets in bulk",
         statement="A manager must be able to approve multiple timesheets in one action "
                   "where all selected timesheets are complete."),
    dict(id="REQ-M-04", prd="PRD-M-02", product=MER,
         title="Payroll exports follow a fixed schedule",
         statement="Payroll exports must run on a fixed, pre-configured schedule and must "
                   "not be triggered ad hoc by end users."),
    dict(id="REQ-M-05", prd="PRD-M-03", product=MER,
         title="Approved hours feed finance reporting",
         statement="Finance reporting must reflect only approved hours from the ledger."),
    dict(id="REQ-M-06", prd="PRD-M-04", product=MER,
         title="Benefits and tax adjustments are self-service",
         statement="Employees must be able to review and change benefits and tax band "
                   "settings themselves, subject to approval rules."),
    dict(id="REQ-M-07", prd="PRD-M-04", product=MER,
         title="Payslips are self-serve",
         statement="An employee must be able to view and download their own payslips from "
                   "a self-service area."),
    dict(id="REQ-M-08", prd="PRD-M-05", product=MER,
         title="Overtime and leaver pay follow approval",
         statement="Overtime hours and final leaver payments must be approved before they "
                   "enter the ledger."),
    dict(id="REQ-M-09", prd="PRD-M-06", product=MER,
         title="Audit trail is exportable",
         statement="An exportable audit trail must record every approval and payroll "
                   "action for compliance review."),
    dict(id="REQ-T-01", prd="PRD-T-01", product=TAL,
         title="Streak loss is mitigated before it occurs",
         statement="The product must offer a reduced-effort alternative before a user "
                   "breaks an established streak."),
    dict(id="REQ-T-02", prd="PRD-T-02", product=TAL,
         title="Templates are adoptable in one step",
         statement="A user must be able to adopt a habit template without entering the "
                   "habits it contains by hand."),
    dict(id="REQ-T-03", prd="PRD-T-02", product=TAL,
         title="Reminders respect a schedule",
         statement="Reminder schedules must be user-configurable and must not exceed one "
                   "prompt per habit per day."),
    dict(id="REQ-T-04", prd="PRD-T-03", product=TAL,
         title="Recurring habits repeat predictably",
         statement="A recurring habit must repeat on the user's chosen days and times "
                   "without drifting."),
    dict(id="REQ-T-05", prd="PRD-T-03", product=TAL,
         title="Freeze tokens are limited and honest",
         statement="A freeze token must protect a streak exactly once and the supply of "
                   "tokens must be visible to the user."),
    dict(id="REQ-T-06", prd="PRD-T-04", product=TAL,
         title="Progress feels acknowledged",
         statement="Milestones and progress must be surfaced to the user in a way that "
                   "acknowledges sustained effort."),
    dict(id="REQ-T-07", prd="PRD-T-04", product=TAL,
         title="Sharing is explicit and revocable",
         statement="Any sharing of habits with others must be explicit on the user's part "
                   "and reversible at any time."),
]

PRD_SPECS: list[dict] = [
    dict(id="PRD-M-01", product=MER, title="Meridian employee onboarding and payroll readiness",
         author_role="Senior Product Manager", versioned=True,
         summary="Defines how a new employee becomes payroll-ready, including the "
                 "progressive collection of tax and banking details."),
    dict(id="PRD-M-02", product=MER, title="Meridian manager approval and payroll export",
         author_role="Product Manager", versioned=True,
         summary="Covers bulk timesheet approval and recurring payroll file export to "
                 "external payroll providers."),
    dict(id="PRD-M-03", product=MER, title="Meridian finance reporting from the ledger",
         author_role="Product Manager", versioned=True,
         summary="Fixes the ledger as the single source for approved hours feeding "
                 "finance reporting."),
    dict(id="PRD-M-04", product=MER, title="Meridian self-service employee portal",
         author_role="Senior Product Manager", versioned=False,
         summary="Covers benefits enrolment, tax band adjustments and self-serve payslips "
                 "for employees."),
    dict(id="PRD-M-05", product=MER, title="Meridian overtime and leaver processing",
         author_role="Product Manager", versioned=False,
         summary="Defines how overtime and final leaver payments flow through approval "
                 "before entering the ledger."),
    dict(id="PRD-M-06", product=MER, title="Meridian compliance and audit export",
         author_role="Compliance Product Manager", versioned=False,
         summary="Requires an exportable audit trail of approval and payroll actions."),
    dict(id="PRD-T-01", product=TAL, title="Tally streak retention",
         author_role="Founder", versioned=True,
         summary="Covers reducing user churn when an established streak is about to "
                 "break."),
    dict(id="PRD-T-02", product=TAL, title="Tally template adoption and reminders",
         author_role="Founder", versioned=True,
         summary="Covers one-step template adoption and user-configurable reminder "
                 "schedules."),
    dict(id="PRD-T-03", product=TAL, title="Tally repeatability and streak honesty",
         author_role="Founder", versioned=True,
         summary="Covers predictable recurring habits and the honest, limited supply of "
                 "streak freeze tokens."),
    dict(id="PRD-T-04", product=TAL, title="Tally social acknowledgement and sharing",
         author_role="Founder", versioned=True,
         summary="Covers badges and challenges, and the explicit, revocable sharing of "
                 "habits."),
]

# ---------------------------------------------------------------------------
# Components (18)
# ---------------------------------------------------------------------------

COMPONENT_SPECS: list[dict] = [
    dict(id="COMP-M-01", name="Verisign Identity Verification API", kind="third_party",
         owner="external vendor",
         notes="Third-party identity document verification. The team does not own this "
               "service; failures surface only as a timeout."),
    dict(id="COMP-M-02", name="Payroll Ledger Database", kind="database", owner="platform",
         notes="System of record for approved hours, overtime and payroll totals."),
    dict(id="COMP-M-03", name="Timesheet Approval Engine", kind="service", owner="platform",
         notes="Evaluates the completeness of submitted timesheets and records approvals."),
    dict(id="COMP-M-04", name="Digest Notification Worker", kind="service",
         owner="platform", notes="Builds and sends scheduled email digests."),
    dict(id="COMP-M-05", name="Domain Event Bus", kind="queue", owner="platform",
         notes="Carries domain events between services."),
    dict(id="COMP-M-06", name="TaxBand Rate Service", kind="third_party",
         owner="external vendor",
         notes="Resolves tax bands for a given jurisdiction. Rate-limited, 20 calls/min."),
    dict(id="COMP-M-07", name="Payslip Generation Service", kind="service",
         owner="platform", notes="Renders payslips from ledger data into a distributable "
                                 "format."),
    dict(id="COMP-M-08", name="MyMeridian Employee App", kind="service", owner="platform",
         notes="The employee-facing web application surface."),
    dict(id="COMP-M-09", name="Benefits Provider API", kind="third_party",
         owner="external vendor",
         notes="Third-party benefits catalogue and enrolment. Availability controls the "
               "perks hub."),
    dict(id="COMP-M-10", name="Audit Trail Store", kind="database", owner="platform",
         notes="Append-only store for approval and payroll audit events."),
    dict(id="COMP-T-01", name="Habit Store", kind="database", owner="platform",
         notes="Primary store for habits, logs and streak state."),
    dict(id="COMP-T-02", name="Streak Calculator", kind="service", owner="platform",
         notes="Computes streak state from the log. Pure function over logged entries."),
    dict(id="COMP-T-03", name="Push Notification Gateway", kind="third_party",
         owner="external vendor",
         notes="Third-party push delivery. Delivery timing cannot be fully controlled."),
    dict(id="COMP-T-04", name="Email Digest Worker", kind="service", owner="platform",
         notes="Assembles and sends email digests on a schedule."),
    dict(id="COMP-T-05", name="Prompt Scheduler", kind="service", owner="platform",
         notes="Schedules and fires reminder and recovery prompts."),
    dict(id="COMP-T-06", name="Template Library", kind="database", owner="platform",
         notes="Catalogue of adoptable habit templates."),
    dict(id="COMP-T-07", name="Social Graph Service", kind="service", owner="platform",
         notes="Manages friend relationships and shared-streak state."),
    dict(id="COMP-T-08", name="Export Bundle Service", kind="service", owner="platform",
         notes="Packages a user's habit history into a portable export bundle."),
]

COMPONENTS_BY_ID = {c["id"]: c for c in COMPONENT_SPECS}

# ---------------------------------------------------------------------------
# Dependency tables (approved counts, exact)
# ---------------------------------------------------------------------------

# E1: 24 explicit feature -> primary component.
# E2: 24 explicit component -> component (first is the Q-10 target COMP-M-03 -> COMP-M-02).
# E5:  4 explicit feature -> third-party component (first is the Q-12 target).
# E3:  8 explicit feature -> feature depends_on.
# E4:  6 explicit feature -> feature ordering (first is the Q-11 target).
# E6: 12 explicit pbi -> pbi.
# E7: 26 explicit pbi -> component.

E2_M = [
    ("COMP-M-03", "COMP-M-02"),
    ("COMP-M-07", "COMP-M-02"),
    ("COMP-M-04", "COMP-M-05"),
    ("COMP-M-08", "COMP-M-03"),
    ("COMP-M-10", "COMP-M-02"),
    ("COMP-M-02", "COMP-M-05"),
    ("COMP-M-06", "COMP-M-05"),
    ("COMP-M-05", "COMP-M-01"),
    ("COMP-M-09", "COMP-M-05"),
    ("COMP-M-01", "COMP-M-05"),
    ("COMP-M-08", "COMP-M-05"),
    ("COMP-M-07", "COMP-M-05"),
]
E2_T = [
    ("COMP-T-02", "COMP-T-01"),
    ("COMP-T-05", "COMP-T-01"),
    ("COMP-T-05", "COMP-T-03"),
    ("COMP-T-04", "COMP-T-01"),
    ("COMP-T-06", "COMP-T-01"),
    ("COMP-T-07", "COMP-T-01"),
    ("COMP-T-08", "COMP-T-01"),
    ("COMP-T-01", "COMP-T-03"),
    ("COMP-T-02", "COMP-T-05"),
    ("COMP-T-07", "COMP-T-03"),
    ("COMP-T-08", "COMP-T-05"),
    ("COMP-T-06", "COMP-T-05"),
]

E5 = [
    ("FEAT-M-01", "COMP-M-01"),
    ("FEAT-M-08", "COMP-M-06"),
    ("FEAT-T-01", "COMP-T-03"),
    ("FEAT-T-03", "COMP-T-03"),
]

E3 = [
    ("FEAT-M-05", "FEAT-M-04"),
    ("FEAT-M-06", "FEAT-M-03"),
    ("FEAT-M-09", "FEAT-M-07"),
    ("FEAT-M-12", "FEAT-M-05"),
    ("FEAT-T-10", "FEAT-T-01"),
    ("FEAT-T-02", "FEAT-T-06"),
    ("FEAT-T-12", "FEAT-T-07"),
    ("FEAT-T-09", "FEAT-T-08"),
]

E4 = [
    ("FEAT-M-02", "FEAT-M-01"),
    ("FEAT-M-08", "FEAT-M-01"),
    ("FEAT-M-11", "FEAT-M-03"),
    ("FEAT-T-04", "FEAT-T-01"),
    ("FEAT-T-05", "FEAT-T-04"),
    ("FEAT-T-12", "FEAT-T-04"),
]

E6_M = [("PBI-M-002", "PBI-M-001"), ("PBI-M-007", "PBI-M-006"),
        ("PBI-M-012", "PBI-M-011"), ("PBI-M-017", "PBI-M-016"),
        ("PBI-M-022", "PBI-M-021"), ("PBI-M-027", "PBI-M-026")]
E6_T = [("PBI-T-002", "PBI-T-001"), ("PBI-T-007", "PBI-T-006"),
        ("PBI-T-012", "PBI-T-011"), ("PBI-T-017", "PBI-T-016"),
        ("PBI-T-022", "PBI-T-021"), ("PBI-T-027", "PBI-T-026")]

# I1: 24 implicit feature -> component (first is the Q-13/Q-16/Q-19 target;
#     the first-runbook evidence belongs to COMP-M-05).
I1_M = [
    ("FEAT-M-03", "COMP-M-05"), ("FEAT-M-01", "COMP-M-02"),
    ("FEAT-M-02", "COMP-M-06"), ("FEAT-M-04", "COMP-M-10"),
    ("FEAT-M-05", "COMP-M-03"), ("FEAT-M-06", "COMP-M-02"),
    ("FEAT-M-07", "COMP-M-02"), ("FEAT-M-08", "COMP-M-02"),
    ("FEAT-M-09", "COMP-M-02"), ("FEAT-M-10", "COMP-M-03"),
    ("FEAT-M-11", "COMP-M-05"), ("FEAT-M-12", "COMP-M-05"),
]
I1_T = [
    ("FEAT-T-01", "COMP-T-01"), ("FEAT-T-02", "COMP-T-01"),
    ("FEAT-T-03", "COMP-T-01"), ("FEAT-T-04", "COMP-T-03"),
    ("FEAT-T-05", "COMP-T-01"), ("FEAT-T-06", "COMP-T-02"),
    ("FEAT-T-07", "COMP-T-01"), ("FEAT-T-08", "COMP-T-05"),
    ("FEAT-T-09", "COMP-T-02"), ("FEAT-T-10", "COMP-T-01"),
    ("FEAT-T-11", "COMP-T-02"), ("FEAT-T-12", "COMP-T-01"),
]

# I3: 14 implicit feature -> feature depends_on (first is the Q-15 target).
I3_M = [
    ("FEAT-M-09", "FEAT-M-08"), ("FEAT-M-07", "FEAT-M-02"),
    ("FEAT-M-10", "FEAT-M-06"), ("FEAT-M-11", "FEAT-M-09"),
    ("FEAT-M-12", "FEAT-M-06"), ("FEAT-M-01", "FEAT-M-02"),
]
I3_T = [
    ("FEAT-T-08", "FEAT-T-04"), ("FEAT-T-06", "FEAT-T-04"),
    ("FEAT-T-05", "FEAT-T-03"), ("FEAT-T-10", "FEAT-T-03"),
    ("FEAT-T-12", "FEAT-T-04"), ("FEAT-T-11", "FEAT-T-01"),
    ("FEAT-T-09", "FEAT-T-06"), ("FEAT-T-02", "FEAT-T-04"),
]

# I2: 2 implicit ordering (first is the Q-14/Q-20 target).
I2 = [
    ("FEAT-T-01", "FEAT-T-04"),
    ("FEAT-M-08", "FEAT-M-03"),
]

# I4: 3 implicit requirement -> component (first is the Q-21 target:
#     REQ-M-03 is defined by the superseded PRD-M-02 v1).
I4 = [
    ("REQ-M-03", "COMP-M-03"),
    ("REQ-T-01", "COMP-T-02"),
    ("REQ-M-01", "COMP-M-06"),
]

TICKET_PATTERN = [2, 2, 2, 2, 1, 2, 1, 1, 2, 1, 2, 2]  # 20 per product


def _story_text(spec: dict, k: int) -> tuple[str, str]:
    scenes = [
        ("capture the first useful moment", "so a person sees value before the full "
         "experience is there"),
        ("make the next step obvious", "so it is clear what to do next"),
        ("let a mistake be undone", "so a wrong tap never costs progress"),
        ("keep a record of what changed", "so there is a visible trail of the change"),
        ("explain why it happened", "so the reason is visible rather than hidden"),
    ]
    personas = {
        MER: ["new starter", "payroll admin", "line manager", "employee",
              "compliance officer"],
        TAL: ["casual keeper", "streak chaser", "planner", "new user", "friend"],
    }
    action, reason = scenes[k]
    persona = personas[spec["product"]][(FEATURE_SPECS.index(spec) + k) % 5]
    term = spec["colloquial"][0]
    title = f"{spec['name']} - {action}"
    description = (f"As a {persona} I want to {action} {term} {reason}. "
                   f"This touches the {COMPONENTS_BY_ID[spec['comp']]['name'].lower()}.")
    return title, description


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

FEATURE_INDEX = {s["id"]: i for i, s in enumerate(FEATURE_SPECS)}


def feature_order(product: str) -> list[dict]:
    return [s for s in FEATURE_SPECS if s["product"] == product]


def build_final_corpus() -> SourceModel:
    products = [
        Product(product_id=MER, name="Meridian", domain="HRTech",
                documentation_maturity="formal", team_size=14),
        Product(product_id=TAL, name="Tally", domain="Consumer habit-tracking",
                documentation_maturity="informal", team_size=5),
    ]

    # --- features (29 entities after version expansion -> 29 documents) -----
    features: list[Feature] = []
    for spec in FEATURE_SPECS:
        base = dict(
            feature_id=spec["id"], product_id=spec["product"], name=spec["name"],
            status=spec["status"], priority=spec["priority"],
            formal_term=spec["formal"], colloquial_terms=spec["colloquial"],
            summary=spec["summary"], confusable_with=spec["confusable"],
            requirement_id=spec["req"],
        )
        if spec["id"] in VERSIONED_FEATURES:
            features.append(Feature(
                **base,
                approval_limit=spec.get("approval_limit_v1",
                                        spec.get("approval_limit", "")),
                document_id=_fid(spec["id"], "1.0"), version="1.0",
                version_status="superseded", created_date="2026-02-10",
                modified_date="2026-02-10",
                superseded_by=_fid(spec["id"], "2.0"), supersedes="",
                is_current=False))
            features.append(Feature(
                **base, approval_limit=spec.get("approval_limit", ""),
                document_id=_fid(spec["id"], "2.0"), version="2.0",
                version_status="current", created_date="2026-02-10",
                modified_date="2026-07-22",
                superseded_by="", supersedes=_fid(spec["id"], "1.0"),
                is_current=True))
        else:
            features.append(Feature(
                **base, document_id=_fid(spec["id"], "1.0"), version="1.0",
                version_status="current", created_date="2026-03-04",
                modified_date="2026-03-04",
                superseded_by="", supersedes="", is_current=True))

    # --- PRDs (17 entities -> 17 documents) ---------------------------------
    prds: list[Prd] = []
    for spec in PRD_SPECS:
        req_ids = sorted(r["id"] for r in REQUIREMENT_SPECS if r["prd"] == spec["id"])
        if spec["versioned"]:
            v1_sections = ["Background", "Goals", "Non-goals", "Requirements",
                           "Success measures", "Open questions"]
            v2_sections = ["Background", "Goals", "Non-goals", "Requirements",
                           "Success measures", "Open questions"]
            if spec["product"] == MER:
                v2_sections.append("Change log")
            prds.append(Prd(
                prd_id=spec["id"], product_id=spec["product"], title=spec["title"],
                author_role=spec["author_role"], is_normative=True,
                summary=spec["summary"], sections=v1_sections,
                requirement_ids=req_ids,
                document_id=_pid(spec["id"], "1.0"), version="1.0",
                version_status="superseded", created_date="2026-02-02",
                modified_date="2026-02-02",
                superseded_by=_pid(spec["id"], "2.0"), supersedes="",
                is_current=False))
            prds.append(Prd(
                prd_id=spec["id"], product_id=spec["product"], title=spec["title"],
                author_role=spec["author_role"], is_normative=True,
                summary=spec["summary"], sections=v2_sections,
                requirement_ids=req_ids,
                document_id=_pid(spec["id"], "2.0"), version="2.0",
                version_status="current", created_date="2026-02-02",
                modified_date="2026-07-18",
                superseded_by="", supersedes=_pid(spec["id"], "1.0"),
                is_current=True))
        else:
            prds.append(Prd(
                prd_id=spec["id"], product_id=spec["product"], title=spec["title"],
                author_role=spec["author_role"], is_normative=True,
                summary=spec["summary"],
                sections=["Background", "Goals", "Non-goals", "Requirements",
                          "Success measures", "Open questions"],
                requirement_ids=req_ids,
                document_id=_pid(spec["id"], "1.0"), version="1.0",
                version_status="current", created_date="2026-04-10",
                modified_date="2026-04-10",
                superseded_by="", supersedes="", is_current=True))

    requirements = [
        Requirement(requirement_id=r["id"], prd_id=r["prd"], product_id=r["product"],
                    title=r["title"], statement=r["statement"], is_normative=True)
        for r in REQUIREMENT_SPECS
    ]

    # --- components (18) ------------------------------------------------------
    components = []
    for chain, product in ((M_COMP, MER), (T_COMP, TAL)):
        for index, comp_id in enumerate(chain):
            spec = COMPONENTS_BY_ID[comp_id]
            adjacent = []
            if index > 0:
                adjacent.append(chain[index - 1])
            if index < len(chain) - 1:
                adjacent.append(chain[index + 1])
            components.append(TechnicalComponent(
                component_id=comp_id, name=spec["name"],
                component_type=spec["kind"], owner_team=spec["owner"],
                notes=spec["notes"], adjacent_component_ids=adjacent))

    # --- PBIs (120) ---------------------------------------------------------
    pbis: list[Pbi] = []
    pbis_by_feature: dict[str, list[Pbi]] = {}
    for product in (MER, TAL):
        counter = 0
        for spec in feature_order(product):
            fid = spec["id"]
            for k in range(5):
                counter += 1
                pbi_id = f"PBI-{product[-1]}-{counter:03d}"
                comp = (M_COMP if product == MER else T_COMP)[
                    (FEATURE_INDEX[fid] * 5 + k) % len(M_COMP if product == MER else T_COMP)]
                title, description = _story_text(spec, k)
                status = ["to_do", "in_progress", "in_review", "done"][
                    (FEATURE_INDEX[fid] + k) % 4]
                pbi = Pbi(
                    pbi_id=pbi_id, product_id=product, feature_id=fid,
                    title=title, description=description,
                    story_points=1 + (FEATURE_INDEX[fid] + k) % 5,
                    status=status,
                    created_date=f"2026-{1 + (FEATURE_INDEX[fid] + k) % 9:02d}-"
                                 f"{10 + (k * 7) % 18:02d}",
                    author_role="Product Owner" if product == MER else "Founder",
                    component_id=comp)
                pbis.append(pbi)
                pbis_by_feature.setdefault(fid, []).append(pbi)

    # --- tickets (40) ---------------------------------------------------------
    tickets: list[Ticket] = []
    complaints = [
        "It asked me to do {term} at a random moment and then lost it when I left the page.",
        "I clicked through {term} and nothing happened, but it said done anyway.",
        "The {term} thing kept coming back even after I had sorted it once.",
        "I could not tell what {term} had actually changed until the next day.",
        "The screen for {term} was so slow that I gave up and closed the app.",
    ]
    segments = {
        MER: ["new starter", "payroll admin", "line manager", "compliance officer",
              "employee"],
        TAL: ["casual keeper", "streak chaser", "planner", "new user", "friend"],
    }
    for product in (MER, TAL):
        counter = 0
        for spec in feature_order(product):
            fid = spec["id"]
            for _t in range(TICKET_PATTERN[feature_order(product).index(spec)]):
                counter += 1
                ticket_id = f"TKT-{product[-1]}-{counter:03d}"
                pbi = pbis_by_feature[fid][_t % 5]
                comp = (M_COMP if product == MER else T_COMP)[
                    (FEATURE_INDEX[fid] + counter) % len(M_COMP if product == MER else T_COMP)]
                tickets.append(Ticket(
                    ticket_id=ticket_id, product_id=product, feature_id=fid,
                    related_component_id=comp, pbi_id=pbi.pbi_id,
                    reported_symptom=complaints[(_t + FEATURE_INDEX[fid]) % 5].format(
                        term=spec["colloquial"][0]),
                    customer_segment=segments[product][
                        (FEATURE_INDEX[fid] + counter) % 5],
                    severity=["low", "medium", "high"][counter % 3],
                    opened_date=f"2026-{1 + (FEATURE_INDEX[fid] + counter) % 9:02d}-"
                                f"{3 + (counter * 5) % 20:02d}",
                    reporter_role="Support agent"))

    # --- decisions (16) -------------------------------------------------------
    decisions = _build_decisions()

    # --- meeting notes (24) ---------------------------------------------------
    meeting_notes = _build_notes(pbis_by_feature)

    # --- runbooks (8) ---------------------------------------------------------
    runbooks = _build_runbooks()

    # --- dependencies (208) ---------------------------------------------------
    dependencies = _build_dependencies(pbis)

    # --- conflicts (12) -------------------------------------------------------
    conflicts = _build_conflicts()

    # --- links ------------------------------------------------------------------
    document_links = _build_links(features, prds, pbis, tickets, decisions,
                                  meeting_notes, runbooks, components)

    model = SourceModel(
        model_version="v1-final-corpus",
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
        document_links=document_links,
    )
    _assert_targets(model)
    return model


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------

def _build_decisions() -> list[DecisionRecord]:
    specs = [
        ("DEC-M-01", MER, "FEAT-M-01",
         "Move tax collection to day three of the onboarding ramp rather than during sign-up.",
         "Early testing showed the long sign-up form caused abandonment in the first "
         "session. Asking once the user has seen value raised tax-step completion.",
         "2026-07-16", "Senior Product Manager"),
        ("DEC-M-02", MER, "FEAT-M-03",
         "Release bulk approval for whole batches only; no partial-batch approval.",
         "Partial-batch approval complicates the audit trail and is not needed by the "
         "managers interviewed.",
         "2026-06-11", "Product Manager"),
        ("DEC-M-03", MER, "FEAT-M-04",
         "Export payroll files nightly at a fixed clock time; never on demand.",
         "A pre-configured schedule keeps provider feeds predictable and matches the "
         "normative requirement.",
         "2026-06-20", "Product Manager"),
        ("DEC-M-04", MER, "FEAT-M-06",
         "The manager console is read-only until an approval is closed.",
         "Editable pending rows caused accidental approvals; closing first removed the "
         "class of error.",
         "2026-05-30", "Engineering lead"),
        ("DEC-M-05", MER, "FEAT-M-09",
         "Payslips are viewable on demand in the app; no payslip email delivery.",
         "Emails with payslip attachments failed security review. On-demand access meets "
         "the self-service requirement.",
         "2026-07-02", "Security lead"),
        ("DEC-M-06", MER, "FEAT-M-12",
         "Audit trail retains exportable records for 24 months.",
         "Compliance review requires at least 24 months of approval and payroll events.",
         "2026-08-14", "Compliance Product Manager"),
        ("DEC-M-07", MER, "FEAT-M-05",
         "Reporting reflects only approved hours from the ledger.",
         "Finance reconciliation is only trustworthy when unapproved hours are excluded.",
         "2026-06-30", "Finance lead"),
        ("DEC-M-08", MER, "FEAT-M-07",
         "Benefits enrolment requires a verified identity first.",
         "Unverified enrolment produced duplicate perks. Verification is mandatory before "
         "any benefits are applied.",
         "2026-08-20", "Product Manager"),
        ("DEC-T-01", TAL, "FEAT-T-01",
         "Ship the streak saver prompt only in the evening, not on waking.",
         "Morning prompts were dismissed unread. Evening is when people already open the app.",
         "2026-08-01", "Founder"),
        ("DEC-T-02", TAL, "FEAT-T-03",
         "Reminders never exceed one prompt per habit per day.",
         "A second prompt each day raised mute rates. One prompt keeps the schedule honest.",
         "2026-08-06", "Founder"),
        ("DEC-T-03", TAL, "FEAT-T-05",
         "Issue at most four freeze tokens per user per year.",
         "An unlimited token supply makes streaks meaningless; four is visible, limited "
         "and honest.",
         "2026-08-09", "Founder"),
        ("DEC-T-04", TAL, "FEAT-T-12",
         "The Team Challenges reward tier was deprioritised for this quarter and stays in "
         "the backlog.",
         "Streak retention does not yet hold well enough for challenges to help. The "
         "reward tier is deferred rather than cancelled.",
         "2026-08-24", "Founder"),
        ("DEC-T-05", TAL, "FEAT-T-04",
         "Recurring habits default to weekly and let the user override the day and time.",
         "A weekly default matched the most common plan without drifting, and the override "
         "covers the rest.",
         "2026-09-01", "Founder"),
        ("DEC-T-06", TAL, "FEAT-T-06",
         "Badges are awarded retroactively from existing history.",
         "People who already held a milestone would resub them; retroactive awarding "
         "reflects real progress.",
         "2026-09-05", "Founder"),
        ("DEC-T-07", TAL, "FEAT-T-07",
         "Sharing defaults to friends only and can be revoked at any time.",
         "The requirement treats sharing as explicit and reversible; friends-only is the "
         "smallest surface that satisfies it.",
         "2026-09-10", "Founder"),
        ("DEC-T-08", TAL, "FEAT-T-02",
         "Adopting a template requires an active account.",
         "One-step adoption of a pack is useless if the account is about to break a "
         "streak; onboarding must settle first.",
         "2026-09-12", "Founder"),
    ]
    return [
        DecisionRecord(decision_id=did, product_id=prod, about_entity_id=feat,
                       decision=decision, rationale=rationale,
                       decided_date=date, decided_by_role=role)
        for did, prod, feat, decision, rationale, date, role in specs
    ]


# ---------------------------------------------------------------------------
# Meeting notes
# ---------------------------------------------------------------------------

def _build_notes(pbis_by_feature: dict[str, list[Pbi]]) -> list[MeetingNote]:
    notes: list[MeetingNote] = []
    for product, order in ((MER, [0, 2, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
                           (TAL, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])):
        for index, fid_index in enumerate(order, start=1):
            spec = feature_order(product)[fid_index]
            fid = spec["id"]
            pbi = pbis_by_feature[fid][0]
            topics = [
                f"{spec['name']}: the {spec['colloquial'][0]} flow is the busy part of "
                f"the quarter",
                f"Agreed to keep {spec['confusable'][0]} separate so the naming cannot "
                f"be confused in support",
                f"Follow up on how {spec['comp']} behaves before we commit to a date",
            ]
            product_slug = "M" if product == MER else "T"
            notes.append(MeetingNote(
                note_id=f"NOTE-{product_slug}-{index:02d}", product_id=product,
                about_entity_ids=[fid, pbi.pbi_id],
                meeting_date=f"2026-{1 + (fid_index * 3) % 9:02d}-{12 + index % 15:02d}",
                attendees_role=["Product Manager", "Engineering lead"]
                if product == MER else ["Founder"],
                topics=topics))
    return notes


# ---------------------------------------------------------------------------
# Runbooks
# ---------------------------------------------------------------------------

def _build_runbooks() -> list[Runbook]:
    table = [
        ("RBK-M-01", MER, "COMP-M-05", "Domain Event Bus: recovering a delayed event",
         ["A delayed event shows up in the bus metrics as lag above 5 seconds.",
          "Check the consumer group lag and restart the stalled consumer.",
          "Do not drop the event; the ledger update depends on it completing.",
          "If lag persists after two restarts, page the platform team."],
         "2026-08-05"),
        ("RBK-M-02", MER, "COMP-M-02", "Payroll Ledger: overnight reconciliation",
         ["Verify the ledger and the export totals match within tolerance.",
          "Re-run the export job if totals diverge; do not edit records by hand.",
          "Record the drift in the audit trail before closing the run."],
         "2026-08-10"),
        ("RBK-M-03", MER, "COMP-M-06", "TaxBand rate service: handling rate-limit responses",
         ["A 429 from the rate service means the 20 calls/minute budget is exhausted.",
          "Back off for 30 seconds, then retry the single call. Do not retry the batch.",
          "If three consecutive batches fail, raise an operations alert; the tax step "
          "cannot complete without resolved rates."],
         "2026-08-12"),
        ("RBK-M-04", MER, "COMP-M-01", "Verisign identity verification: timeout handling",
         ["A timeout means the verification did not return a decision.",
          "Requeue the verification with a fresh correlation id.",
          "Never auto-approve on timeout; the payment privilege must wait."],
         "2026-08-15"),
        ("RBK-T-01", TAL, "COMP-T-01", "Habit Store: repairing a split log",
         ["A split log shows two streak states for one user.",
          "Merge the log entries by timestamp and recompute the streak.",
          "Advise the user if recovery prompts were skipped while broken."],
         "2026-08-18"),
        ("RBK-T-02", TAL, "COMP-T-03", "Push gateway: quiet-hours deliveries",
         ["The gateway may delay pushes outside control.",
          "Treat a delayed push as delivered-late, not failed.",
          "Do not retry the same prompt; a second copy reads as nagging."],
         "2026-08-20"),
        ("RBK-T-03", TAL, "COMP-T-05", "Prompt Scheduler: silent schedule drift",
         ["Schedules drift when the store write failed silently.",
          "Recompute the next fire time from the habit schedule.",
          "Recovery prompts are only valid before the streak breaks."],
         "2026-08-22"),
        ("RBK-T-04", TAL, "COMP-T-02", "Streak Calculator: inconsistent streak state",
         ["Two reads of the same log disagree on streak length.",
          "Purge duplicate log writes, then recompute from the canonical log.",
          "Freeze tokens must be rebalanced after any recompute."],
         "2026-08-25"),
    ]
    return [
        Runbook(runbook_id=r_id, product_id=product, component_id=comp, title=title,
                steps=steps, last_reviewed=reviewed)
        for r_id, product, comp, title, steps, reviewed in table
    ]


# ---------------------------------------------------------------------------
# Dependencies (208, exact split)
# ---------------------------------------------------------------------------

def _comp_name(comp_id: str) -> str:
    return COMPONENTS_BY_ID[comp_id]["name"]


def _build_dependencies(pbis: list[Pbi]) -> list[Dependency]:
    deps: list[Dependency] = []
    counter = [0]

    def add(from_type, from_id, to_type, to_id, dep_type, description, explicitness):
        counter[0] += 1
        deps.append(Dependency(
            dependency_id=f"DEP-{counter[0]:04d}",
            from_type=from_type, from_id=from_id, to_type=to_type, to_id=to_id,
            dependency_type=dep_type, description=description, explicitness=explicitness))

    # --------------------------- EXPLICIT (104) ---------------------------
    # E1 (24): feature -> primary component; #1 is the Q-09 target.
    for spec in FEATURE_SPECS:
        add("feature", spec["id"], "component", spec["comp"], "depends_on",
            f"{spec['name']} depends on the {_comp_name(spec['comp']).lower()} to provide "
            f"this behaviour, as stated in this specification.",
            "explicit")
    # E2 (24): component -> component; #1 is the Q-10 target.
    for from_id, to_id in E2_M + E2_T:
        add("component", from_id, "component", to_id, "depends_on",
            f"{_comp_name(from_id)} depends on the {_comp_name(to_id).lower()} to perform "
            f"its work, as stated in this component document.",
            "explicit")
    # E5 (4): feature -> third-party component; #1 is the Q-12 target.
    for from_id, to_id in E5:
        add("feature", from_id, "component", to_id, "depends_on",
            f"{from_id} relies on the third-party service {_comp_name(to_id)}; stated in "
            f"the specification.",
            "explicit")
    # E3 (8): feature -> feature depends_on.
    for from_id, to_id in E3:
        add("feature", from_id, "feature", to_id, "depends_on",
            f"{from_id} depends on {to_id} to complete the flow; stated in the "
            f"specification.",
            "explicit")
    # E4 (6): feature -> feature ordering; #1 is the Q-11 target.
    for from_id, to_id in E4:
        add("feature", from_id, "feature", to_id, "ordering",
            f"{from_id} is ordered to run before {to_id} in the product sequence; stated "
            f"in the specification.",
            "explicit")
    # E6 (12): pbi -> pbi.
    for from_id, to_id in E6_M + E6_T:
        add("pbi", from_id, "pbi", to_id, "depends_on",
            f"{from_id} depends on {to_id} being complete, as stated in this backlog item.",
            "explicit")
    # E7 (26): pbi -> component.
    for i in range(13):
        add("pbi", f"PBI-M-{i + 1:03d}", "component", M_COMP[(i * 3) % 10],
            "depends_on",
            f"PBI-M-{i + 1:03d} operates directly on the {_comp_name(M_COMP[(i * 3) % 10]).lower()} "
            f"as stated in the item.",
            "explicit")
    for i in range(13):
        to = T_COMP[(i * 2) % 8]
        add("pbi", f"PBI-T-{i + 1:03d}", "component", to, "depends_on",
            f"PBI-T-{i + 1:03d} operates directly on the {_comp_name(to).lower()} as "
            f"stated in the item.",
            "explicit")

    # --------------------------- IMPLICIT (104) ---------------------------
    # I1 (24): feature -> component; #1 is the Q-13/Q-16/Q-19 target.
    for i, (from_id, to_id) in enumerate(I1_M + I1_T):
        if i == 0:
            description = ("No document states this. Bulk approvals must publish approval "
                           "events before the ledger is updated, and the Domain Event Bus "
                           "is the only mechanism that carries them.")
        else:
            description = ("No document states this; it follows from the feature's "
                           "responsibility and the component's role in the product.")
        add("feature", from_id, "component", to_id, "depends_on", description, "implicit")
    # I3 (14): feature -> feature depends_on; #1 is the Q-15 target.
    for i, (from_id, to_id) in enumerate(I3_M + I3_T):
        if i == 0:
            description = ("No document states this. Reflection Prompts can only surface "
                           "for habits that Recurring Habit Scheduling has already created.")
        else:
            description = ("No document states this; the dependency follows from how the "
                           "two features share state.")
        add("feature", from_id, "feature", to_id, "depends_on", description, "implicit")
    # I2 (2): feature -> feature ordering; #1 is the Q-14/Q-20 target.
    for i, (from_id, to_id) in enumerate(I2):
        if i == 0:
            description = ("No document states an order between them, but the streak saver "
                           "can only offer an easier alternative once a recurring schedule "
                           "exists; the sequence is implied by the PRD.")
        else:
            description = ("No document states the order; tax adjustments must land before "
                           "bulk approvals pay out at the new rate, implied by the PRD "
                           "sequence.")
        add("feature", from_id, "feature", to_id, "ordering", description, "implicit")
    # I4 (3): requirement -> component; #1 is the Q-21 target.
    for i, (from_id, to_id) in enumerate(I4):
        if i == 0:
            description = ("No document states this. The bulk-approval requirement implies "
                           "the approval engine; the only textual evidence of the coupling "
                           "sits in the superseded PRD-M-02 v1.")
        elif i == 1:
            description = ("No document states this; the streak-mitigation requirement "
                           "implies the streak calculator.")
        else:
            description = ("No document states this; the progressive-tax requirement "
                           "implies the tax band rate service.")
        add("requirement", from_id, "component", to_id, "depends_on", description,
            "implicit")
    # I5 (40): pbi -> pbi.
    for i in range(20):
        frm = f"PBI-M-{i + 1:03d}"
        to = f"PBI-M-{(i + 2) % 60 + 1:03d}"
        add("pbi", frm, "pbi", to, "depends_on",
            "No document states this; the two backlog items share a feature and only one "
            "can land first.",
            "implicit")
    for i in range(20):
        frm = f"PBI-T-{i + 1:03d}"
        to = f"PBI-T-{(i + 2) % 60 + 1:03d}"
        add("pbi", frm, "pbi", to, "depends_on",
            "No document states this; the two backlog items share a feature and only one "
            "can land first.",
            "implicit")
    # I6 (21): pbi -> component.
    for i in range(11):
        to = M_COMP[(i * 5 + 2) % 10]
        add("pbi", f"PBI-M-{i + 1:03d}", "component", to, "depends_on",
            "No document states this; the item's behaviour requires the component's "
            "capability.",
            "implicit")
    for i in range(10):
        to = T_COMP[(i * 3 + 1) % 8]
        add("pbi", f"PBI-T-{i + 1:03d}", "component", to, "depends_on",
            "No document states this; the item's behaviour requires the component's "
            "capability.",
            "implicit")

    return deps


# ---------------------------------------------------------------------------
# Conflicts (12: 7 resolved / 5 unresolved)
# ---------------------------------------------------------------------------

def _build_conflicts() -> list[Conflict]:
    return [
        Conflict(conflict_id="CONF-M-01", product_id=MER,
                 document_a_id=_pid("PRD-M-01", "1.0"),
                 document_b_id=_fid("FEAT-M-01", "1.0"),
                 conflict_type="stale_requirement",
                 description="PRD-M-01 v1 and the Progressive Profiling v1 spec both "
                             "require tax details during initial registration. DEC-M-01 "
                             "later moved the tax step to day three of the ramp.",
                 is_resolved=True,
                 resolution_note="Resolved by PRD-M-01 v2, which is normative. Both v1 "
                                 "documents remain in the repository and are now stale.",
                 resolved_by_document_id=_pid("PRD-M-01", "2.0")),
        Conflict(conflict_id="CONF-M-02", product_id=MER,
                 document_a_id=_fid("FEAT-M-04", "1.0"),
                 document_b_id=_fid("FEAT-M-04", "2.0"),
                 conflict_type="inconsistent_claim",
                 description="Payroll Export Scheduling v1 runs exports a half hour before "
                             "the ledger closes; v2 runs them after close. Both versions "
                             "are still in the repository.",
                 is_resolved=True,
                 resolution_note="Resolved by FEAT-M-04 v2, which confirms the late slot.",
                 resolved_by_document_id=_fid("FEAT-M-04", "2.0")),
        Conflict(conflict_id="CONF-M-03", product_id=MER,
                 document_a_id=_fid("FEAT-M-03", "1.0"),
                 document_b_id=_fid("FEAT-M-06", "1.0"),
                 conflict_type="incompatible_scope",
                 description="Bulk Timesheet Approval allows partial-batch approval while "
                             "the Manager Approval Console treats batches as indivisible.",
                 is_resolved=True,
                 resolution_note="Resolved by PRD-M-02 v2 and DEC-M-02: whole-batch only.",
                 resolved_by_document_id=_pid("PRD-M-02", "2.0")),
        Conflict(conflict_id="CONF-M-04", product_id=MER,
                 document_a_id=_fid("FEAT-M-05", "1.0"),
                 document_b_id=_pid("PRD-M-03", "1.0"),
                 conflict_type="scope_mismatch",
                 description="Approved Hours Reporting claims to include provisional "
                             "totals; PRD-M-03 v1 limits reporting to approved hours only.",
                 is_resolved=True,
                 resolution_note="Resolved by PRD-M-03 v2 and DEC-M-07. Reporting reflects "
                                 "approved hours only.",
                 resolved_by_document_id=_pid("PRD-M-03", "2.0")),
        Conflict(conflict_id="CONF-M-05", product_id=MER,
                 document_a_id=_fid("FEAT-M-09", "1.0"),
                 document_b_id=_pid("PRD-M-04", "1.0"),
                 conflict_type="retention_mismatch",
                 description="Self-Serve Payslips keeps every generated payslip for 36 "
                             "months; PRD-M-04 states a 24-month self-service window.",
                 is_resolved=False,
                 resolution_note="", resolved_by_document_id=""),
        Conflict(conflict_id="CONF-M-06", product_id=MER,
                 document_a_id=_fid("FEAT-M-12", "1.0"),
                 document_b_id=_pid("PRD-M-06", "1.0"),
                 conflict_type="timing_mismatch",
                 description="Audit Trail Export exports events every hour; the audit "
                             "store is append-only and only flushes daily.",
                 is_resolved=False,
                 resolution_note="", resolved_by_document_id=""),
        Conflict(conflict_id="CONF-M-07", product_id=MER,
                 document_a_id=_fid("FEAT-M-11", "1.0"),
                 document_b_id=_pid("PRD-M-05", "1.0"),
                 conflict_type="unsettled_timing",
                 description="Leaver Processing pays final salary in the next run; "
                             "PRD-M-05 leaves the timing to a follow-up decision.",
                 is_resolved=False,
                 resolution_note="", resolved_by_document_id=""),
        Conflict(conflict_id="CONF-T-01", product_id=TAL,
                 document_a_id=_fid("FEAT-T-01", "1.0"),
                 document_b_id=_fid("FEAT-T-01", "2.0"),
                 conflict_type="inconsistent_claim",
                 description="Streak Recovery v1 states the prompt fires on waking. v2 "
                             "states it fires in the evening (DEC-T-01).",
                 is_resolved=True,
                 resolution_note="Resolved by FEAT-T-01 v2; the v1 spec is retained for "
                                 "history.",
                 resolved_by_document_id=_fid("FEAT-T-01", "2.0")),
        Conflict(conflict_id="CONF-T-02", product_id=TAL,
                 document_a_id=_fid("FEAT-T-05", "1.0"),
                 document_b_id=_fid("FEAT-T-05", "2.0"),
                 conflict_type="inconsistent_claim",
                 description="Streak Freeze Tokens v1 allows ten tokens a year; v2 allows "
                             "max four (DEC-T-03).",
                 is_resolved=True,
                 resolution_note="Resolved by FEAT-T-05 v2; the limit is four per year.",
                 resolved_by_document_id=_fid("FEAT-T-05", "2.0")),
        Conflict(conflict_id="CONF-T-03", product_id=TAL,
                 document_a_id=_fid("FEAT-T-03", "1.0"),
                 document_b_id=_fid("FEAT-T-10", "1.0"),
                 conflict_type="escalation_disagreement",
                 description="Evening Reminder Builder sets one reminder per habit; the "
                             "Gentle Escalation Flow wants a second nudge before a "
                             "streak is written off.",
                 is_resolved=False,
                 resolution_note="", resolved_by_document_id=""),
        Conflict(conflict_id="CONF-T-04", product_id=TAL,
                 document_a_id=_fid("FEAT-T-02", "1.0"),
                 document_b_id=_pid("PRD-T-02", "1.0"),
                 conflict_type="one_step_scope",
                 description="The Template Marketplace spec shows templates adopted with "
                             "an empty-handed account; PRD-T-02 v1 requires an active "
                             "account first.",
                 is_resolved=True,
                 resolution_note="Resolved by PRD-T-02 v2, following DEC-T-08.",
                 resolved_by_document_id=_pid("PRD-T-02", "2.0")),
        Conflict(conflict_id="CONF-T-05", product_id=TAL,
                 document_a_id=_fid("FEAT-T-07", "1.0"),
                 document_b_id=_pid("PRD-T-04", "1.0"),
                 conflict_type="sharing_defaults",
                 description="Habit Sharing Board makes shared streaks public by default; "
                             "PRD-T-04 v1 requires explicit, revocable sharing.",
                 is_resolved=False,
                 resolution_note="", resolved_by_document_id=""),
    ]


# ---------------------------------------------------------------------------
# Cross-document links
# ---------------------------------------------------------------------------

def _build_links(features, prds, pbis, tickets, decisions, meeting_notes, runbooks,
                 components) -> list[DocumentLink]:
    links: list[DocumentLink] = []
    counter = [0]

    def link(from_doc, to_type, to_id, link_type):
        counter[0] += 1
        links.append(DocumentLink(
            link_id=f"LNK-{counter[0]:04d}", from_document_id=from_doc,
            to_entity_type=to_type, to_entity_id=to_id, link_type=link_type))

    for prd in prds:
        if prd.supersedes:
            link(prd.document_id, "product", prd.product_id, "supersedes")
        for requirement_id in prd.requirement_ids:
            link(prd.document_id, "requirement", requirement_id, "defines")
    for feature in features:
        if feature.supersedes:
            link(feature.document_id, "product", feature.product_id, "supersedes")
        link(feature.document_id, "product", feature.product_id, "defines")
    for pbi in pbis:
        link(f"DOC-{pbi.pbi_id}", "feature", pbi.feature_id, "implements")
        link(f"DOC-{pbi.pbi_id}", "component", pbi.component_id, "implements")
    for ticket in tickets:
        link(f"DOC-{ticket.ticket_id}", "feature", ticket.feature_id, "implements")
        link(f"DOC-{ticket.ticket_id}", "component", ticket.related_component_id,
             "depends_on")
    for note in meeting_notes:
        for entity_id in note.about_entity_ids:
            link(f"DOC-{note.note_id}",
                 "feature" if entity_id.startswith("FEAT") else "pbi",
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
    for feature in features:
        if not feature.is_current:
            continue
        for other in feature.confusable_with:
            link(feature.document_id, "feature", other, "contextualises")
    link("DOC-PBI-M-002", "pbi", "PBI-M-003", "blocks")
    link("DOC-PBI-T-001", "pbi", "PBI-T-002", "blocks")
    return links


# ---------------------------------------------------------------------------
# Target assertions
# ---------------------------------------------------------------------------

def _assert_targets(model: SourceModel) -> None:
    expected = {
        "products": 2, "features": 29, "prds": 17, "requirements": 16,
        "pbis": 120, "components": 18, "tickets": 40, "decisions": 16,
        "meeting_notes": 24, "runbooks": 8,
    }
    for name, value in expected.items():
        actual = len(getattr(model, name))
        assert actual == value, f"{name}: expected {value}, got {actual}"
    explicit = sum(1 for d in model.dependencies if d.explicitness == "explicit")
    implicit = sum(1 for d in model.dependencies if d.explicitness == "implicit")
    assert len(model.dependencies) == 208, len(model.dependencies)
    assert explicit == 104 and implicit == 104, (explicit, implicit)
    superseded = sum(1 for e in model.all_versioned() if not e.is_current)
    assert superseded == 12, superseded
    resolved = sum(1 for c in model.conflicts if c.is_resolved)
    unresolved = sum(1 for c in model.conflicts if not c.is_resolved)
    assert len(model.conflicts) == 12 and resolved == 7 and unresolved == 5, (
        len(model.conflicts), resolved, unresolved)
    ordering = [d for d in model.dependencies if d.dependency_type == "ordering"]
    assert len(ordering) >= 8, len(ordering)
    assert len(model.document_links) >= 400, len(model.document_links)
    assert not any(d.from_id == d.to_id for d in model.dependencies), "self-dependency"
    pbi_ids = {p.pbi_id for p in model.pbis}
    assert len(pbi_ids) == 120
    feature_ids = {f.feature_id for f in model.features}
    assert len(feature_ids) == 24
    prd_ids = {p.prd_id for p in model.prds}
    assert len(prd_ids) == 10
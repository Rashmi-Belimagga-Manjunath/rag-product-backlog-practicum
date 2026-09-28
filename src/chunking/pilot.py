"""
Long-document chunking pilot.

WHY THIS EXISTS
---------------
The mechanism sample cannot discriminate 1000/200 from 600/100: no sample document exceeds
~239 words, so both configurations emit exactly one chunk per document. The approved
comparison therefore needs documents long enough that the two configurations actually
produce different layouts. This module builds such a pilot from the mechanism sample.

WHAT THIS PILOT IS, AND IS NOT
------------------------------
It IS: a structural test of the packer at approved full-corpus document lengths, using the
real C1-C8 criteria.

It IS NOT: the final corpus, and not a performance experiment. No BM25 and no RAG result is
computed here, and the configuration selection must not be driven by retrieval quality.

TARGET LENGTHS
--------------
Documents are extended to the TOP of each approved word-count range. That is deliberate and
conservative: chunk boundaries are densest at the top of a range, so passing coherence there
bounds the behaviour across the whole range. Testing only the midpoint would understate
boundary pressure.

The pilot does not invent new documents or new entities. It preserves every byte of the
original rendered content and appends additional register-consistent sections, so the
requirements, dependencies, versions and links that C2, C3, C4, C6 and C8 depend on are
still present and still testable.
"""

from __future__ import annotations

import random

from ..data_generation.render_v1 import Document

# Top of each approved range (docs/proposal_corpus_and_queries.md).
PILOT_LENGTH_TARGETS = {
    "prd": 2200,
    "feature_spec": 700,
    "pbi": 130,
    "component_doc": 550,
    "ticket": 160,
    "decision_log": 300,
    "meeting_notes": 110,
    "runbook": 450,
}

# Register-appropriate vocabulary. A document must read in the register its product uses;
# appending a formal register to an informal product would itself be a defect and would make
# C6 (near-duplicate detection) meaningless.
FORMAL_SUBJECTS = [
    "the onboarding workflow", "the compliance pathway",
    "the payment privileges subsystem", "the payroll readiness criteria",
    "the employee activation sequence", "the tax documentation step",
    "the manager approval controls", "the export scheduling configuration",
]
INFORMAL_SUBJECTS = [
    "the onboarding flow", "the compliance bits", "the payment unlock",
    "the payroll sign-off stuff", "the new-hire setup", "the tax paperwork step",
    "the manager sign-off", "the export scheduler",
]
FORMAL_ACTIONS = [
    "is confirmed during the review window", "is recorded against the owning team",
    "is re-tested after each release candidate", "is signed off before the rollout window",
    "is reconciled against the prior reporting period",
    "is reviewed whenever the underlying policy changes",
]
INFORMAL_ACTIONS = [
    "gets checked during the review window", "gets logged against whoever owns it",
    "gets re-tested after every release candidate", "gets signed off before we roll it out",
    "gets compared against last month's numbers", "gets a look whenever the policy changes",
]
FORMAL_ROLLOUT = [
    "Staged rollout proceeds behind a feature flag so that the team can reduce exposure "
    "without a full rollback.",
    "The release is scheduled behind existing maintenance windows to limit disruption.",
    "Early monitoring focuses on completion rate rather than raw request volume.",
    "The owning team publishes a short summary of observed behaviour after each stage.",
    "Any stage that does not meet its stated measure is halted before the next begins.",
]
INFORMAL_ROLLOUT = [
    "We roll this out behind a flag so we can back it out without a full rollback.",
    "The release goes out in our normal maintenance window to keep the noise down.",
    "We are watching completion rate first, not just how many people hit the endpoint.",
    "Whoever owns it will write up what actually happened once each stage is done.",
    "If a stage misses its number we stop there instead of pushing on.",
]
FORMAL_RISKS = [
    "Scope growth in adjacent areas would delay the agreed release date.",
    "Dependence on external parties introduces timing uncertainty outside team control.",
    "Ambiguous ownership at handover points risks silent omission of required checks.",
]
INFORMAL_RISKS = [
    "Scope creep in the neighbouring bits would push the date out.",
    "Relying on other orgs means we are exposed to timing we do not control.",
    "If nobody clearly owns the handoff, steps get quietly dropped.",
]
FORMAL_ALTERNATIVES = [
    "One option was considered and set aside because it duplicates an existing control.",
    "A second option was examined and set aside because it moved risk rather than "
    "reducing it.",
    "A third option was recorded as future work and deliberately excluded here.",
]
INFORMAL_ALTERNATIVES = [
    "We looked at one other option and skipped it - it duplicates something we already have.",
    "We checked a second option and left it out, it just moves the problem around.",
    "A third idea got parked for later rather than being pulled into this.",
]
FORMAL_EDGE = [
    "Behaviour is unchanged when the precondition is not satisfied.",
    "The failure path is reported to the caller rather than silently swallowed.",
    "Repeated submissions are treated idempotently.",
    "Partial completion is retained so the user need not restart the whole sequence.",
]
INFORMAL_EDGE = [
    "Nothing changes if the precondition is not met.",
    "Failures get handed back to the caller instead of vanishing.",
    "Submitting twice is safe - it just does the same thing again.",
    "Part-finished work is kept, so nobody has to start over.",
]
FORMAL_OBS = [
    "Structured logs record the stage reached, without capturing personal data.",
    "Metrics are emitted at stage boundaries so drop-off can be located precisely.",
    "Alerts fire on sustained deviation rather than on single events.",
]
INFORMAL_OBS = [
    "Logs note which stage someone got to, and we do not log personal data.",
    "We emit metrics at each stage so we can see where people drop off.",
    "Alerts only fire when it stays bad for a bit, not on one-off blips.",
]


def _vocabulary(register: str) -> dict:
    if register == "formal":
        return {
            "subjects": FORMAL_SUBJECTS, "actions": FORMAL_ACTIONS,
            "rollout": FORMAL_ROLLOUT, "risks": FORMAL_RISKS,
            "alternatives": FORMAL_ALTERNATIVES, "edge": FORMAL_EDGE,
            "obs": FORMAL_OBS,
        }
    return {
        "subjects": INFORMAL_SUBJECTS, "actions": INFORMAL_ACTIONS,
        "rollout": INFORMAL_ROLLOUT, "risks": INFORMAL_RISKS,
        "alternatives": INFORMAL_ALTERNATIVES, "edge": INFORMAL_EDGE,
        "obs": INFORMAL_OBS,
    }


# Extra sections appended per document type, in document order.
SECTION_PLAN = {
    "prd": [
        "Context and constraints", "Stakeholders and responsibilities",
        "Assumptions", "Sequencing and rollout", "Risks and mitigations",
        "Measurement plan", "Out of scope for this iteration",
    ],
    "feature_spec": [
        "Behavioural details", "Edge cases", "Observability",
        "Rollout notes", "Alternatives considered",
    ],
    "component_doc": [
        "Interfaces", "Failure modes", "Scaling behaviour",
        "Operational notes", "Ownership and support",
    ],
    "pbi": ["Acceptance criteria", "Notes and relationships"],
    "ticket": ["Reproduction", "Expected behaviour", "Workaround"],
    "decision_log": ["Context", "Alternatives considered", "Consequences"],
    "meeting_notes": ["Action items", "Attendees"],
    "runbook": ["Verification steps", "Escalation path", "Common failures"],
}


# Combinatorial filler. The first version of this pilot drew sentences from a pool of
# roughly forty fixed strings, so a 2200-word PRD reused them. C6 then reported 28%
# near-duplicate chunks with similarity up to 1.00 - a real measurement of the FILLER, not
# of the packer. The criteria would have been reported as a chunking defect, which would
# have been wrong. Sentences are now composed from independent slots, giving ~25,000
# combinations, and the pool is a combinatorial product rather than a fixed list.
FORMAL_CONTEXT = [
    "During the review window", "For the next release", "In the current iteration",
    "As part of the rollout", "For the reporting period", "Under the revised process",
    "Once the migration completes", "For new joiners", "At each stage",
    "Following the change", "Before the handover", "After the backfill",
]
INFORMAL_CONTEXT = [
    "During the review window", "For the next release", "In this round of work",
    "As part of the rollout", "For the reporting period", "Under the new process",
    "Once the migration wraps up", "For new joiners", "At each stage",
    "After the change lands", "Before we hand it over", "After the backfill",
]
CONDITIONS = [
    "provided the precondition holds", "unless the exception is approved",
    "while the feature flag stays on", "once the owning team confirms",
    "subject to the review outcome", "if no regression turns up",
    "after the backfill completes", "when the policy window opens",
    "as long as the audit entry exists", "provided nothing downstream changed",
]
# No leading article: the templates supply their own, otherwise the text reads
# "the the measurement sheet".
# CONDITIONS above are preposition-led, so they read correctly after a verb
# ("is signed off IF no regression turns up") but NOT after the conjunction "If", which
# would produce "If unless the exception is approved". IF_CLAUSES are the bare-clause
# forms for the "If" template.
IF_CLAUSES = [
    "the precondition holds", "the exception is approved", "no regression is detected",
    "the owning team confirms", "the audit entry exists",
    "the feature flag remains enabled", "the backfill has completed",
    "the policy window is still open", "the review outcome is unchanged",
    "the release checklist is complete",
]
# Same reason as IF_CLAUSES: "Because" also needs a bare clause, not "Because provided".
BECAUSE_CLAUSES = [
    "the precondition does not hold", "the exception was approved",
    "the backfill did not complete", "the policy window closed",
    "the review outcome changed", "the release checklist is incomplete",
    "the audit entry was missing", "the owning team reassigned the work",
    "the downstream contract changed", "the feature flag was turned off",
]
ARTIFACTS = [
    "change record", "review log", "release checklist",
    "support note", "measurement sheet", "handover summary",
    "verification trace", "audit entry", "rollout plan",
    "exception register",
]

# Template shapes, so successive sections do not share a single sentence rhythm.
TEMPLATES = [
    "{context}, {subject} {action} {condition}, and the outcome is recorded in the "
    "{artifact}.",
    "The {artifact} shows that {subject} {action} {condition}.",
    "If {if_condition}, {subject} {action}; the {artifact} is updated at the same time.",
    "{context} the team confirmed that {subject} {action} {condition}, per the "
    "{artifact}.",
    "It remains necessary to check whether {subject} {action} {condition}, and the "
    "{artifact} carries the detail.",
    "Because {because_clause}, {subject} {action} {condition}, as noted in the "
    "{artifact}.",
    "Reviewers treat {subject} as the reference point: it {action} {condition}, and the "
    "{artifact} is the authoritative record.",
    "{context}, no exception is raised for {subject} when it {action} {condition}; the "
    "{artifact} captures the decision.",
]

REGISTER_CONTEXT = {"formal": FORMAL_CONTEXT, "informal": INFORMAL_CONTEXT}


def _register_from_document_maturity(maturity: str) -> str:
    return "formal" if maturity == "formal" else "informal"


def _section_sentences(register: str, rng: random.Random, count: int,
                       vocab: dict) -> list:
    """
    Deterministic, register-consistent, entity-neutral sentences, sampled WITHOUT
    replacement so no sentence repeats inside a document.
    """
    contexts = REGISTER_CONTEXT[register]
    seen: set = set()
    out: list = []
    attempts = 0
    while len(out) < count and attempts < count * 40:
        attempts += 1
        template = rng.choice(TEMPLATES)
        candidate = template.format(
            context=rng.choice(contexts),
            subject=rng.choice(vocab["subjects"]),
            action=rng.choice(vocab["actions"]),
            condition=rng.choice(CONDITIONS),
            if_condition=rng.choice(IF_CLAUSES),
            because_clause=rng.choice(BECAUSE_CLAUSES),
            condition2=rng.choice(CONDITIONS),
            artifact=rng.choice(ARTIFACTS),
        )
        if candidate in seen:
            continue
        seen.add(candidate)
        out.append(candidate)
    return out


def _register_of(model, product_id: str) -> str:
    product = next(p for p in model.products if p.product_id == product_id)
    return product.documentation_maturity


def extend_document(document, model, target_words: int):
    """
    Return a copy of `document` extended to ~`target_words`.

    The original body is preserved verbatim and first. Extensions never restate a
    requirement statement or a dependency description, because duplicating them would create
    false C2/C3 hits; assert_no_protected_restatements enforces that.
    """
    register = _register_of(model, document.product_id)
    vocab = _vocabulary(register)
    plan = SECTION_PLAN.get(document.doc_type, [])
    rng = random.Random(f"{document.document_id}|{register}|chunking-pilot")

    body = document.body
    index = 0
    while len(body.split()) < target_words and plan:
        heading = plan[index % len(plan)]
        repeats = index // len(plan)
        suffix = f" (part {repeats + 1})" if repeats else ""
        body += f"\n\n## {heading}{suffix}\n\n" + " ".join(
            _section_sentences(register, rng, count=6, vocab=vocab)
        )
        index += 1

    return Document(
        document_id=document.document_id,
        doc_type=document.doc_type,
        title=document.title,
        body=body,
        source_entity_id=document.source_entity_id,
        product_id=document.product_id,
        version=document.version,
        version_status=document.version_status,
        is_current=document.is_current,
        superseded_by=document.superseded_by,
        supersedes=document.supersedes,
        created_date=document.created_date,
        modified_date=document.modified_date,
        references=document.references,
    )


def build_pilot_documents(model, documents):
    return [
        extend_document(d, model, PILOT_LENGTH_TARGETS.get(d.doc_type, 400))
        for d in documents
    ]


def assert_no_protected_restatements(model, documents) -> None:
    """
    Guard: the extension must not restate a requirement statement or an explicit dependency
    description, or C2/C3 would report splits that are really restatements. Raises rather
    than warns, because a silent violation corrupts the comparison.
    """
    protected = []
    for requirement in model.requirements:
        protected.append((requirement.requirement_id,
                          " ".join(requirement.statement.split()[:8])))
    for dependency in model.dependencies:
        if dependency.explicitness == "explicit":
            protected.append((dependency.dependency_id,
                              " ".join(dependency.description.split()[:8])))

    offenders = []
    for document in documents:
        for label, key in protected:
            if key and document.body.count(key) > 1:
                offenders.append(
                    f"{document.document_id} duplicates {label} x{document.body.count(key)}"
                )
    if offenders:
        raise AssertionError(
            "Pilot extension restated protected statements, which would corrupt C2/C3:\n  "
            + "\n  ".join(offenders)
        )

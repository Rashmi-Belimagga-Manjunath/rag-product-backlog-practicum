"""
Ground-truth validation gate.

Two jobs:

1. Validate the 32-slot specification against every approved constraint.
2. Validate that every ID a slot resolves to actually EXISTS in the structured model.

The second job is a hard gate. An unresolvable ground-truth reference is a STOP condition,
never a warning and never a reason to drop the slot. Run against the mechanism sample it
reports which slots the FINAL corpus must satisfy; run against the final corpus it must
report zero unresolved slots before the freeze is signed.

Nothing here consults BM25, RAG, or a language model.

Run:  python3 -m src.benchmark.validate_ground_truth
      python3 -m src.benchmark.validate_ground_truth --against-final
"""

from __future__ import annotations

import sys
from collections import Counter
from dataclasses import dataclass, field

from ..data_generation.render_v1 import render_corpus
from ..data_generation.v1_sample import build_mechanism_sample
from .query_spec import SLOTS, validate_spec
from .selectors import resolve_slot


def known_ids(model) -> dict:
    """Every ID the model can legitimately hand out."""
    # Document IDs are the sources of declared links (validation V8 guarantees every
    # document has at least one), plus the document_id carried by versioned entities.
    document_ids = {l.from_document_id for l in model.document_links}
    for item in list(model.features) + list(model.prds):
        if getattr(item, "document_id", ""):
            document_ids.add(item.document_id)
    entity_ids = set()
    for collection, key in (
        (model.features, "feature_id"), (model.prds, "prd_id"),
        (model.requirements, "requirement_id"), (model.pbis, "pbi_id"),
        (model.components, "component_id"), (model.tickets, "ticket_id"),
        (model.decisions, "decision_id"), (model.meeting_notes, "note_id"),
        (model.runbooks, "runbook_id"),
    ):
        entity_ids |= {getattr(item, key) for item in collection}
    return {
        "documents": document_ids,
        "entities": entity_ids,
        "dependencies": {d.dependency_id for d in model.dependencies},
        "conflicts": {c.conflict_id for c in model.conflicts},
        "products": {p.product_id for p in model.products},
    }


def check_ids(resolution, known) -> list:
    """Every ID the resolution produced must exist. Unresolvable = STOP."""
    problems = []
    for document_id in resolution.document_ids:
        if document_id not in known["documents"]:
            problems.append(f"document '{document_id}' does not exist in the model")
    for entity_id in resolution.entity_ids:
        if entity_id not in known["entities"]:
            problems.append(f"entity '{entity_id}' does not exist in the model")
    for dependency_id in resolution.expected_dependencies:
        if dependency_id not in known["dependencies"]:
            problems.append(f"dependency '{dependency_id}' does not exist in the model")
    # Conflicts are a separate ID space. A conflict_id in entity_ids would resolve against
    # no entity and look like a valid empty result instead of an error.
    for conflict_id in resolution.conflict_ids:
        if conflict_id not in known["conflicts"]:
            problems.append(f"conflict '{conflict_id}' does not exist in the model")
    for document_id in resolution.distractor_document_ids:
        if document_id not in known["documents"]:
            problems.append(
                f"distractor document '{document_id}' does not exist in the model")
    return problems


@dataclass
class Report:
    """Outcome of one validation pass. Separated from printing so it is testable."""
    spec_problems: list = field(default_factory=list)
    id_problems: list = field(default_factory=list)
    unmet: list = field(default_factory=list)
    resolutions: dict = field(default_factory=dict)

    @property
    def broken_references(self) -> bool:
        """An ID was produced that does not exist. Always a defect, in any mode."""
        return bool(self.spec_problems or self.id_problems)

    @property
    def freezable(self) -> bool:
        """A freeze requires a valid spec, no broken references, and no unmet slots."""
        return not self.broken_references and not self.unmet


def validate_ground_truth(model=None, documents=None, against_final: bool = False) -> Report:
    """
    Resolve all 32 slots against a structured model and report what does not hold.

    against_final=False (mechanism sample): unmet slots are corpus requirements. They are
    reported, and the caller is told the model is not freezable, but they are not defects.
    against_final=True: the same code path is the freeze gate, where any unmet slot is a
    hard stop.

    The distinction matters because the mechanism sample deliberately omits phenomena the
    final corpus must contain. Reporting those as broken references would train everyone to
    ignore this gate.
    """
    model = model if model is not None else build_mechanism_sample()
    documents = documents if documents is not None else render_corpus(model)
    known = known_ids(model)
    report = Report(spec_problems=validate_spec())

    for slot in SLOTS:
        resolution = resolve_slot(slot, model, documents)
        bad = check_ids(resolution, known)
        if bad:
            report.id_problems.append((slot.query_id, bad))
        if not resolution.resolved:
            report.unmet.append({
                "query_id": slot.query_id,
                "category": slot.category,
                "selector": slot.selector,
                "needs": resolution.notes[0] if resolution.notes else slot.selector,
                "required_corpus_facts": list(slot.required_corpus_facts),
            })
        report.resolutions[slot.query_id] = resolution
    return report


def main() -> int:
    against_final = "--against-final" in sys.argv
    report = validate_ground_truth(against_final=against_final)
    model = build_mechanism_sample()

    print("=" * 78)
    print("GROUND-TRUTH VALIDATION GATE")
    print("=" * 78)
    print("mode:", "FINAL CORPUS (any unmet slot is a hard stop)" if against_final
          else "mechanism sample (unmet slots are corpus requirements)")
    print(f"specification problems: {report.spec_problems or 'none'}")
    print()

    print(f"{'slot':8}{'cat':7}{'diff':9}{'dep':9}{'rel':6}{'docs':5}{'deps':5}  note")
    print("-" * 92)
    for slot in sorted(SLOTS, key=lambda s: s.slot):
        resolution = report.resolutions[slot.query_id]
        note = resolution.notes[0][:36] if resolution.notes else ""
        print(f"{slot.query_id:8}{slot.category[:6]:7}{slot.difficulty:9}"
              f"{(slot.dependency_explicitness or '-'):9}"
              f"{resolution.relevance_basis[:5]:6}"
              f"{len(resolution.document_ids):<5}"
              f"{len(resolution.expected_dependencies):<5}  {note}")
        for qid, bad in report.id_problems:
            if qid == slot.query_id:
                for problem in bad:
                    print(f"{'':8}  !! {problem}")

    difficulties = Counter(s.difficulty for s in SLOTS)
    dependency_slots = [s for s in SLOTS if s.dependency_explicitness]
    explicitness = Counter(s.dependency_explicitness for s in dependency_slots)
    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    print(f"slots                     {len(SLOTS)}")
    print(f"difficulty                {dict(difficulties)}  (required 11 easy / 11 moderate / 10 hard)")
    print(f"categories                {len({s.category for s in SLOTS})} distinct, counts as approved")
    print(f"dependency-related        {len(dependency_slots)} "
          f"(explicit {explicitness['explicit']}, implicit {explicitness['implicit']})")
    print(f"version queries           {sum(1 for s in SLOTS if s.version_kind)} "
          f"(Q-SUP-1/2/3, approved wording only)")
    print()
    print(f"unresolvable-ID problems  {len(report.id_problems)}")
    print(f"slots this model cannot resolve  {len(report.unmet)}")

    if report.unmet:
        print()
        print("CORPUS REQUIREMENTS for the final 272-document corpus")
        print("-" * 78)
        print("These are NOT defects. The mechanism sample carries 10 dependencies and 1")
        print("superseded pair per product; the final corpus carries ~208 dependencies and")
        print("12 superseded documents. Every item below is a property the final corpus MUST")
        print("provide, and the freeze is blocked until each resolves.")
        print()
        for item in report.unmet:
            print(f"  {item['query_id']}  ({item['category']})")
            print(f"      needs: {item['needs']}")
            for fact in item["required_corpus_facts"]:
                print(f"      fact:  {fact}")

    print()
    if report.broken_references:
        print("RESULT: FAIL - a ground-truth reference does not resolve.")
        print("        This is a hard stop in either mode. Do not proceed to the freeze.")
        return 1

    if report.unmet:
        print("RESULT: specification valid and every resolved ID exists in the model.")
        print(f"        NOT FREEZABLE against this model: "
              f"{len(report.unmet)} slot(s) unmet.")
        if against_final:
            print("        --against-final was set, so this is a HARD STOP.")
            return 1
        print("        Against the mechanism sample this is expected and not a defect.")
        print("        Re-run with --against-final: there, any unmet slot is a hard stop.")
        return 2

    print("RESULT: PASS - all 32 slots resolve and every referenced ID exists.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

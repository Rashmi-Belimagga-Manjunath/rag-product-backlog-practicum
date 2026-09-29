"""
Render docs/query_specification.md from SLOTS.

The document is GENERATED so it cannot drift from the machine specification. A test
asserts the committed file matches this render, so changing a slot without regenerating
fails CI rather than silently producing a document that contradicts the code.

Run:  python3 -m src.benchmark.render_spec_doc [--check]
"""

from __future__ import annotations

import sys
from pathlib import Path

from .query_spec import (
    APPROVED_CATEGORY_COUNTS, APPROVED_DEPENDENCY_TOTAL, APPROVED_DIFFICULTY_COUNTS,
    APPROVED_EXPLICIT, APPROVED_IMPLICIT, CATEGORY_LABEL, CHUNKING_LIMITATION_NOTE,
    DEPENDENCY_CATEGORIES, DIFFICULTY_METHOD_NOTE, DIFFICULTY_MISMATCH_NOTE,
    Q05_INTENT_NOTE, SLOTS, validate_spec,
)

DOC = Path("docs/query_specification.md")


def render() -> str:
    problems = validate_spec()
    if problems:
        raise SystemExit("refusing to render: spec invalid:\n  " + "\n  ".join(problems))

    L: list[str] = []
    L.append("# Query Benchmark Specification (32 slots)\n")
    L.append("> **Generated file.** Produced by `python3 -m src.benchmark.render_spec_doc`")
    L.append("> from `src/benchmark/query_spec.py`. Do not edit by hand; a test asserts this")
    L.append("> file matches the code.\n")
    L.append("The slot distribution is **APPROVED and FROZEN**. All 32 slots now carry")
    L.append("approved wording (see Exact approved wording). The three Q-SUP queries were fixed")
    L.append("before the corpus existed; the other 29 were authored against the frozen")
    L.append("272-document corpus, each derived from the corpus and the slot's own selector.")
    L.append("Difficulty is re-measured from the final wording before either system is")
    L.append("evaluated.\n")
    L.append("## Approved totals\n")
    L.append("| Property | Required |")
    L.append("|---|---|")
    L.append(f"| Total slots | {len(SLOTS)} |")
    for k, v in APPROVED_DIFFICULTY_COUNTS.items():
        L.append(f"| Difficulty: {k} | {v} |")
    for k, v in APPROVED_CATEGORY_COUNTS.items():
        L.append(f"| {CATEGORY_LABEL[k]} | {v} |")
    L.append(f"| Dependency-related total | {APPROVED_DEPENDENCY_TOTAL} "
             f"({APPROVED_EXPLICIT} explicit, {APPROVED_IMPLICIT} implicit) |")
    L.append("\nDependency-related categories are "
             + " and ".join(f"`{c}`" for c in sorted(DEPENDENCY_CATEGORIES)) + ".\n")
    L.append("## Slot register\n")
    L.append("Slots are **selectors over the structured model**, not hard-coded document IDs.")
    L.append("The final 272-document corpus has different IDs from the mechanism sample, so a")
    L.append("selector that resolves against the sample must also resolve against the final")
    L.append("corpus. An unresolved slot is a hard STOP at freeze, never a warning.\n")
    L.append("| Slot | ID | Category | Difficulty | Selector | Dep. | Version | Purpose |")
    L.append("|---:|---|---|---|---|---|---|---|")
    for s in sorted(SLOTS, key=lambda s: s.slot):
        L.append(
            f"| {s.slot} | `{s.query_id}` | {CATEGORY_LABEL[s.category]} | {s.difficulty} "
            f"| `{s.selector}` | {s.dependency_explicitness or '-'} "
            f"| {s.version_kind or '-'} | {s.purpose} |"
        )
    L.append("\n## Exact approved wording\n")
    L.append("All 32 slots are worded. These are fixed by the specification and are **not**")
    L.append("placeholders.\n")
    for s in sorted(SLOTS, key=lambda s: s.slot):
        if s.query_text:
            L.append(f"- `{s.query_id}`: \"{s.query_text}\"")
    L.append("\n## Corpus requirements attached to slots\n")
    L.append("Some slots cannot resolve against the 34-document mechanism sample because the")
    L.append("sample deliberately does not contain the phenomenon. These are **corpus")
    L.append("requirements, not defects**; `validate_ground_truth --against-final` makes them")
    L.append("hard stops.\n")
    for s in sorted(SLOTS, key=lambda s: s.slot):
        if s.required_corpus_facts:
            L.append(f"- `{s.query_id}`:")
            for fact in s.required_corpus_facts:
                L.append(f"  - {fact}")
    L.append("\n## Difficulty definition\n")
    L.append("Easy `>=40%` lexical overlap, moderate `20-39%`, hard `<20%`, computed with the")
    L.append("frozen stopword set over query text versus the target documents. This is a")
    L.append("property of the benchmark, not a psychological claim about difficulty.\n")
    L.append("## Difficulty labels vs lexical overlap\n")
    L.append("Evidence terminology: `difficulty_label` is the frozen benchmark difficulty")
    L.append("designation; `lexical_overlap` is the measured lexical-overlap percentage;")
    L.append("`lexical_overlap_band` is the band produced by the frozen overlap thresholds;")
    L.append("`difficulty_status` is MATCH / MISMATCH between the frozen label and the band.")
    L.append("The QUERIES sheet of the evidence workbook reports one row per slot with all")
    L.append("four fields.\n")
    L.append(DIFFICULTY_METHOD_NOTE + "\n")
    L.append(DIFFICULTY_MISMATCH_NOTE + "\n")
    L.append("## Chunking limitation\n")
    L.append(CHUNKING_LIMITATION_NOTE + "\n")
    L.append("## Q-05 intent\n")
    L.append(Q05_INTENT_NOTE + "\n")
    L.append("## Validation\n")
    L.append("`python3 -m src.benchmark.query_spec` prints the table and exits non-zero on any")
    L.append("distribution violation. `python3 -m src.benchmark.validate_ground_truth`")
    L.append("resolves every selector against the structured model.\n")
    return "\n".join(L)


def main() -> int:
    text = render()
    if "--check" in sys.argv:
        current = DOC.read_text() if DOC.exists() else ""
        if current != text:
            print(f"FAIL: {DOC} is out of date. Run: python3 -m src.benchmark.render_spec_doc")
            return 1
        print(f"OK: {DOC} matches the machine specification.")
        return 0
    DOC.write_text(text)
    print(f"wrote {DOC} ({len(text.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

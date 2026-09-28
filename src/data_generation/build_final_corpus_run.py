"""
Final corpus build and validation runner (freeze gate).

Builds the approved 272-document corpus, renders it, chunks it at the frozen 1000/200
configuration (plus the 600/100 comparison), validates structural invariants, C1-C8
coherence, determinism, and resolves all 32 ground-truth slots in FINAL mode with
`against_final=True`.

Any unresolved slot, broken reference, or structural failure is a HARD STOP (exit 1):
the gate never reports a corpus as freezable unless every check passes.

Writes the D-012 freeze layout:
    data/corpus/v1/source_model.json
    data/corpus/v1/rendered/          (272 Markdown documents + index)
    data/corpus/v1/chunks/chunks.json (primary 1000/200)
    data/corpus/v1/chunks/chunks-comparison.json (600/100)
    data/corpus/v1/VALIDATION.md
    data/manifest/validation/final_corpus_report.md   (the 20-item report)

Run:  python3 -m src.data_generation.build_final_corpus_run
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from ..benchmark.validate_ground_truth import validate_ground_truth
from ..chunking.splitter import (
    ChunkingConfig,
    chunk_corpus,
    validate_coherence,
)
from ..ground_truth.schema import lexical_overlap
from .render_v1 import render_corpus
from .source_model import doc_ids_from, validate_model
from .v1_full import CREATED, build_final_corpus

OUT = Path("data/corpus/v1")
REPORT_DIR = Path("data/manifest/validation")

PRIMARY = ChunkingConfig(1000, 200, "primary")
COMPARISON = ChunkingConfig(600, 100, "comparison")

EXPECTED_SCALE = {"superseded_documents": 12, "explicit_dependencies": 104}


def write_outputs(model, documents, chunks_primary, chunks_comparison) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "source_model.json").write_text(
        json.dumps(model.to_dict(), indent=2, sort_keys=False) + "\n")

    corpus_dir = OUT / "rendered"
    if corpus_dir.exists():
        for old in corpus_dir.glob("*.md"):
            old.unlink()
    corpus_dir.mkdir(exist_ok=True)
    for document in documents:
        (corpus_dir / f"{document.document_id}.md").write_text(document.body + "\n")
    types = Counter(d.doc_type for d in documents)
    (corpus_dir / "INDEX.md").write_text(
        "# Final corpus document index\n\n"
        f"{len(documents)} documents, "
        f"{sum(d.word_count() for d in documents)} words.\n\n"
        "| Document type | Count |\n|---|---:|\n"
        + "\n".join(f"| {t} | {types[t]} |" for t in sorted(types))
        + "\n\n| Document | Type | Subject | Version | Words |\n"
          "|---|---|---|---|---:|\n"
        + "\n".join(
            f"| `{d.document_id}` | {d.doc_type} | `{d.source_entity_id}` | "
            f"{d.version} {d.version_status} | {d.word_count()} |"
            for d in sorted(documents, key=lambda x: x.document_id))
        + "\n")

    chunk_dir = OUT / "chunks"
    chunk_dir.mkdir(exist_ok=True)
    (chunk_dir / "chunks.json").write_text(
        json.dumps([c.__dict__ for c in chunks_primary], indent=2) + "\n")
    (chunk_dir / "chunks-comparison.json").write_text(
        json.dumps([c.__dict__ for c in chunks_comparison], indent=2) + "\n")


def main() -> int:
    model = build_final_corpus()
    documents = render_corpus(model)
    chunks_primary = chunk_corpus(documents, PRIMARY)
    chunks_comparison = chunk_corpus(documents, COMPARISON)
    write_outputs(model, documents, chunks_primary, chunks_comparison)

    passthrough = True
    report_lines: list[str] = []
    add = report_lines.append

    add(f"# Final corpus validation report ({model.model_version})")
    add("")
    add(f"Built {CREATED}. Model `{model.model_version}` · seed `{model.seed}`.")

    # ---- 1. Structural + scale invariants (V1-V9) ---------------------------
    structural = validate_model(model, expected_scale=EXPECTED_SCALE)
    structural_failures = [r for r in structural if not r.passed]
    add("")
    add("## 1. Source-model invariants (V1-V9)")
    add("")
    add("| Check | Result | Detail |")
    add("|---|---|---|")
    for result in structural:
        mark = "PASS" if result.passed else "FAIL"
        add(f"| {result.check_id} | {mark} | {result.detail} |")
    if structural_failures:
        passthrough = False

    # ---- 2. Corpus cardinality -------------------------------------------------
    add("")
    add("## 2. Corpus cardinality (approved targets)")
    add("")
    types = Counter(d.doc_type for d in documents)
    approved = {"prd": 17, "feature_spec": 29, "pbi": 120, "component_doc": 18,
                "ticket": 40, "decision_log": 16, "meeting_notes": 24, "runbook": 8}
    add("| Type | Actual | Approved |")
    add("| --- | ---: | ---: |")
    for t in sorted(approved):
        ok = "PASS" if types.get(t, 0) == approved[t] else "FAIL"
        if ok == "FAIL":
            passthrough = False
        add(f"| {t} | {types.get(t, 0)} | {approved[t]} | {ok}")
    add(f"| **total** | **{len(documents)}** | **272** | "
        f"{'PASS' if len(documents) == 272 else 'FAIL'}")
    if len(documents) != 272:
        passthrough = False
    explicit = sum(1 for d in model.dependencies if d.explicitness == "explicit")
    implicit = sum(1 for d in model.dependencies if d.explicitness == "implicit")
    resolved_conflicts = sum(1 for c in model.conflicts if c.is_resolved)
    add(f"- Dependencies: **{len(model.dependencies)}** "
        f"({explicit} explicit / {implicit} implicit)")
    add(f"- Conflicts: **{len(model.conflicts)}** "
        f"({resolved_conflicts} resolved / {len(model.conflicts) - resolved_conflicts} "
        f"unresolved)")
    add(f"- Document links: **{len(model.document_links)}**")

    # ---- 3. Determinism ---------------------------------------------------------
    rebuilt = build_final_corpus()
    rerendered = render_corpus(rebuilt)
    re_chunked = chunk_corpus(rerendered, PRIMARY)
    det_model = rebuilt.to_dict() == model.to_dict()
    det_docs = [d.body for d in rerendered] == [d.body for d in documents]
    det_chunks = [c.__dict__ for c in re_chunked] == [c.__dict__ for c in chunks_primary]
    add("")
    add("## 3. Determinism (two independent builds)")
    add("")
    add(f"- Model byte-identical: **{det_model}**")
    add(f"- Rendering byte-identical: **{det_docs}**")
    add(f"- Chunking byte-identical: **{det_chunks}**")
    if not (det_model and det_docs and det_chunks):
        passthrough = False

    # ---- 4. Chunking coherence C1-C8 ---------------------------------------------
    add("")
    add("## 4. Chunking coherence")
    add("")
    coherence_by_config: dict = {}
    for label, config, chunks in (("Primary 1000/200", PRIMARY, chunks_primary),
                                  ("Comparison 600/100", COMPARISON, chunks_comparison)):
        add(f"### {label}")
        add("")
        results = validate_coherence(documents, chunks, model, config)
        coherence_by_config[label] = {r.check_id: r for r in results}
        for result in results:
            mark = "PASS" if result.passed else "FAIL"
            if result.passed is False and config == PRIMARY:
                passthrough = False
            add(f"- **{result.check_id} {mark}** - {result.description}")
            add(f"  - observed {result.observed} (threshold {result.threshold})")
        add("")

    # ---- 5. Ground truth (32 slots, final mode) ----------------------------------
    add("## 5. Ground truth: all 32 slots, final mode (`--against-final`)")
    add("")
    report = validate_ground_truth(model=model, documents=documents, against_final=True)
    add(f"- Specification problems: **{report.spec_problems or 'none'}**")
    add(f"- Broken references: **{len(report.id_problems)}**")
    add(f"- Unresolved slots: **{len(report.unmet)}**")
    if report.id_problems:
        passthrough = False
        for qid, problems in report.id_problems:
            add(f"  - {qid}: {problems}")
    if report.unmet:
        passthrough = False
        for item in report.unmet:
            add(f"  - {item['query_id']} needs: {item['needs']}")
    add("")
    add("| Slot | Category | Docs | Rel. basis | Note |")
    add("|---|---|---:|---|---|")
    for slot in sorted(__import__("src.benchmark.query_spec", fromlist=["SLOTS"]).SLOTS,
                       key=lambda s: s.slot):
        resolution = report.resolutions[slot.query_id]
        note = (resolution.notes[0] if resolution.notes else "")[:60]
        add(f"| {slot.query_id} | {slot.category} | {len(resolution.document_ids)} | "
            f"{resolution.relevance_basis} | {note} |")

    # ---- 6. Seven explicit corpus requirements -----------------------------------
    gates = ["Q-05", "Q-SUP-3", "Q-10", "Q-11", "Q-14", "Q-20", "Q-21"]
    unmet_ids = {u["query_id"] for u in report.unmet}
    add("")
    add("## 6. The seven former corpus requirements (freeze checklist B)")
    add("")
    for qid in gates:
        status = "RESOLVED" if qid not in unmet_ids else "UNRESOLVED"
        if status == "UNRESOLVED":
            passthrough = False
        add(f"- **{qid}: {status}**")

    # ---- 7. Twenty-item validation checklist + verdict --------------------
    primary = coherence_by_config["Primary 1000/200"]
    struct_ok = not structural_failures
    items = [
        ("V1-V8 source-model invariants", struct_ok or all(
            r.passed for r in structural if r.check_id != "V9")),
        ("V9 dependency scale (104 explicit / 104 implicit / 208 total)",
         any(r.passed for r in structural if r.check_id == "V9")),
        ("Superseded document count = 12",
         any(r.passed for r in structural if r.check_id == "V4")),
        ("Corpus cardinality = 272 documents", len(documents) == 272),
        ("Per-type counts match the approved targets", all(
            types.get(t, 0) == approved[t] for t in approved)),
        ("Conflicts = 12 with 7 resolved / 5 unresolved",
         resolved_conflicts == 7 and len(model.conflicts) - resolved_conflicts == 5),
        ("No broken document references (543 links resolvable)",
         not report.id_problems and len(model.document_links) == 543),
        ("Determinism: model serialisation byte-identical", det_model),
        ("Determinism: rendered documents byte-identical", det_docs),
        ("Determinism: chunking byte-identical", det_chunks),
        ("C1 no sentence split at chunk boundary", primary["C1"].passed),
        ("C2 dependency statements never split", primary["C2"].passed),
        ("C3 requirement statements never split", primary["C3"].passed),
        ("C4 every chunk carries entity provenance", primary["C4"].passed),
        ("C5 orphan chunks under 50 words below 3%", primary["C5"].passed),
        ("C6 no near-duplicate chunks within a document", primary["C6"].passed),
        ("C7 every document yields >=1 chunk", primary["C7"].passed),
        ("C8 every ground-truth document reachable", primary["C8"].passed),
        ("Ground truth: zero broken references", not report.id_problems),
        ("Ground truth: all 32 slots resolved (final mode)", not report.unmet),
    ]
    add("")
    add("## 7. Twenty-item validation checklist")
    add("")
    add("| # | Item | Result |")
    add("|---|---|---|")
    for index, (label, ok) in enumerate(items, start=1):
        if not ok:
            passthrough = False
        add(f"| {index} | {label} | {'PASS' if ok else 'FAIL'} |")

    add("")
    add("## Verdict")
    add("")
    if passthrough:
        add("**PASS - the final corpus is freezable on every check.**")
        add("")
        add("The corpus, its dependencies, chunks, and ground truth are all deterministic;")
        add("the seven former corpus requirements (Q-05, Q-SUP-3, Q-10, Q-11, Q-14, Q-20,")
        add("Q-21) and all 32 benchmark slots resolve against the resulting documents. The")
        add("corpus is ready for the BM25 and RAG comparison.")
    else:
        add("**FAIL - at least one gate did not pass; the corpus is not freezable.**")

    final_report = "\n".join(report_lines) + "\n"

    VALIDATION = OUT / "VALIDATION.md"
    OUT.mkdir(parents=True, exist_ok=True)
    VALIDATION.write_text(final_report)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "final_corpus_report.md").write_text(final_report)
    print(final_report)

    print("=" * 78)
    if structural_failures:
        print("STRUCTURAL FAILURES:", [r.check_id for r in structural_failures])
    if report.id_problems:
        print("BROKEN GROUND-TRUTH REFERENCES:", [q for q, _ in report.id_problems])
    if report.unmet:
        print("UNRESOLVED SLOTS:", [u["query_id"] for u in report.unmet])
    print(f"documents: {len(documents)} | chunks (primary): {len(chunks_primary)} | "
          f"chunks (comparison): {len(chunks_comparison)}")
    print(f"wrote {OUT}/source_model.json, rendered/, chunks/, VALIDATION.md")
    print(f"wrote {REPORT_DIR}/final_corpus_report.md")

    if not passthrough:
        print("RESULT: FAIL - see report above. Hard stop.")
        return 1
    print("RESULT: PASS - final corpus freezable on every check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
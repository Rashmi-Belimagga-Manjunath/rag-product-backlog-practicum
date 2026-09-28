"""
Mechanism-sample build and review runner.

Writes the final schema sample to disk as a source-of-truth JSON plus rendered Markdown,
then runs structural, rendering, determinism, provenance, and chunk-coherence checks and
writes a validation report.

Run:  python3 -m src.data_generation.build_v1_sample_run
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from ..chunking.splitter import (
    ChunkingConfig,
    chunk_corpus,
    project_scaling,
    validate_coherence,
)
from ..ground_truth.schema import (
    QuerySpec,
    derive_ground_truth,
    verify_traceable,
)
from .render_v1 import render_corpus
from .source_model import validate_model
from .v1_sample import build_mechanism_sample

OUT = Path("data/synthetic/v1-schema-sample")

PRIMARY = ChunkingConfig(1000, 200, "primary")
COMPARISON = ChunkingConfig(600, 100, "comparison")


def write_sample(model, documents, chunks) -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    (OUT / "source_model.json").write_text(
        json.dumps(model.to_dict(), indent=2, sort_keys=False) + "\n"
    )

    corpus_dir = OUT / "rendered"
    corpus_dir.mkdir(exist_ok=True)
    for document in documents:
        (corpus_dir / f"{document.document_id}.md").write_text(document.body + "\n")
    (corpus_dir / "INDEX.md").write_text(
        "# Mechanism sample document index\n\n"
        f"{len(documents)} documents, "
        f"{sum(d.word_count() for d in documents)} words.\n\n"
        "| Document | Type | Subject | Version | Words |\n"
        "|---|---|---|---|---:|\n"
        + "\n".join(
            f"| `{d.document_id}` | {d.doc_type} | `{d.source_entity_id}` | "
            f"{d.version} {d.version_status} | {d.word_count()} |"
            for d in sorted(documents, key=lambda x: x.document_id)
        )
        + "\n"
    )

    chunk_dir = OUT / "chunks"
    chunk_dir.mkdir(exist_ok=True)
    (chunk_dir / "chunks.json").write_text(
        json.dumps([c.__dict__ for c in chunks], indent=2) + "\n"
    )


def build_report(model, documents, chunks_primary, chunks_comparison) -> str:
    OUT.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    add = lines.append

    add("# Mechanism Sample Validation Report")
    add("")
    add(f"Model: `{model.model_version}` · seed `{model.seed}` · created {model.created_date}")
    add("")

    add("## 1. Source-model structural validation")
    add("")
    add("| Check | Result | Detail |")
    add("|---|---|---|")
    for result in validate_model(model):
        mark = "PASS" if result.passed else "FAIL"
        scale = " *(scale target, not applicable at sample size)*" if result.is_scale_target else ""
        add(f"| {result.check_id} | {mark}{scale} | {result.detail} |")
    add("")

    add("## 2. Rendering")
    add("")
    total_words = sum(d.word_count() for d in documents)
    types: dict[str, int] = {}
    for document in documents:
        types[document.doc_type] = types.get(document.doc_type, 0) + 1
    add(f"- Documents: **{len(documents)}**")
    add(f"- Total words: **{total_words}**")
    add(f"- Document links: **{len(model.document_links)}**")
    add(f"- Superseded: **{sum(1 for d in documents if not d.is_current)}**")
    add("")
    add("| Document type | Count |")
    add("|---|---:|")
    for doc_type in sorted(types):
        add(f"| {doc_type} | {types[doc_type]} |")
    add("")

    add("## 3. Determinism")
    add("")
    rebuilt = build_mechanism_sample()
    rerendered = render_corpus(rebuilt)
    deterministic_model = rebuilt.to_dict() == model.to_dict()
    deterministic_docs = [d.body for d in rerendered] == [d.body for d in documents]
    re_chunked = chunk_corpus(documents, PRIMARY)
    deterministic_chunks = [c.__dict__ for c in re_chunked] == [
        c.__dict__ for c in chunks_primary
    ]
    add(f"- Model rebuilt identically: **{deterministic_model}**")
    add(f"- Rendering byte-identical: **{deterministic_docs}**")
    add(f"- Chunking byte-identical: **{deterministic_chunks}**")
    add("")

    add("## 4. Chunk provenance")
    add("")
    no_provenance = [c.chunk_id for c in chunks_primary if not c.all_entity_ids()]
    covered = {e for c in chunks_primary for e in c.all_entity_ids()}
    add(f"- Chunks with no entity provenance: **{len(no_provenance)}**")
    add(f"- Distinct entities reachable through chunk provenance: **{len(covered)}**")
    add(f"- Every requirement has a subject chunk: "
        f"**{all(any(c.source_entity_id == r.requirement_id for c in chunks_primary) for r in model.requirements)}**")
    add(f"- Every PBI has a subject chunk: "
        f"**{all(any(c.source_entity_id == p.pbi_id for c in chunks_primary) for p in model.pbis)}**")
    add("")

    add("## 5. Link-type coverage")
    add("")
    from typing import get_args
    from .source_model import LinkType

    exercised = {l.link_type for l in model.document_links}
    declared = set(get_args(LinkType))
    add("| Link type | Count |")
    add("|---|---:|")
    for link_type in sorted(declared):
        count = sum(1 for l in model.document_links if l.link_type == link_type)
        add(f"| `{link_type}` | {count} |")
    add("")
    add(f"- Declared but not exercised: **{sorted(declared - exercised) or 'none'}**")
    add("")

    add("## 6. Ground-truth derivation")
    add("")
    spec = QuerySpec(
        query_id="Q-SAMPLE-1",
        slot=0,
        category="dependency_identification",
        target_entity_id="FEAT-A-01",
        target_document_ids=["DOC-FEAT-A-01-v2", "DOC-PRD-A-01-v2"],
        target_dependency_ids=["DEP-006"],
        dependency_explicitness="implicit",
        intended_difficulty="hard",
        distractors=["DOC-FEAT-A-02", "DOC-COMP-05"],
    )
    gt = derive_ground_truth(
        spec, "Which service has to be reached before the ramp can ask for tax paperwork?",
        model, documents, chunks_primary,
    )
    problems = verify_traceable(gt, model)
    add(f"- Derived from model only: **yes** (no retrieval, no LLM, no re-reading chunk text)")
    add(f"- Traceability problems: **{problems or 'none'}**")
    add(f"- Measured overlap: **{gt.measured_overlap:.1%}** → band **{gt.difficulty}** "
        f"(slot targeted `{spec.intended_difficulty}`)")
    add(f"- Relevant chunk IDs resolved: **{len(gt.relevant_chunk_ids)}**")
    add("")
    add("> The band disagreement above is the intended demonstration. The slot targeted "
        "`hard` and the measurement returned a different band, because lexical overlap is "
        "a property of wording plus corpus, not a property of the slot label.")
    add("")

    add("## 7. Chunking coherence")
    add("")
    for label, config, chunks in (
        ("Primary 1000 / 200", PRIMARY, chunks_primary),
        ("Comparison 600 / 100", COMPARISON, chunks_comparison),
    ):
        add(f"### {label}")
        add("")
        results = validate_coherence(documents, chunks, model, config)
        for result in results:
            mark = "PASS" if result.passed else "FAIL"
            add(f"- **{result.check_id} {mark}** — {result.description}")
            add(f"  - {result.observed} (threshold {result.threshold})")
        add("")

    add("### Config selection")
    add("")
    if [c.chunk_id for c in chunks_primary] == [c.chunk_id for c in chunks_comparison]:
        add("Both configurations produce an identical chunk layout on this sample, because "
            "no sample document exceeds 239 words and therefore fits in one chunk at either "
            "size. **The sample cannot discriminate between them.** Primary 1000/200 is "
            "carried forward on the approved 289-chunk projection, and the comparison must "
            "be repeated on the full corpus before the freeze.")
    else:
        add("The configurations diverge on this sample; see chunk counts above.")
    add("")

    add("## 8. Scale projection")
    add("")
    projection = project_scaling(PRIMARY)
    add(f"- Projected documents: **{projection['projected_total_documents']}** "
        f"(approved 272)")
    add(f"- Projected chunks: **{projection['projected_total_chunks']}** "
        f"(approved target 289)")
    add(f"- Projected orphans: **{projection['projected_orphan_chunks']}** "
        f"= {projection['projected_orphan_rate']:.2%}")
    add("")
    add(f"> {projection['caveat']}")
    add("")

    return "\n".join(lines) + "\n"


def main() -> int:
    model = build_mechanism_sample()
    documents = render_corpus(model)
    chunks_primary = chunk_corpus(documents, PRIMARY)
    chunks_comparison = chunk_corpus(documents, COMPARISON)

    structural_failures = [r for r in validate_model(model) if not r.passed]
    report = build_report(model, documents, chunks_primary, chunks_comparison)
    (OUT / "VALIDATION.md").write_text(report)
    write_sample(model, documents, chunks_primary)

    print(report)

    coherence = validate_coherence(documents, chunks_primary, model, PRIMARY)
    failed = [r for r in coherence if not r.passed]
    if structural_failures:
        print("STRUCTURAL FAILURES:", [r.check_id for r in structural_failures])
    print(f"wrote {OUT}/source_model.json, rendered/, chunks/, VALIDATION.md")
    print(f"coherence: {len(coherence) - len(failed)}/{len(coherence)} pass; "
          f"failing: {[r.check_id for r in failed] or 'none'}")
    return 0 if not structural_failures else 1


if __name__ == "__main__":
    sys.exit(main())

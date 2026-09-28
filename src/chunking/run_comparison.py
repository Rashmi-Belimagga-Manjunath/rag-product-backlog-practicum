"""
Run the approved chunking comparison: 1000/200 vs 600/100.

Selection is made ONLY on the pre-specified C1-C8 coherence criteria. No BM25 and no RAG
result is computed, and none may be used to choose a configuration.

Run:  python3 -m src.chunking.run_comparison
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from ..data_generation.render_v1 import render_corpus
from ..data_generation.v1_sample import build_mechanism_sample
from .pilot import (
    PILOT_LENGTH_TARGETS,
    assert_no_protected_restatements,
    build_pilot_documents,
)
from .splitter import ChunkingConfig, _bag, chunk_corpus, validate_coherence

CONFIGS = [
    ChunkingConfig(1000, 200, "A"),
    ChunkingConfig(600, 100, "B"),
]

OUT = Path("data/synthetic/chunking-pilot")


def evaluate(documents, model, config):
    chunks = chunk_corpus(documents, config)
    results = validate_coherence(documents, chunks, model, config)

    # DIAGNOSTIC ONLY - not a pre-specified criterion, and not used for selection.
    # C6's pre-specified measure is a type-bag containment test at 0.9. That measure is
    # sensitive to how many distinct word TYPES a document uses, independent of whether any
    # text is actually repeated. This diagnostic measures real verbatim repetition with
    # 8-gram containment so the two can be compared.
    def _shingles(text: str, n: int = 8) -> set:
        words = text.lower().split()
        return {tuple(words[i:i + n]) for i in range(max(0, len(words) - n + 1))}

    adjacent = []
    by_doc: dict = {}
    for c in chunks:
        by_doc.setdefault(c.document_id, []).append(c)
    for doc_id, group in by_doc.items():
        group.sort(key=lambda c: c.chunk_index)
        for a_chunk, b_chunk in zip(group, group[1:]):
            sa, sb = _shingles(a_chunk.text), _shingles(b_chunk.text)
            if not sa or not sb:
                continue
            adjacent.append({
                "document_id": doc_id,
                "pair": f"{a_chunk.chunk_id}|{b_chunk.chunk_id}",
                "type_bag_containment": round(
                    len(_bag(a_chunk.text) & _bag(b_chunk.text))
                    / min(len(_bag(a_chunk.text)), len(_bag(b_chunk.text))), 4),
                "ngram8_containment": round(len(sa & sb) / min(len(sa), len(sb)), 4),
            })

    type_diversity = {
        d.document_id: {"tokens": len(d.body.split()),
                        "distinct_types": len(_bag(d.body))}
        for d in documents
    }

    per_type = Counter(c.doc_type for c in chunks)
    multi = {
        doc_id: sum(1 for c in chunks if c.document_id == doc_id)
        for doc_id in {c.document_id for c in chunks}
    }
    words = sorted(c.word_count for c in chunks)

    return {
        "config": config.as_dict(),
        "chunks": len(chunks),
        "documents_spanning_multiple_chunks": sum(1 for v in multi.values() if v > 1),
        "chunks_by_doc_type": dict(sorted(per_type.items())),
        "words": {
            "total": sum(words),
            "min": words[0] if words else 0,
            "median": words[len(words) // 2] if words else 0,
            "max": words[-1] if words else 0,
        },
        "diagnostic": {
            "note": (
                "Diagnostic only. NOT a pre-specified criterion and NOT used to select a "
                "configuration. 8-gram containment measures verbatim repetition; the C6 "
                "type-bag measure is sensitive to type-vocabulary size."
            ),
            "document_type_diversity": type_diversity,
            "adjacent_chunk_pairs": adjacent,
        },
        "checks": [
            {
                "check_id": r.check_id,
                "description": r.description,
                "passed": r.passed,
                "observed": r.observed,
                "threshold": r.threshold,
                "critical": r.critical,
            }
            for r in results
        ],
        "all_pass": all(r.passed for r in results),
        "failed": [r.check_id for r in results if not r.passed],
    }


def main() -> int:
    model = build_mechanism_sample()
    base = render_corpus(model)
    documents = build_pilot_documents(model, base)

    # The guard must pass BEFORE any evaluation, or C2/C3 are meaningless.
    assert_no_protected_restatements(model, documents)

    print("=" * 78)
    print("CHUNKING COMPARISON - long-document pilot")
    print("=" * 78)
    print(f"documents: {len(documents)} "
          f"(from {len(base)} sample documents, extended to approved length targets)")
    print("\nword counts after extension:")
    by_type = {}
    for d in documents:
        by_type.setdefault(d.doc_type, []).append(d.word_count())
    for doc_type in sorted(by_type):
        counts = by_type[doc_type]
        target = PILOT_LENGTH_TARGETS.get(doc_type)
        print(f"  {doc_type:15} n={len(counts):2}  min {min(counts):5} "
              f"max {max(counts):5}  target<= {target}")

    reports = [evaluate(documents, model, c) for c in CONFIGS]

    print()
    for report in reports:
        cfg = report["config"]
        print("-" * 78)
        print(f"CONFIG {cfg['label']}: {cfg['chunk_size']} words / "
              f"{cfg['chunk_overlap']} overlap")
        print("-" * 78)
        print(f"  chunks: {report['chunks']}   "
              f"documents spanning >1 chunk: {report['documents_spanning_multiple_chunks']}")
        w = report["words"]
        print(f"  words: total {w['total']}  min {w['min']}  median {w['median']}  max {w['max']}")
        print(f"  chunks by type: {report['chunks_by_doc_type']}")
        print()
        for check in report["checks"]:
            mark = "PASS" if check["passed"] else "FAIL"
            print(f"  [{mark}] {check['check_id']}  {check['description']}")
            print(f"         {check['observed']}  (threshold {check['threshold']})")
        print()

    print("=" * 78)
    print("DECISION ON PRE-SPECIFIED CRITERIA ONLY")
    print("=" * 78)
    a, b = reports
    # ALL checks count, not just the critical ones. An earlier version of this script
    # filtered to non-critical checks and so silently ignored the C6 failure.
    a_fails = [c["check_id"] for c in a["checks"] if not c["passed"]]
    b_fails = [c["check_id"] for c in b["checks"] if not c["passed"]]

    if not a_fails and not b_fails:
        verdict = ("Both configurations satisfy every pre-specified criterion. The criteria "
                   "do not justify selecting either, and selection on retrieval performance "
                   "is prohibited. Open decision requiring explicit approval.")
    elif a_fails and not b_fails:
        verdict = f"SELECT B (600/100) - only B satisfies every criterion. A fails {a_fails}."
    elif b_fails and not a_fails:
        verdict = f"SELECT A (1000/200) - only A satisfies every criterion. B fails {b_fails}."
    else:
        verdict = (
            f"NO DISCRIMINATION. A fails {a_fails}; B fails {b_fails}. Both configurations "
            f"fail the same pre-specified check, so the criteria do not select between "
            f"them, and selecting on retrieval performance is prohibited. This is a genuine "
            f"open decision requiring explicit approval."
        )
    print(verdict)
    print()
    print("  C6 history (recorded, not a live decision):")
    print("    The original C6 measure was same-document word-TYPE-BAG containment > 0.9.")
    print("    It was replaced on 2026-09-28 by same-document 8-gram containment > 0.5,")
    print("    because type-bag containment saturates in a closed-domain templated corpus")
    print("    and flagged pairs that share no repeated text. See CHUNKING_DECISION.md.")
    print()
    print("  The revision is a corpus/chunk COHERENCE check. It is a project-defined")
    print("  structural validation threshold, not an externally validated constant, and")
    print("  it is NOT a retrieval-performance metric. No BM25 or RAG result exists or may")
    print("  be used to choose a configuration.")
    print()
    for report in reports:
        cfg = report["config"]
        pairs = report["diagnostic"]["adjacent_chunk_pairs"]
        if not pairs:
            continue
        t = [p["type_bag_containment"] for p in pairs]
        n = [p["ngram8_containment"] for p in pairs]
        over_old = sum(1 for v in t if v > 0.9)
        over_new = sum(1 for v in n if v > 0.5)
        print(f"  {cfg['label']} ({cfg['chunk_size']}/{cfg['chunk_overlap']}): "
              f"{len(pairs)} adjacent same-document pair(s) measured; "
              f"type-bag>0.9 flags {over_old}, 8-gram>0.5 flags {over_new}")
        print(f"       mean type-bag {sum(t)/len(t):.3f} (max {max(t):.3f})   "
              f"mean 8-gram {sum(n)/len(n):.3f} (max {max(n):.3f})")

    print()
    print("Observed differences (reported for transparency, NOT a selection basis):")
    print(f"  chunks              A={a['chunks']:4}  B={b['chunks']:4}")
    print(f"  max chunk words     A={a['words']['max']:4}  B={b['words']['max']:4}")
    print(f"  median chunk words  A={a['words']['median']:4}  B={b['words']['median']:4}")

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "pilot": "chunking-comparison",
        "status": "STRUCTURAL COMPARISON ONLY - no BM25/RAG run",
        "documents": len(documents),
        "source": "mechanism sample extended to approved full-corpus length targets",
        "reports": reports,
        "verdict": verdict,
    }
    (OUT / "comparison.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(f"\nwrote {OUT / 'comparison.json'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

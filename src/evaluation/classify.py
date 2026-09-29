"""Error classification for the two systems.

D-009 separates retrieval failure from generation/reasoning failure:

  * BM25 has no generation stage. Every BM25 error is a retrieval error
    (relevant evidence absent from the top-5).
  * RAG has both stages. A classification is evidence-driven and conservative:
    we never manufacture a 'reasoning failure' verdict without the evidence to
    support it. Automated rules used here:

      - retrieval failure: no relevant chunk in the top-5.
      - citation fabrication: a citation whose id was never supplied.
      - unsupported citation (mis-citation): a supplied chunk was cited but is
        not relevant to the query's gold set (retrieved-but-unsupporting).
      - abstention with evidence present: the model said it cannot answer while
        relevant evidence was supplied -> generation/reasoning failure.
      - otherwise: answer quality cannot be classified from evidence alone and
        is marked REQUIRE_MANUAL_REVIEW, never guessed.

  The RAG path therefore intentionally has NO CORRECT branch. D-009 lists
  'Correct' as `P(q) = E(q)`, which requires judging answer/content equivalence
  and cannot be automated from the retrieval log and evidence alone; any case
  that passes the low-level rules above is deferred to REQUIRE_MANUAL_REVIEW
  rather than auto-marked correct. Consequently a reported 'RAG CORRECT = 0' is
  a structural property of the error classifier (category counts), and must be
  distinguished from overall answer correctness, which is evaluated separately
  and is not auto-judged here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.evaluation.ground_truth import QueryGroundTruth
from src.rag.citations import CitationReport

ABSTENTION_LINE = "The retrieved evidence does not contain the answer to this question."


@dataclass(frozen=True)
class Classification:
    query_id: str
    system: str
    judgement: str            # CORRECT | RETRIEVAL_FAILURE | GENERATION_FAILURE | FABRICATION | MIS_CITATION | REQUIRE_MANUAL_REVIEW
    evidence: list[str] = field(default_factory=list)


def abstract_answer_present(answer: str) -> bool:
    """True when the model used the frozen abstention line verbatim."""
    return ABSTENTION_LINE in answer


def classify_bm25(retrieved_chunk_ids: list[str], ground_truth: QueryGroundTruth) -> Classification:
    if any(cid in ground_truth.relevant_chunk_ids for cid in retrieved_chunk_ids):
        return Classification(
            query_id=ground_truth.query_id,
            system="bm25",
            judgement="CORRECT",
            evidence=["at least one relevant chunk in top-5"],
        )
    return Classification(
        query_id=ground_truth.query_id,
        system="bm25",
        judgement="RETRIEVAL_FAILURE",
        evidence=["no relevant chunk in top-5"],
    )


@dataclass(frozen=True)
class RagClassificationInputs:
    retrieved_chunk_ids: list[str]
    ground_truth: QueryGroundTruth
    citation_report: CitationReport
    answer: str


def classify_rag(inputs: RagClassificationInputs) -> Classification:
    relevant = inputs.ground_truth.relevant_chunk_ids
    has_relevant = any(cid in relevant for cid in inputs.retrieved_chunk_ids)

    evidence: list[str] = []

    if inputs.citation_report.fabricated:
        evidence.append(
            f"fabricated citations: {[c.raw for c in inputs.citation_report.fabricated][:5]}"
        )
    if inputs.citation_report.unknown_raw:
        evidence.append(f"unparseable citation tokens: {inputs.citation_report.unknown_raw[:5]}")

    # A fabricated or unparseable identifier is never forgivable at any stage.
    if inputs.citation_report.fabricated or inputs.citation_report.unknown_raw:
        return Classification(
            query_id=inputs.ground_truth.query_id,
            system="rag",
            judgement="FABRICATION",
            evidence=evidence,
        )

    if not has_relevant:
        return Classification(
            query_id=inputs.ground_truth.query_id,
            system="rag",
            judgement="RETRIEVAL_FAILURE",
            evidence=["no relevant chunk in top-5"] + evidence,
        )

    # Cited but not-relevant supplied chunks: retrieved-but-unsupporting.
    unsupported = [
        c for c in inputs.citation_report.supplied_cited
        if f"{c.document_id}#C{c.chunk_index}" not in relevant
    ]
    if unsupported:
        evidence.append(
            f"retrieved-but-unsupporting citations: {[c.raw for c in unsupported][:5]}"
        )
        return Classification(
            query_id=inputs.ground_truth.query_id,
            system="rag",
            judgement="MIS_CITATION",
            evidence=evidence,
        )

    # Evidence supplied but the model abstained -> it failed to use it.
    if abstract_answer_present(inputs.answer):
        return Classification(
            query_id=inputs.ground_truth.query_id,
            system="rag",
            judgement="GENERATION_FAILURE",
            evidence=["relevant evidence supplied but model abstained"],
        )

    # Citations present and at least one relevant chunk supplied. Beyond this we
    # cannot judge answer correctness from evidence alone; the automated run marks
    # it for manual review instead of inventing a verdict.
    return Classification(
        query_id=inputs.ground_truth.query_id,
        system="rag",
        judgement="REQUIRE_MANUAL_REVIEW",
        evidence=["relevant evidence retrieved; answer correctness needs human review"],
    )


def summarize(classifications: list[Classification]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for classification in classifications:
        counts[classification.judgement] = counts.get(classification.judgement, 0) + 1
    return counts
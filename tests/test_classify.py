import pytest

from src.evaluation.classify import (
    RagClassificationInputs,
    abstract_answer_present,
    classify_bm25,
    classify_rag,
    summarize,
)
from src.evaluation.ground_truth import QueryGroundTruth
from src.rag.citations import Citation, CitationReport

A0 = "DOC-A#C0"
A1 = "DOC-A#C1"


def make_gt(relevant=(A0, A1)):
    return QueryGroundTruth(
        query_id="Q-01",
        slot=None,
        relevant_document_ids=("DOC-A",),
        relevant_chunk_ids=tuple(relevant),
        expected_dependencies=(),
        is_dependency_query=False,
        dependency_explicitness="none",
        relevance_basis="test",
    )


def make_report(fabricated=(), supplied=()):
    return CitationReport(
        citations=[],
        fabricated=[Citation(raw=c, document_id=c.split("#")[0], chunk_index=0) for c in fabricated],
        supplied_cited=[Citation(raw=c, document_id=c.split("#")[0], chunk_index=0) for c in supplied],
        unknown_raw=[],
    )


def make_inputs(retrieved, gt, report=None, answer=f"Supported by [{A0}]."):
    return RagClassificationInputs(
        retrieved_chunk_ids=list(retrieved),
        ground_truth=gt,
        citation_report=report if report is not None else make_report(),
        answer=answer,
    )


class TestAbstentionLine:
    def test_verbatim_line_detected(self):
        assert abstract_answer_present(
            "The retrieved evidence does not contain the answer to this question."
        ) is True
        assert abstract_answer_present("I cannot find that.") is False


class TestClassifyBM25:
    def test_correct_when_relevant_retrieved(self):
        c = classify_bm25([A0, "x"], make_gt())
        assert c.judgement == "CORRECT"

    def test_retrieval_failure_when_none_relevant(self):
        c = classify_bm25(["x1", "x2"], make_gt())
        assert c.judgement == "RETRIEVAL_FAILURE"
        assert c.system == "bm25"


class TestClassifyRAG:
    def test_fabrication_is_fatal(self):
        gt = make_gt()
        report = make_report(fabricated=["DOC-FAKE#C9"], supplied=[])
        c = classify_rag(make_inputs([A0], gt, report))
        assert c.judgement == "FABRICATION"

    def test_unknown_tokens_are_fabrication(self):
        report = CitationReport(citations=[], fabricated=[], supplied_cited=[],
                                unknown_raw=["[junk]"])
        c = classify_rag(make_inputs([A0], make_gt(), report))
        assert c.judgement == "FABRICATION"

    def test_retrieval_failure_when_no_relevant(self):
        gt = make_gt(relevant=("DOC-C#C0",))
        c = classify_rag(make_inputs(["x1", "x2"], gt))
        assert c.judgement == "RETRIEVAL_FAILURE"

    def test_mis_citation_when_supplied_but_unsupporting(self):
        gt = make_gt(relevant=(A0,))
        report = make_report(supplied=["DOC-B#C0"])
        c = classify_rag(make_inputs([A0, "DOC-B#C0"], gt, report))
        assert c.judgement == "MIS_CITATION"

    def test_generation_failure_when_abstains_with_evidence(self):
        gt = make_gt(relevant=(A0,))
        c = classify_rag(make_inputs(
            [A0], gt, answer="The retrieved evidence does not contain the answer to this question."
        ))
        assert c.judgement == "GENERATION_FAILURE"

    def test_manual_review_when_unverifiable(self):
        gt = make_gt(relevant=(A0,))
        report = make_report(supplied=[A0])
        c = classify_rag(make_inputs([A0], gt, report))
        assert c.judgement == "REQUIRE_MANUAL_REVIEW"

    def test_no_manufactured_verdict_without_evidence(self):
        # retrieval ok + supplied citations to a relevant chunk, but the answer
        # never says it supports the gold fact -> we must not guess it is correct.
        gt = make_gt(relevant=(A0,))
        report = make_report(supplied=[A0])
        c = classify_rag(make_inputs([A0], gt, report))
        assert c.judgement == "REQUIRE_MANUAL_REVIEW"


class TestSummarize:
    def test_counts(self):
        counts = summarize([
            classify_bm25([A0], make_gt()),
            classify_bm25(["x"], make_gt()),
        ])
        assert counts["CORRECT"] == 1
        assert counts["RETRIEVAL_FAILURE"] == 1
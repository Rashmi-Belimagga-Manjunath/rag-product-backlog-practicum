import pytest

from src.rag import citations as ci
from src.rag.context import build_context
from src.rag.generator import RAGConfig, prompt_sha256, verify_frozen_prompt
from src.retrieval.units import RetrievalUnit, RetrievalUnitSet
from tests.fake_client import FakeClient


def make_unit(chunk_id, text="some content"):
    document_id = chunk_id.rsplit("-C", 1)[0]
    return RetrievalUnit(
        chunk_id=chunk_id,
        document_id=document_id,
        chunk_index=int(chunk_id.rsplit("-C", 1)[1]),
        text=text,
        version_status="current",
    )


UNITS = RetrievalUnitSet(
    units=[make_unit("DOC-PRD-A-01-v2-C0"), make_unit("DOC-PRD-A-01-v2-C1")],
    by_id={
        "DOC-PRD-A-01-v2-C0": make_unit("DOC-PRD-A-01-v2-C0"),
        "DOC-PRD-A-01-v2-C1": make_unit("DOC-PRD-A-01-v2-C1"),
    },
    by_document={"DOC-PRD-A-01-v2": [
        make_unit("DOC-PRD-A-01-v2-C0"), make_unit("DOC-PRD-A-01-v2-C1")]},
)


class TestFrozenPrompt:
    def test_hash_matches_frozen_doc(self):
        assert prompt_sha256() == \
            "7ab15349db7a7a5db04c3b1a5f6aa52505a4f7bbc3e7d1a37ea234b4ca553dc1"

    def test_verify_frozen_prompt_ok(self):
        verify_frozen_prompt()  # must not raise


class TestContext:
    def test_passages_numbered_in_rank_order(self):
        hits = [
            {"chunk_id": "DOC-PRD-A-01-v2-C0", "document_id": "DOC-PRD-A-01-v2", "score": 0.9},
            {"chunk_id": "DOC-PRD-A-01-v2-C1", "document_id": "DOC-PRD-A-01-v2", "score": 0.8},
        ]
        from src.vectorstore.store import VectorHit
        hit_objs = [VectorHit(h["chunk_id"], h["score"], h["document_id"]) for h in hits]
        context = build_context("question?", hit_objs, UNITS, "sha")
        block = context.passage_block()
        assert block.startswith("Passage 1\nPassage ID: DOC-PRD-A-01-v2#C0")
        assert "Passage 2\nPassage ID: DOC-PRD-A-01-v2#C1" in block

    def test_messages_contain_frozen_system_instruction(self):
        from src.vectorstore.store import VectorHit
        hit = [VectorHit("DOC-PRD-A-01-v2-C0", 0.9, "DOC-PRD-A-01-v2")]
        context = build_context("question?", hit, UNITS, "sha")
        messages = context.to_messages()
        assert messages[0]["role"] == "system"
        assert "Answer the question using ONLY those passages" in messages[0]["content"]
        assert "CITATION ON EVERY CLAIM" in messages[0]["content"].upper()
        assert messages[1]["role"] == "user"
        assert "Question: question?" in messages[1]["content"]


class TestCitationParse:
    def test_extract_citations(self):
        answer = "Value X [DOC-PRD-A-01-v2#C0] and Y [DOC-PRD-A-01-v2#C1]."
        assert ci.extract_citations(answer) == ["DOC-PRD-A-01-v2#C0", "DOC-PRD-A-01-v2#C1"]

    def test_parse_good_and_unknown(self):
        parsed, unknown = ci.parse_all(["DOC-PRD-A-01-v2#C0", "not-a-citation"])
        assert len(parsed) == 1
        assert unknown == ["not-a-citation"]

    def test_validates_supplied_ids(self):
        citations, _ = ci.parse_all(["DOC-PRD-A-01-v2#C0"])
        report = ci.validate(citations, {"DOC-PRD-A-01-v2#C0"})
        assert report.fabricated == []
        assert len(report.supplied_cited) == 1

    def test_flags_fabricated_when_never_supplied(self):
        citations, _ = ci.parse_all(["DOC-PRD-A-01-v2#C0"])
        report = ci.validate(citations, {"DOC-PRD-A-99-v9#C7"})
        assert len(report.fabricated) == 1
        assert report.supplied_cited == []

    def test_supplied_citation_ids_from_chunk_ids(self):
        supplied = ci.supplied_citation_ids(["DOC-PRD-A-01-v2-C0"])
        assert supplied == {"DOC-PRD-A-01-v2#C0"}

    def test_supplied_citation_ids_handle_embedded_dash_c_in_document_ids(self):
        # Component document ids contain "-C" (e.g. DOC-COMP-M-05). Only the
        # trailing -C<index> is the chunk suffix; the document id must survive.
        supplied = ci.supplied_citation_ids(["DOC-COMP-M-05-C0", "DOC-PRD-A-01-v2-C0"])
        assert supplied == {"DOC-COMP-M-05#C0", "DOC-PRD-A-01-v2#C0"}


class TestGeneratorParameters:
    def test_frozen_parameters_sent(self):
        client = FakeClient(respond_with="Gold answer. [DOC-PRD-A-01-v2#C0]")
        config = RAGConfig.load()
        assert config.model_name == "gpt-4o-mini"
        assert config.temperature == 0.0
        assert config.max_tokens == 800
        assert config.n == 1
        assert config.seed is None

    def test_kwargs_omit_null_top_p_and_seed(self):
        from src.rag.context import Context
        from src.rag.generator import generate

        client = FakeClient()
        config = RAGConfig.load()
        context = Context(question="q", passages=[], prompt_sha256=prompt_sha256())
        result = generate(client, config, context)
        kwargs = client.record[-1]
        assert "top_p" not in kwargs
        assert "seed" not in kwargs
        assert kwargs["temperature"] == 0.0
        assert kwargs["max_tokens"] == 800
        assert kwargs["n"] == 1

    def test_generation_returns_answer_and_usage(self):
        client = FakeClient(respond_with="Fixture answer. [DOC-PRD-A-01-v2#C0]")
        config = RAGConfig.load()
        from src.rag.context import Context
        from src.rag.generator import generate
        context = Context(question="q", passages=[], prompt_sha256=prompt_sha256())
        result = generate(client, config, context)
        assert result.answer == "Fixture answer. [DOC-PRD-A-01-v2#C0]"
        assert result.finish_reason == "stop"
        assert result.usage["total_tokens"] >= 0
        assert result.latency_seconds >= 0.0
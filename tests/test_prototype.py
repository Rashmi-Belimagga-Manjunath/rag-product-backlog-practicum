import pytest

from src.prototype.pipeline import DemoPipeline
from tests.fake_client import FakeClient, make_query_embedding


@pytest.fixture(scope="module")
def pipeline():
    return DemoPipeline()


class TestDemoPipeline:
    def test_bm25_retrieve_works_on_real_corpus(self, pipeline):
        hits = pipeline.bm25_retrieve("describe the tax engine approval workflow")
        assert hits
        # the demo BM25 uses the same frozen implementation, same top-k
        assert len(hits) <= pipeline.bm25_config.top_k
        assert set(hits[0].keys()) == {"chunk_id", "rank", "score", "document_id"}

    def test_bm25_passages_render_with_citation(self, pipeline):
        hits = pipeline.bm25_retrieve("describe the tax engine approval workflow", top_k=1)
        passages = pipeline.bm25_passages(hits)
        assert "Passage 1" in passages[0]
        assert "#C" in passages[0]

    def test_no_benchmark_write_on_demo(self, pipeline, tmp_path, monkeypatch):
        # DemoPipeline never writes to experiments/runs, results/ or the workbook.
        import os

        for root in ["experiments/runs", "results"]:
            before = set(os.listdir(root)) if os.path.isdir(root) else set()
            pipeline.bm25_retrieve("a generic demonstration question")
            after = set(os.listdir(root)) if os.path.isdir(root) else set()
            assert after == before, f"demo wrote into {root}"

    def test_answer_endpoint_with_fake_client_and_no_chroma(self, pipeline, monkeypatch):
        # RAG path is stubbed so no Chroma directory is created; this exercises
        # the answer() assembly + fake generation without any API/networking.
        monkeypatch.setattr(pipeline, "rag_retrieve", lambda q, e, top_k=None: [])
        client = FakeClient(respond_with="Demo answer. [DOC-PRD-A-01-v2#C0]")

        def embed_query(text):
            return make_query_embedding(text)

        result = pipeline.answer("demo question", client, embed_query)
        assert result.status == "ok"
        assert result.rag_answer.startswith("Demo answer.")
        assert result.model == "gpt-4o-mini"
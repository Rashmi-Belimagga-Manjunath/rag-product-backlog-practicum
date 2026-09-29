import math

import pytest

from src.bm25.retriever import BM25Config, BM25Index
from src.retrieval.units import RetrievalUnit, RetrievalUnitSet


def make_units(records):
    """records: list of (chunk_id, text)."""
    units = []
    for chunk_id, text in records:
        document_id = chunk_id.rsplit("-C", 1)[0]
        units.append(
            RetrievalUnit(
                chunk_id=chunk_id,
                document_id=document_id,
                chunk_index=int(chunk_id.rsplit("-C", 1)[1]),
                text=text,
            )
        )
    by_id = {u.chunk_id: u for u in units}
    by_document = {}
    for u in units:
        by_document.setdefault(u.document_id, []).append(u)
    return RetrievalUnitSet(units=units, by_id=by_id, by_document=by_document)


@pytest.fixture(scope="module")
def config():
    return BM25Config.load()


class TestConfigLoad:
    def test_frozen_values(self, config):
        assert config.k1 == 1.5
        assert config.b == 0.75
        assert config.idf == "lucene"
        assert config.top_k == 5
        assert config.tie_breaking == "ascending chunk ID"
        assert config.lowercase is True
        assert config.stemming is False
        assert config.stopword_removal is False
        assert config.verbatim_queries is True

    def test_idf_formula_constant(self, config):
        assert "ln(1 + (N - df(t) + 0.5)" in config.idf_formula


class TestBM25HandComputed:
    def test_lucene_idf_hand_value(self, config):
        units = make_units([
            ("A-C0", "apple pie recipe"),
            ("B-C0", "apple banana"),
            ("C-C0", "banana bread recipe"),
        ])
        index = BM25Index(units, config)
        # term "recipe" appears in 2 of 3 units (df=2), dry IDF for the corpus:
        expected_idf = math.log(1.0 + (3 - 2 + 0.5) / (2 + 0.5))
        assert index.term_idf["recipe"] == pytest.approx(expected_idf)

    def test_scores_rank_by_relevance(self, config):
        units = make_units([
            ("A-C0", "apple pie recipe"),
            ("B-C0", "apple banana"),
            ("C-C0", "banana bread recipe"),
        ])
        index = BM25Index(units, config)
        ranked = index.search("apple recipe")
        ids = [units.units[p].chunk_id for p, _ in ranked]
        assert ids == ["A-C0", "B-C0", "C-C0"]

    def test_score_is_sum_of_tfidf(self, config):
        units = make_units([("A-C0", "alpha beta"), ("B-C0", "gamma")])
        index = BM25Index(units, config)
        # Document 0 contains both query terms; document 1 neither.
        alpha_idf = index.term_idf["alpha"]
        beta_idf = index.term_idf["beta"]
        # f=1 for both terms, same document length, so tf is identical for both.
        length = 2
        tf = (1.0 * (config.k1 + 1)) / (
            1.0 + config.k1 * (1 - config.b + config.b * length / index.average_document_length)
        )
        expected = (alpha_idf + beta_idf) * tf
        score = index.score_document(0, ["alpha", "beta"])
        assert score == pytest.approx(expected)


class TestDeterminism:
    def test_ties_break_ascending_chunk_id(self, config):
        units = make_units([
            ("DOC-B-C0", "identical wording here"),
            ("DOC-A-C0", "identical wording here"),
        ])
        index = BM25Index(units, config)
        ids = [units.units[p].chunk_id for p, _ in index.search("identical wording here")]
        assert ids == ["DOC-A-C0", "DOC-B-C0"]

    def test_identical_inputs_identical_output(self, config):
        units = make_units([("A-C0", "alpha beta"), ("B-C0", "beta alpha")])
        index = BM25Index(units, config)
        first = index.search("alpha")
        second = index.search("alpha")
        assert [(p, round(s, 9)) for p, s in first] == [(p, round(s, 9)) for p, s in second]

    def test_query_is_verbatim_not_expanded(self, config):
        units = make_units([("A-C0", "apple")])
        index = BM25Index(units, config)
        assert len(index.search("apple pie")) == 1  # only "apple" matches

    def test_result_logs_frozen_fields(self, config):
        units = make_units([("A-C0", "apple pie")])
        index = BM25Index(units, config)
        result = index.query("Q-1", "apple")
        hit = result.hits[0]
        assert set(hit.as_dict().keys()) == {
            "chunk_id", "rank", "score", "document_id"
        }
        assert result.chunk_ids() == ["A-C0"]
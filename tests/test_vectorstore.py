import numpy as np
import pytest

from src.embeddings.cache import EmbeddingMeta, LoadedMatrix
from src.vectorstore.store import CrossCheckResult, VectorStore, numpy_crosscheck
from src.retrieval.units import RetrievalUnit, RetrievalUnitSet
from src.vectorstore.store import _embedding_list


def make_units_and_matrix(n=8, dimension=16):
    units = []
    rng = np.random.default_rng(42)
    matrix = rng.normal(size=(n, dimension)).astype(np.float32)
    # normalise rows so cosine distance behaves
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    matrix = matrix / norms
    for i in range(n):
        chunk_id = f"DOC-{i:02d}-C0"
        units.append(
            RetrievalUnit(
                chunk_id=chunk_id,
                document_id=f"DOC-{i:02d}",
                chunk_index=0,
                text=f"text {i}",
                source_entity_id=f"E{i}",
            )
        )
    by_id = {u.chunk_id: u for u in units}
    by_document = {}
    for u in units:
        by_document.setdefault(u.document_id, []).append(u)
    unit_set = RetrievalUnitSet(units=units, by_id=by_id, by_document=by_document)
    meta = EmbeddingMeta(
        model_name="test", model_snapshot="test", embedding_dimension=dimension,
        generated_date="t", corpus_version="v1", chunking_version="v1",
        chunk_id_order=unit_set.chunk_id_order,
    )
    loaded = LoadedMatrix(matrix=matrix, meta=meta, fingerprint="fp-test")
    return unit_set, loaded


def build_store(tmp_path, n=8, dimension=16):
    units, loaded = make_units_and_matrix(n, dimension)
    store = VectorStore(persist_directory=str(tmp_path), collection_name="test")
    summary = store.build_from_loaded(loaded, units)
    return store, units, loaded, summary


def query_similar_to(loaded, index):
    return (np.asarray(loaded.matrix)[index]).copy()


class TestVectorStore:
    def test_build_count_and_dimension(self, tmp_path):
        store, units, loaded, summary = build_store(tmp_path)
        assert summary["count"] == 8
        assert summary["dimension"] == 16

    def test_topk_returns_finite_sorted(self, tmp_path):
        store, units, loaded, _ = build_store(tmp_path)
        q = query_similar_to(loaded, 0)
        hits = store.search_topk(q, 3, units)
        assert len(hits) == 3
        # cosine similarity of unit vectors lives within [-1, 1]; allow the
        # float tolerance that Chroma's 1-distance produces.
        assert all(abs(h.score) <= 1.0 + 1e-6 for h in hits)
        # top hit should be the query's own chunk
        assert hits[0].chunk_id == units.units[0].chunk_id

    def test_tie_break_ascending_chunk_id(self, tmp_path):
        # Two chunks with IDENTICAL embeddings are a genuine score tie; the
        # frozen tie-break sorts by ascending chunk id.
        units, loaded = make_units_and_matrix(3, 16)
        two = np.asarray(loaded.matrix)[0].copy()
        matrix = np.stack([two, two, np.asarray(loaded.matrix)[2]])
        from src.embeddings.cache import EmbeddingMeta as EM

        meta = EM(
            model_name="test", model_snapshot="test", embedding_dimension=16,
            generated_date="t", corpus_version="v1", chunking_version="v1",
            chunk_id_order=units.chunk_id_order,
        )
        loaded_tie = LoadedMatrix(matrix=matrix, meta=meta, fingerprint="fp-tie")
        store = VectorStore(persist_directory=str(tmp_path), collection_name="tie")
        store.build_from_loaded(loaded_tie, units)
        hits = store.search_topk(two, 3, units)
        ids = [h.chunk_id for h in hits]
        assert ids[0] == "DOC-00-C0" and ids[1] == "DOC-01-C0"

    def test_search_maps_document_id(self, tmp_path):
        store, units, loaded, _ = build_store(tmp_path)
        q = query_similar_to(loaded, 2)
        hits = store.search_topk(q, 1, units)
        assert hits[0].document_id == "DOC-02"


class TestListVsNumpyEmbedding:
    def test_search_accepts_python_list_embedding(self, tmp_path):
        # Regression for the Streamlit demo crash: the prototype embeds through
        # the OpenAI SDK, which returns a plain Python list (encoding_format
        # 'float'); search_topk must not call .tolist() on it.
        store, units, loaded, _ = build_store(tmp_path)
        q_array = query_similar_to(loaded, 0)
        q_list = q_array.tolist()
        assert type(q_list) is list
        hits_list = store.search_topk(q_list, 3, units)
        hits_array = store.search_topk(q_array, 3, units)
        assert [h.chunk_id for h in hits_list] == [h.chunk_id for h in hits_array]
        assert hits_list[0].chunk_id == units.units[0].chunk_id

    def test_query_native_accepts_python_list_embedding(self, tmp_path):
        store, units, loaded, _ = build_store(tmp_path)
        q_list = query_similar_to(loaded, 0).tolist()
        result = store.query_native(q_list, 1)
        assert result["ids"]
        assert len(result["ids"][0]) == 1

    def test_unknown_embedding_type_raises_type_error(self, tmp_path):
        store, units, loaded, _ = build_store(tmp_path)
        with pytest.raises(TypeError):
            store.search_topk("not-an-embedding", 3, units)

    def test_embedding_list_helper_preserves_types(self):
        array = np.array([0.1, 0.2, 0.3])
        assert _embedding_list(array) == [0.1, 0.2, 0.3]
        assert _embedding_list([0.1, 0.2, 0.3]) == [0.1, 0.2, 0.3]
        with pytest.raises(TypeError):
            _embedding_list(None)


class TestNumpyCrosscheck:
    def test_agreement_ok(self, tmp_path):
        store, units, loaded, _ = build_store(tmp_path)
        q = query_similar_to(loaded, 1)
        hits = store.search_topk(q, 3, units)
        result = numpy_crosscheck(store, loaded, q, hits, 3)
        assert isinstance(result, CrossCheckResult)
        assert result.ok is True

    def test_mismatch_is_reported_not_silent(self, tmp_path):
        store, units, loaded, _ = build_store(tmp_path)
        q = query_similar_to(loaded, 1)
        hits = store.search_topk(q, 3, units)
        # deliberately corrupt the order the store reported
        wrong_order = [hits[1], hits[0], hits[2]]
        result = numpy_crosscheck(store, loaded, q, wrong_order, 3)
        assert result.ok is False
        assert result.order_match is False

    def test_zero_norm_query_detected(self, tmp_path):
        store, units, loaded, _ = build_store(tmp_path)
        zero = np.zeros(16, dtype=np.float32)
        result = numpy_crosscheck(store, loaded, zero, [], 3)
        assert result.ok is False

    def test_crosscheck_never_modifies_results(self, tmp_path):
        store, units, loaded, _ = build_store(tmp_path)
        q = query_similar_to(loaded, 0)
        before = store.search_topk(q, 5, units)
        fingerprint_before = loaded.fingerprint
        numpy_crosscheck(store, loaded, q, before, 5)
        after = store.search_topk(q, 5, units)
        assert before == after  # cross-check is read-only
        assert fingerprint_before == loaded.fingerprint
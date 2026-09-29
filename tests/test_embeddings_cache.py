import numpy as np
import pytest

from src.embeddings import cache
from src.embeddings.cache import EmbeddingMeta


def make_meta(n=4, dimension=64):
    return EmbeddingMeta(
        model_name="text-embedding-3-large",
        model_snapshot="text-embedding-3-large",
        embedding_dimension=dimension,
        generated_date="2026-09-28",
        corpus_version="v1",
        chunking_version="v1",
        chunk_id_order=[f"DOC-{i}-C0" for i in range(1, n + 1)],
        matrix_creation_frozen_block={"model": "text-embedding-3-large"},
        frozen_config_git_commit="test-hash",
        token_usage={"total_tokens": 500, "requests": 1},
    )


def make_matrix(n=4, dimension=64):
    rng = np.random.default_rng(7)
    return rng.normal(size=(n, dimension)).astype(np.float32)


class TestSaveLoad:
    def test_roundtrip_preserves_values_and_order(self, tmp_path):
        npy = str(tmp_path / "embeddings.npy")
        sidecar = str(tmp_path / "embeddings.meta.json")
        meta = make_meta()
        matrix = make_matrix()

        summary = cache.save_matrix(matrix, meta, npy, sidecar)
        assert summary["rows"] == 4
        assert summary["columns"] == 64
        assert len(summary["sha256"]) == 64

        loaded = cache.load_matrix(npy, sidecar)
        np.testing.assert_array_equal(loaded.matrix, matrix)
        assert loaded.meta.chunk_id_order == meta.chunk_id_order
        assert loaded.fingerprint == summary["sha256"]

    def test_sidecar_records_frozen_fields(self, tmp_path):
        import json

        npy = str(tmp_path / "embeddings.npy")
        sidecar = str(tmp_path / "embeddings.meta.json")
        cache.save_matrix(make_matrix(), make_meta(), npy, sidecar)
        with open(sidecar, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        # sidecar_fields from the frozen config, unchanged:
        for field in ["model_name", "embedding_dimension", "generated_date",
                      "corpus_version", "chunking_version", "chunk_id_order",
                      "matrix_creation_frozen_block", "frozen_config_git_commit",
                      "token_usage"]:
            assert field in raw

    def test_dimension_mismatch_rejected(self, tmp_path):
        npy = str(tmp_path / "embeddings.npy")
        sidecar = str(tmp_path / "embeddings.meta.json")
        with pytest.raises(ValueError):
            cache.save_matrix(make_matrix(dimension=8), make_meta(4, 64), npy, sidecar)

    def test_row_count_mismatch_rejected(self, tmp_path):
        npy = str(tmp_path / "embeddings.npy")
        sidecar = str(tmp_path / "embeddings.meta.json")
        with pytest.raises(ValueError):
            cache.save_matrix(make_matrix(n=2), make_meta(4), npy, sidecar)

    def test_load_missing_artefact_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            cache.load_matrix(str(tmp_path / "missing.npy"),
                              str(tmp_path / "missing.meta.json"))

    def test_empty_schema_reference(self):
        schema = cache.embed_record_schema()
        assert set(schema) == {
            "model_name", "model_snapshot", "embedding_dimension", "generated_date",
            "corpus_version", "chunking_version", "chunk_id_order",
            "matrix_creation_frozen_block", "frozen_config_git_commit", "token_usage",
        }
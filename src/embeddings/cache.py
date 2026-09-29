"""Cache layer for the frozen embedding matrix.

The embedding matrix is a reproducibility artefact (embedding_config.json
reproducibility_artifact): a run reuses the byte-identical stored vectors rather
than re-calling the model. This module performs NO API calls. It writes and
reads the .npy matrix plus the sidecar .meta.json, and validates that every load
matches the frozen expectations before anything can consume it.

The API call itself lives in src/embeddings/generate.py and is only ever opened
at the explicit freeze step, never in tests.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

EMBEDDINGS_PATH = "data/embeddings/v1-corpus/embeddings.npy"
SIDECAR_PATH = "data/embeddings/v1-corpus/embeddings.meta.json"


@dataclass(frozen=True)
class EmbeddingMeta:
    """The frozen sidecar fields (embedding_config.json sidecar_fields)."""

    model_name: str
    model_snapshot: str
    embedding_dimension: int
    generated_date: str
    corpus_version: str
    chunking_version: str
    chunk_id_order: list[str] = field(default_factory=list)
    matrix_creation_frozen_block: dict = field(default_factory=dict)
    frozen_config_git_commit: str = ""
    token_usage: dict = field(default_factory=dict)


def embed_record_schema() -> dict:
    """Return an empty sidecar record so callers share the same field schema."""
    return {
        "model_name": "",
        "model_snapshot": "",
        "embedding_dimension": 0,
        "generated_date": "",
        "corpus_version": "",
        "chunking_version": "",
        "chunk_id_order": "",
        "matrix_creation_frozen_block": {},
        "frozen_config_git_commit": "",
        "token_usage": {},
    }


def matrix_sha256(matrix_path: str = EMBEDDINGS_PATH) -> str:
    """Hash of the stored .npy bytes, used as the artifact fingerprint.

    A SHA-256 over the file bytes is stable across runs and survives in the
    FREEZE manifest plus run logs, so two runs can prove they used identical
    vectors.
    """
    digest = hashlib.sha256()
    with open(matrix_path, "rb") as handle:
        # npy files are ~3.3 MB (3072 float32 x 272 rows); one read is fine here.
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def save_matrix(matrix, meta: EmbeddingMeta, npy_path: str = EMBEDDINGS_PATH, sidecar_path: str = SIDECAR_PATH) -> dict:
    """Persist the matrix and its sidecar; return the sha256 fingerprint.

    matrix must be a 2-D float32 numpy array whose row order is meta.chunk_id_order.
    """
    import numpy as np

    matrix = np.asarray(matrix, dtype=np.float32)
    rows, columns = matrix.shape
    if columns != meta.embedding_dimension:
        raise ValueError(
            f"matrix has {columns} columns but frozen dimension is {meta.embedding_dimension}"
        )
    if rows != len(meta.chunk_id_order):
        raise ValueError(
            f"matrix has {rows} rows but chunk_id_order has {len(meta.chunk_id_order)} ids"
        )

    path = Path(npy_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, matrix)

    sidecar = {
        "model_name": meta.model_name,
        "model_snapshot": meta.model_snapshot,
        "embedding_dimension": meta.embedding_dimension,
        "generated_date": meta.generated_date,
        "corpus_version": meta.corpus_version,
        "chunking_version": meta.chunking_version,
        "chunk_id_order": meta.chunk_id_order,
        "matrix_creation_frozen_block": meta.matrix_creation_frozen_block,
        "frozen_config_git_commit": meta.frozen_config_git_commit,
        "token_usage": meta.token_usage,
    }
    with open(sidecar_path, "w", encoding="utf-8") as handle:
        json.dump(sidecar, handle, indent=2, sort_keys=True)
        handle.write("\n")

    return {"sha256": matrix_sha256(npy_path), "rows": rows, "columns": columns}


@dataclass(frozen=True)
class LoadedMatrix:
    matrix: object  # np.ndarray, avoided at import time to keep module numpy-free
    meta: EmbeddingMeta
    fingerprint: str


def load_matrix(npy_path: str = EMBEDDINGS_PATH, sidecar_path: str = SIDECAR_PATH) -> LoadedMatrix:
    """Load and validate the stored matrix + sidecar.

    Raises FileNotFoundError if the artefact does not exist yet (expected before
    the freeze step); raises ValueError if the sidecar contradicts the frozen
    expectations (dimension, id order length).
    """
    import numpy as np

    if not Path(npy_path).exists() or not Path(sidecar_path).exists():
        raise FileNotFoundError(
            "embedding artefact not found; it is only created at the approved freeze step "
            "(order A-K). Check data/embeddings/v1-corpus/."
        )

    with open(sidecar_path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)

    meta = EmbeddingMeta(
        model_name=str(raw["model_name"]),
        model_snapshot=str(raw["model_snapshot"]),
        embedding_dimension=int(raw["embedding_dimension"]),
        generated_date=str(raw["generated_date"]),
        corpus_version=str(raw["corpus_version"]),
        chunking_version=str(raw["chunking_version"]),
        chunk_id_order=list(raw["chunk_id_order"]),
        matrix_creation_frozen_block=dict(raw.get("matrix_creation_frozen_block") or {}),
        frozen_config_git_commit=str(raw.get("frozen_config_git_commit", "")),
        token_usage=dict(raw.get("token_usage") or {}),
    )

    matrix = np.load(npy_path, allow_pickle=False)
    rows, columns = matrix.shape
    if rows != len(meta.chunk_id_order):
        raise ValueError(
            f"matrix rows {rows} != sidecar chunk_id_order length {len(meta.chunk_id_order)}"
        )
    if columns != meta.embedding_dimension:
        raise ValueError(
            f"matrix columns {columns} != frozen dimension {meta.embedding_dimension}"
        )

    return LoadedMatrix(matrix=matrix, meta=meta, fingerprint=matrix_sha256(npy_path))
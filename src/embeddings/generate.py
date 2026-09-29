"""Generation of the frozen embedding matrix via the OpenAI API.

THIS MODULE IS CALLED ONLY AT THE APPROVED FREEZE STEP (never in tests, and not
during the checkpoint review). It performs real API calls and records the
byte-identical matrix + sidecar for reuse by every later run.

The client is injected so the module can be unit-tested against a fake, but the
default paths (cache.py) refuse to save into data/ unless an explicit
save_placeholder strategy is given — the real save path is the freeze step.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import numpy as np

from src.embeddings.cache import EmbeddingMeta, save_matrix

EMBEDDING_CONFIG_PATH = "experiments/configs/embedding_config.json"


@dataclass(frozen=True)
class EmbeddingConfig:
    model_name: str
    embedding_dimension: int
    dimensions: object  # the frozen 'dimensions': None — must never be set
    encoding_format: str
    max_input_tokens_per_string: int
    max_total_tokens_per_request: int
    target_tokens_per_request: int
    metric: str
    persist_directory: str

    @classmethod
    def load(cls, path: str = EMBEDDING_CONFIG_PATH) -> "EmbeddingConfig":
        import json

        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        return cls(
            model_name=str(raw["model_name"]),
            embedding_dimension=int(raw["embedding_dimension"]),
            dimensions=raw["request_parameters"]["dimensions"],
            encoding_format=str(raw["request_parameters"]["encoding_format"]),
            max_input_tokens_per_string=int(raw["batching"]["max_input_tokens_per_string"]),
            max_total_tokens_per_request=int(raw["batching"]["max_total_tokens_per_request"]),
            target_tokens_per_request=int(raw["batching"]["target_tokens_per_request"]),
            metric=str(raw["vector_store"]["metric"]),
            persist_directory=str(raw["vector_store"]["persist_directory"]),
        )


def embed_batch(client, texts: list[str], config: EmbeddingConfig) -> list[list[float]]:
    """Embed one batch of texts. Never sets the frozen 'dimensions' parameter."""
    kwargs = {"model": config.model_name, "input": texts, "encoding_format": config.encoding_format}
    if config.dimensions is not None:
        raise ValueError("frozen config forbids setting 'dimensions'")
    response = client.embeddings.create(**kwargs)
    return [embedding.data for embedding in response.data]


def embed_corpus(client, units, config: EmbeddingConfig) -> tuple[np.ndarray, dict]:
    """Embed all retrieval units in chunk_id_order using token-targeted batches.

    Returns (matrix, token_usage_summary). token_usage is read from the API
    response total_tokens so the sidecar records the true spend of the freeze.
    """
    texts = [unit.text for unit in units.units]
    batches: list[list[str]] = [[]]
    current_tokens = 0
    for text in texts:
        estimated = max(1, len(text) // 4)  # conservative estimate; real usage is recorded below
        if current_tokens + estimated > config.target_tokens_per_request:
            batches.append([])
            current_tokens = 0
        batches[-1].append(text)
        current_tokens += estimated
    if not batches[0]:
        # The tokeniser never yields an empty first batch for a non-empty corpus,
        # but remain defensive: never send an empty request.
        batches = [batches[1]] if batches else []

    vectors: list[np.ndarray] = []
    total_tokens = 0
    total_requests = 0
    for batch in batches:
        if not batch:
            continue
        response = client.embeddings.create(
            model=config.model_name,
            input=batch,
            encoding_format=config.encoding_format,
        )
        total_tokens += int(getattr(response, "usage", None).total_tokens if getattr(response, "usage", None) else 0)
        total_requests += 1
        for embedding in response.data:
            vector = np.asarray(embedding.embedding, dtype=np.float32)
            if vector.shape[0] != config.embedding_dimension:
                raise ValueError(
                    f"embedding returned {vector.shape[0]} dims, frozen config requires "
                    f"{config.embedding_dimension}"
                )
            if not np.all(np.isfinite(vector)):
                raise ValueError("embedding contains non-finite values")
            vectors.append(vector)

    if len(vectors) != len(units.units):
        raise ValueError(
            f"got {len(vectors)} embeddings for {len(units.units)} units"
        )

    matrix = np.vstack(vectors).astype(np.float32)
    usage = {"total_tokens": total_tokens, "requests": total_requests}
    return matrix, usage


def build_meta(config: EmbeddingConfig, units, commit: str, usage: dict, corpus_version: str, chunking_version: str, date: str) -> EmbeddingMeta:
    """Assemble the sidecar with the frozen fields and reproducibility block."""
    return EmbeddingMeta(
        model_name=config.model_name,
        model_snapshot=config.model_name,
        embedding_dimension=config.embedding_dimension,
        generated_date=date,
        corpus_version=corpus_version,
        chunking_version=chunking_version,
        chunk_id_order=units.chunk_id_order,
        matrix_creation_frozen_block={
            "model": config.model_name,
            "dimensions": config.embedding_dimension,
            "dimensions_override": "none",
            "encoding_format": config.encoding_format,
        },
        frozen_config_git_commit=commit,
        token_usage=usage,
    )


def api_key_available() -> bool:
    """True only when the OpenAI key is in the environment (never return it)."""
    return bool(os.environ.get("OPENAI_API_KEY"))


# The OpenAI key is read only at call time and is never logged, stored in the
# sidecar, the manifest, or any report. The check above is a boolean presence
# probe only; it must never leak the value.
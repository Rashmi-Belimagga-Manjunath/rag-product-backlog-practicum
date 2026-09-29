"""Generation call for the RAG treatment.

Wraps the OpenAI chat completion. The frozen config (rag_config.json) fixes the
model, temperature=0.0, top_p=null, max_tokens=800, n=1, seed=null. Those null
fields are deliberately NOT sent so we never add a hidden parameter; the runner
records whether the endpoint honoured anything.

The generation layer never knows the ground truth. It receives only the
numbered passages and must cite them in [DOCUMENT_ID#Cn] form.
"""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass

from src.rag.context import Context

RAG_CONFIG_PATH = "experiments/configs/rag_config.json"
RAG_PROMPT_PATH = "experiments/configs/rag_prompt.txt"
RAG_PROMPT_SHA256 = "7ab15349db7a7a5db04c3b1a5f6aa52505a4f7bbc3e7d1a37ea234b4ca553dc1"


@dataclass(frozen=True)
class RAGConfig:
    top_k: int
    model_name: str
    temperature: float
    top_p: object
    max_tokens: int
    n: int
    seed: object
    citation_pattern: str
    vector_store_name: str
    persist_directory: str

    @classmethod
    def load(cls, path: str = RAG_CONFIG_PATH) -> "RAGConfig":
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        generation = raw["generation"]
        vector_store = raw["vector_store"]
        return cls(
            top_k=int(raw["retrieval"]["top_k"]),
            model_name=str(generation["model_name"]),
            temperature=float(generation["temperature"]),
            top_p=generation["top_p"],
            max_tokens=int(generation["max_tokens"]),
            n=int(generation["n"]),
            seed=generation["seed"],
            citation_pattern=str(raw["citation_format"]["pattern"]),
            vector_store_name=str(vector_store["name"]),
            persist_directory=str(vector_store["persist_directory"]),
        )


def prompt_sha256() -> str:
    """Hash the frozen prompt; the sidecar and run logs record it each time."""
    with open(RAG_PROMPT_PATH, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def verify_frozen_prompt() -> None:
    """Raise if the prompt drifted from the frozen hash."""
    actual = prompt_sha256()
    if actual != RAG_PROMPT_SHA256:
        raise ValueError(
            f"rag_prompt.txt hash {actual} does not match frozen {RAG_PROMPT_SHA256}"
        )


@dataclass(frozen=True)
class GenerationResult:
    answer: str
    finish_reason: str
    model: str
    usage: dict
    latency_seconds: float


def generate(client, config: RAGConfig, context: Context) -> GenerationResult:
    """Call the model once for a context. Abstentions are the model's decision."""
    verify_frozen_prompt()
    import time

    start = time.monotonic()
    messages = context.to_messages()
    kwargs: dict = {
        "model": config.model_name,
        "messages": messages,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "n": config.n,
    }
    if config.seed is not None:
        kwargs["seed"] = config.seed  # frozen seed: null is not sent
    if config.top_p is not None:
        kwargs["top_p"] = config.top_p

    response = client.chat.completions.create(**kwargs)
    elapsed = time.monotonic() - start

    choice = response.choices[0]
    return GenerationResult(
        answer=str(choice.message.content or ""),
        finish_reason=str(choice.finish_reason),
        model=str(response.model),
        usage={
            "prompt_tokens": int(response.usage.prompt_tokens),
            "completion_tokens": int(response.usage.completion_tokens),
            "total_tokens": int(response.usage.total_tokens),
        },
        latency_seconds=elapsed,
    )
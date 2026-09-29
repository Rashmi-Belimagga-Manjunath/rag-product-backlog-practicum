"""Fake OpenAI client for unit tests.

Implements the tiny surface the harness actually uses: embeddings.create and
chat.completions.create. Vectors are deterministic (seeded by the input text) so
tests that consume them are reproducible and never touch the network.
"""

from __future__ import annotations

import hashlib


class _FakeEmbedding:
    def __init__(self, index: int, text: str, dimension: int = 3072):
        digest = hashlib.sha256(f"{index}:{text}".encode()).digest()
        vector = [((digest[i % len(digest)] / 255.0) - 0.5) for i in range(dimension)]
        self.embedding = vector


class _FakeEmbeddingsResource:
    def __init__(self, dimension: int = 3072):
        self.dimension = dimension

    def create(self, model, input, encoding_format="float", **kwargs):
        class Response:
            def __init__(self, embeddings, model):
                self.data = embeddings
                self.model = model
                self.usage = _Usage(len(input))

        if isinstance(input, str):
            input = [input]
        embeddings = [
            _FakeEmbedding(index, text, self.dimension)
            for index, text in enumerate(input)
        ]
        return Response(embeddings, model)


class _Usage:
    def __init__(self, n_inputs: int):
        self.prompt_tokens = n_inputs * 100
        self.completion_tokens = 0
        self.total_tokens = n_inputs * 100


class _FakeChoice:
    def __init__(self, content: str, finish_reason: str):
        self.message = _FakeMessage(content)
        self.finish_reason = finish_reason


class _FakeMessage:
    def __init__(self, content: str):
        self.content = content


class _FakeChatResponse:
    def __init__(self, content: str, model: str):
        self.choices = [_FakeChoice(content, "stop")]
        self.model = model
        self.usage = _Usage(1)


class _FakeChatResource:
    def __init__(self, respond_with: str, model: str = "gpt-4o-mini", record: list | None = None):
        self.respond_with = respond_with
        self.model = model
        self.record = record if record is not None else []

    def create(self, **kwargs):
        self.record.append(kwargs)
        return _FakeChatResponse(self.respond_with, self.model)


class _FakeChat:
    """client.chat.completions.create(...) mirror for openai.OpenAI."""

    def __init__(self, respond_with: str, model: str, record: list):
        self.completions = _FakeCompletions(respond_with, model, record)


class _FakeCompletions:
    def __init__(self, respond_with: str, model: str, record: list):
        delegate = _FakeChatResource(respond_with, model, record)
        self.create = delegate.create


class FakeClient:
    """Mimics openai.OpenAI enough for the harness's usage."""

    def __init__(self, respond_with: str = "Answer. [DOC-PRD-A-01-v2#C0]",
                 model: str = "gpt-4o-mini"):
        self.embeddings = _FakeEmbeddingsResource(dimension=3072)
        self.record: list = []
        self.chat = _FakeChat(respond_with, model, self.record)


def make_query_embedding(text: str, dimension: int = 3072) -> list:
    """Deterministic unit query vector (used by tests that fake embed_query)."""
    import math

    vector = _FakeEmbedding(0, text, dimension).embedding
    norm = math.sqrt(sum(v * v for v in vector))
    return [v / norm for v in vector]
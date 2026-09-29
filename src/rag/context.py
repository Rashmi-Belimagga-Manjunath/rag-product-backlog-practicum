"""RAG context assembly.

Builds the numbered-passage block the frozen rag_prompt.txt expects from the
top-k retrieved units, and packs the final message list for the chat call. It
never talks to the API; generation lives in src/rag/generator.py.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.retrieval.units import Passage, render_passages
from src.vectorstore.store import VectorHit


@dataclass(frozen=True)
class Context:
    """Everything the generation model receives for one question."""

    question: str
    passages: list[Passage]
    prompt_sha256: str

    def passage_block(self) -> str:
        rendered = [passage.render() for passage in self.passages]
        return "\n\n".join(rendered)

    def to_messages(self) -> list[dict[str, str]]:
        """System prompt is the frozen rag_prompt.txt; user message carries the passages."""
        with open("experiments/configs/rag_prompt.txt", "r", encoding="utf-8") as handle:
            system_text = handle.read()
        user_text = (
            "Retrieved passages:\n\n"
            + self.passage_block()
            + "\n\nQuestion: " + self.question
        )
        return [
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_text},
        ]


def build_context(question: str, hits: list[VectorHit], units, prompt_sha256: str) -> Context:
    """Turn retrieval hits into a context. hits must be in final ranked order."""
    ranked_units = [units.by_id[hit.chunk_id] for hit in hits]
    passages = render_passages(ranked_units)
    return Context(question=question, passages=passages, prompt_sha256=prompt_sha256)
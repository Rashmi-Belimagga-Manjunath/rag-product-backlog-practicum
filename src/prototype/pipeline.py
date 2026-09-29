"""Interactive demonstration pipeline (Layer 2).

This is a DEMONSTRATION interface, explicitly NOT a source of experimental
measurements. It calls the exact same frozen modules the experiment uses:

  * the same retrieval units (load_frozen_units),
  * the same BM25 implementation (src/bm25.retriever),
  * the same Chroma/RAG path (src/rag.generator with the frozen config),

but it takes a single user-supplied question and writes nothing to
experiments/runs, results/ or the 32-query benchmark. A demo query can never
contaminate ground-truth resolution or experimental evidence.

The pipeline deliberately does not evaluate: it retrieves with BM25 and RAG and
returns the answer plus both evidence lists and the citation validation. That
keeps interactive exploration separate from benchmark execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class PrototypeResult:
    question: str
    bm25_hits: list[dict]
    rag_context: list[dict]
    rag_answer: str
    rag_citations: list[str]
    fabricated_citations: list[str]
    model: str
    status: str
    error_message: str = ""
    evidence_log: list[str] = field(default_factory=list)


class DemoPipeline:
    """Thin reusable pipeline for the Streamlit front-end and unit tests.

    Either the vector store can be provided (a stored, frozen collection) or the
    demo falls back to BM25-only output. It never opens the raw 32-query
    benchmark.
    """

    def __init__(self, units=None, report=None, bm25_config=None, rag_config=None):
        from src.benchmark.validate_ground_truth import validate_ground_truth
        from src.bm25.retriever import BM25Config
        from src.data_generation.render_v1 import render_corpus
        from src.data_generation.v1_full import build_final_corpus
        from src.rag.generator import RAGConfig
        from src.retrieval.units import load_frozen_units

        self.units = units or load_frozen_units()
        self.model = build_final_corpus()
        self.documents = render_corpus(self.model)
        self.report = report or validate_ground_truth(
            model=self.model, documents=self.documents, against_final=True
        )
        self.bm25_config = bm25_config or BM25Config.load()
        self.rag_config = rag_config or RAGConfig.load()

    # ------------------------------------------------------------------ BM25
    def bm25_retrieve(self, question: str, top_k: int | None = None) -> list[dict]:
        from src.bm25.retriever import BM25Index

        index = BM25Index(units=self.units, config=self.bm25_config)
        result = index.query("demo", question)
        hits = result.hits if top_k is None else result.hits[:top_k]
        return [hit.as_dict() for hit in hits]

    def bm25_passages(self, hits: list[dict]) -> list[str]:
        """The user-facing top-5 retrieved passages for BM25 (Layer B)."""
        passages = []
        for index, hit in enumerate(hits, start=1):
            unit = self.units.by_id[hit["chunk_id"]]
            passages.append(
                "\n".join([
                    f"Passage {index}",
                    f"Passage ID: {unit.citation}",
                    f"Status: {unit.version_status}",
                    unit.text,
                ])
            )
        return passages

    # ------------------------------------------------------------------- RAG
    def rag_retrieve(self, question: str, embed_query, top_k: int | None = None) -> list[dict]:
        """Chroma retrieval (the same path used by the experiment)."""
        from src.vectorstore.store import VectorStore

        store = VectorStore(persist_directory=self.rag_config.persist_directory)
        query_embedding = embed_query(question)
        top_k = top_k or self.rag_config.top_k
        hits = store.search_topk(query_embedding, top_k, self.units)
        return [{"chunk_id": h.chunk_id, "rank": index + 1, "score": h.score,
                 "document_id": h.document_id} for index, h in enumerate(hits)]

    def answer(self, question: str, client, embed_query, top_k: int | None = None) -> PrototypeResult:
        try:
            bm25_hits = self.bm25_retrieve(question, top_k)
            rag_hits = self.rag_retrieve(question, embed_query, top_k)

            from src.rag.context import build_context
            from src.rag.citations import extract_citations, parse_all, supplied_citation_ids, validate
            from src.rag.generator import generate

            context = build_context(question, [self.units.by_id[h["chunk_id"]] for h in rag_hits],
                                    self.units, self.rag_config_prompt_sha())
            result = generate(client, self.rag_config, context)
            citations, unknown = parse_all(extract_citations(result.answer))
            supplied = supplied_citation_ids([h["chunk_id"] for h in rag_hits])
            citation_report = validate(citations, supplied)

            return PrototypeResult(
                question=question,
                bm25_hits=bm25_hits,
                rag_context=rag_hits,
                rag_answer=result.answer,
                rag_citations=[c.raw for c in citation_report.supplied_cited],
                fabricated_citations=[c.raw for c in citation_report.fabricated],
                model=result.model,
                status="ok",
                evidence_log=[
                    "RAG answer generated with the frozen prompt and frozen config",
                ],
            )
        except Exception as error:
            return PrototypeResult(
                question=question,
                bm25_hits=[],
                rag_context=[],
                rag_answer="",
                rag_citations=[],
                fabricated_citations=[],
                model="",
                status="error",
                error_message=f"{type(error).__name__}: {error}",
            )

    @staticmethod
    def rag_config_prompt_sha() -> str:
        from src.rag.generator import prompt_sha256
        return prompt_sha256()
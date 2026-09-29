"""In-repo standard BM25 retriever.

Decision D-004/D-005 (DECISIONS.md): BM25 is implemented in-repo over the frozen
index of retrieval units rather than importing an external BM25 package. k1, b,
the Lucene non-negative IDF and the tokeniser are all read from the frozen
experiments/configs/bm25_config.json so the harness can never drift from the
approved formula. The retriever is pure Python + stdlib (numpy only for
statistics) and fully deterministic: ties break on ascending chunk id, matching
the frozen tie_breaking rule.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

from src.retrieval.units import RetrievalUnit, RetrievalUnitSet, tokens

BM25_CONFIG_PATH = "experiments/configs/bm25_config.json"


@dataclass(frozen=True)
class BM25Config:
    k1: float
    b: float
    idf: str
    idf_formula: str
    tf_formula: str
    top_k: int
    tie_breaking: str
    lowercase: bool
    tokenisation: str
    stemming: bool
    stopword_removal: bool
    verbatim_queries: bool
    logged_per_query: tuple[str, ...]

    @classmethod
    def load(cls, path: str = BM25_CONFIG_PATH) -> "BM25Config":
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        scoring = raw["scoring"]
        text_handling = raw["text_handling"]
        query_handling = raw["query_handling"]
        output = raw["output"]
        return cls(
            k1=float(scoring["k1"]),
            b=float(scoring["b"]),
            idf=str(scoring["idf"]),
            idf_formula=str(scoring["idf_formula"]),
            tf_formula=str(scoring["tf_formula"]),
            top_k=int(output["top_k"]),
            tie_breaking=str(output["tie_breaking"]),
            lowercase=bool(text_handling["lowercase"]),
            tokenisation=str(text_handling["tokenisation"]),
            stemming=bool(text_handling["stemming"]),
            stopword_removal=bool(text_handling["stopword_removal"]),
            verbatim_queries=bool(query_handling["verbatim"]),
            logged_per_query=tuple(output["logged_per_query"]),
        )


@dataclass(frozen=True)
class BM25Hit:
    """One retrieved row, exactly the fields the frozen config logs per query."""

    chunk_id: str
    rank: int
    score: float
    document_id: str

    def as_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "rank": self.rank,
            "score": self.score,
            "document_id": self.document_id,
        }


@dataclass(frozen=True)
class BM25Result:
    query_id: str
    query_text: str
    hits: list[BM25Hit]

    def chunk_ids(self) -> list[str]:
        return [hit.chunk_id for hit in self.hits]


class BM25Index:
    """A frozen, immutable BM25 index over the retrieval units.

    Scored with the standard BM25 formula exactly as frozen:
      idf = ln(1 + (N - df + 0.5) / (df + 0.5))   (Lucene, non-negative)
      tf  = f * (k1 + 1) / (f + k1 * (1 - b + b * |D| / avgdl))
      score = sum over query terms of idf * tf

    The tokeniser lowercases and splits on unicode word characters with embedded
    apostrophes ([\\w']+); there is deliberately no stemming and no stopword
    removal, per bm25_config.json.
    """

    def __init__(self, units: RetrievalUnitSet, config: BM25Config):
        if config.idf != "lucene":
            raise ValueError(f"only the frozen lucene idf is supported, got {config.idf!r}")
        self.units = units
        self.config = config
        self._build()

    def _build(self) -> None:
        self.unit_tokens: list[list[str]] = []
        self.document_lengths: list[int] = []
        total_length = 0
        for unit in self.units.units:
            unit_tokens = tokens(unit.text)
            self.unit_tokens.append(unit_tokens)
            length = len(unit_tokens)
            self.document_lengths.append(length)
            total_length += length

        self.corpus_size = len(self.units.units)
        self.average_document_length = total_length / self.corpus_size if self.corpus_size else 0.0

        # Term -> set of unit positions containing it (the postings lists).
        self.postings: dict[str, list[int]] = {}
        for position, unit_tokens in enumerate(self.unit_tokens):
            for term in set(unit_tokens):
                self.postings.setdefault(term, []).append(position)

        self.term_idf: dict[str, float] = {
            term: math.log(
                1.0 + (self.corpus_size - len(postings) + 0.5) / (len(postings) + 0.5)
            )
            for term, postings in self.postings.items()
        }

    def score_document(self, position: int, query_terms: list[str]) -> float:
        """BM25 score of one unit against a tokenised query."""
        unit_tokens = self.unit_tokens[position]
        term_frequencies: dict[str, int] = {}
        for term in unit_tokens:
            term_frequencies[term] = term_frequencies.get(term, 0) + 1
        length = self.document_lengths[position]
        score = 0.0
        for term in query_terms:
            idf = self.term_idf.get(term)
            if idf is None:
                continue
            f = term_frequencies.get(term, 0)
            if f == 0:
                continue
            tf = (f * (self.config.k1 + 1.0)) / (
                f + self.config.k1 * (1.0 - self.config.b + self.config.b * length / self.average_document_length)
            )
            score += idf * tf
        return score

    def search(self, query_text: str, top_k: int | None = None) -> list[tuple[int, float]]:
        """Return [(unit_position, score)] ranked by score descending.

        Ties on equal score break on ascending chunk id. Sorting by (score desc,
        chunk id asc) in one pass makes the whole ranking deterministic and
        content-independent, exactly as frozen.
        """
        top_k = self.config.top_k if top_k is None else top_k
        query_terms = tokens(query_text) if self.config.verbatim_queries else tokens(query_text)
        if not query_terms:
            return []
        scored: list[tuple[float, int, str]] = []
        for position in range(self.corpus_size):
            score = self.score_document(position, query_terms)
            if score > 0.0:
                scored.append((score, position, self.units.units[position].chunk_id))
        scored.sort(key=lambda entry: (-entry[0], entry[2]))
        return [(position, score) for score, position, _ in scored[:top_k]]

    def query(self, query_id: str, query_text: str) -> BM25Result:
        hits: list[BM25Hit] = []
        for rank, (position, score) in enumerate(self.search(query_text), start=1):
            unit = self.units.units[position]
            hits.append(
                BM25Hit(
                    chunk_id=unit.chunk_id,
                    rank=rank,
                    score=score,
                    document_id=unit.document_id,
                )
            )
        return BM25Result(query_id=query_id, query_text=query_text, hits=hits)
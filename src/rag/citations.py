"""Citation parsing and validation for the RAG treatment.

The frozen citation format is [DOCUMENT_ID#Cn]. Validation is machine-checkable
(rag_config.json citation_format.machine_checkable) and distinguishes:

  * fabricated citation — the cited id was never supplied to the model;
  * retrieved-but-unsupporting (mis-citation) — cited a supplied chunk but the
    claim's supporting content is not what the citation points to;
  * valid citation — points at a supplied chunk.

We can only automate the first and third categories here (the second needs the
retrieval log and the gold relevance set, supplied by the runner). This module
stays free of any ground-truth knowledge: it only knows which citations the
model produced and which ids were supplied.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.retrieval.units import parse_citation

# [DOC-PRD-A-01-v2#C0]
CITATION_RE = re.compile(r"\[([^\]]+)\]")


@dataclass(frozen=True)
class Citation:
    raw: str               # exactly what appeared in brackets
    document_id: str
    chunk_index: int


@dataclass(frozen=True)
class CitationReport:
    citations: list[Citation]
    fabricated: list[Citation]                 # never supplied
    supplied_cited: list[Citation]             # supplied identifiers cited
    unknown_raw: list[str]                     # bracketed text that failed to parse


def extract_citations(answer: str) -> list[str]:
    """All bracketed tokens in the answer, in order."""
    return CITATION_RE.findall(answer)


def parse_all(citation_texts: list[str]) -> tuple[list[Citation], list[str]]:
    """Parse tokens; non-parseable tokens go to unknown_raw."""
    citations: list[Citation] = []
    unknown: list[str] = []
    for text in citation_texts:
        try:
            document_id, chunk_index = parse_citation(text.strip())
            citations.append(Citation(raw=text.strip(), document_id=document_id, chunk_index=chunk_index))
        except ValueError:
            unknown.append(text.strip())
    return citations, unknown


def validate(citations: list[Citation], supplied_citation_ids: set[str]) -> CitationReport:
    """Split parsed citations into fabricated vs supplied.

    supplied_citation_ids is the set of citation strings the model actually
    received (the passage ids of the top-k). Anything cited that is not in that
    set is, by definition, never-supplied and therefore fabricated.
    """
    fabricated: list[Citation] = []
    supplied_cited: list[Citation] = []
    for citation in citations:
        key = f"{citation.document_id}#C{citation.chunk_index}"
        (supplied_cited if key in supplied_citation_ids else fabricated).append(citation)
    unknown_raw: list[str] = []
    return CitationReport(
        citations=citations,
        fabricated=fabricated,
        supplied_cited=supplied_cited,
        unknown_raw=unknown_raw,
    )


def supplied_citation_ids(supplied_chunk_ids: list[str]) -> set[str]:
    """Convert chunk ids (e.g. DOC-PRD-A-01-v2-C0) into citation ids."""
    result = set()
    for chunk_id in supplied_chunk_ids:
        document_id, chunk_index = parse_citation(chunk_id.replace("-C", "#C"))
        result.add(f"{document_id}#C{chunk_index}")
    return result
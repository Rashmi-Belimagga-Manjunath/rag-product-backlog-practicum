"""Shared access to the frozen retrieval units.

Every retrieval system (BM25 and RAG) ranks the exact same objects: the 272
chunks recorded in data/corpus/v1/chunks/chunks.json. Loading them from that
single file (rather than re-chunking documents) is the guarantee that both
systems retrieve the same units, in the same order, with the same provenances.

These helpers are deliberately small and dependency-free so they can be reused by
the BM25, embedding, vector-store and ground-truth modules without circular
imports.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

FROZEN_CHUNKS_PATH = "data/corpus/v1/chunks/chunks.json"

# A frozen chunk id ends in "-C<index>", e.g. "DOC-PRD-A-01-v2-C0".
# The document id is everything before that final "-C<index>".
_CHUNK_ID_RE = re.compile(r"^(?P<document_id>.+)-C(?P<index>\d+)$")


@dataclass(frozen=True)
class RetrievalUnit:
    """A single, immutable retrieval unit (one frozen chunk)."""

    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    heading_path: list[str] = field(default_factory=list)
    word_count: int = 0
    source_entity_id: str = ""
    product_id: str = ""
    doc_type: str = ""
    version: str = ""
    version_status: str = ""
    is_current: bool = True
    supersedes: list[str] = field(default_factory=list)
    superseded_by: str = ""
    document_date: str = ""
    entity_ids: list[str] = field(default_factory=list)

    def entity_cover(self) -> set[str]:
        """All entities this unit is provably about (subject + referenced).

        Used for dependency evidence and ground-truth provenance checks. The
        subject entity is the source_entity_id; referenced entities are those
        the document links to.
        """
        return {self.source_entity_id, *self.entity_ids} - {""}

    @property
    def citation(self) -> str:
        """The presentation citation for this unit: DOCUMENT_ID#Cn.

        Converts the frozen chunk id "DOC-PRD-A-01-v2-C0" into
        "DOC-PRD-A-01-v2#C0", which is the exact form the frozen prompt tells
        the model to copy from the "Passage ID" line.
        """
        return f"{self.document_id}#C{self.chunk_index}"


@dataclass(frozen=True)
class RetrievalUnitSet:
    """The frozen chunk set with the derived lookups every system needs."""

    units: list[RetrievalUnit]
    by_id: dict[str, RetrievalUnit]
    by_document: dict[str, list[RetrievalUnit]]

    @property
    def chunk_id_order(self) -> list[str]:
        return [unit.chunk_id for unit in self.units]

    @property
    def documents(self) -> list[str]:
        return list(self.by_document.keys())

    def relevant_chunk_ids(self, document_ids: list[str]) -> list[str]:
        """Chunk ids (in frozen order) whose document is in document_ids."""
        ids: list[str] = []
        for unit in self.units:
            if unit.document_id in document_ids:
                ids.append(unit.chunk_id)
        return ids


def _split_chunk_id(chunk_id: str) -> tuple[str, int]:
    match = _CHUNK_ID_RE.match(chunk_id)
    if not match:
        raise ValueError(f"chunk_id {chunk_id!r} does not end in -C<index>")
    return match.group("document_id"), int(match.group("index"))


def parse_citation(citation: str) -> tuple[str, int]:
    """Parse "DOC-PRD-A-01-v2#C0" into (document_id, chunk_index).

    Used to validate model citations against the retrieval log. Raises
    ValueError on anything that cannot be a frozen-prompt citation.
    """
    if "#C" not in citation:
        raise ValueError(f"citation {citation!r} has no '#C' separator")
    document_id, _, index = citation.partition("#C")
    if not document_id or not index.isdigit():
        raise ValueError(f"citation {citation!r} is not of form DOCUMENT_ID#Cn")
    return document_id, int(index)


def load_frozen_units(path: str = FROZEN_CHUNKS_PATH) -> RetrievalUnitSet:
    """Load the frozen chunk JSON in on-disk (chunk_id_order) order.

    The JSON record keys are a superset of the retrieval fields. Only the
    fields the systems care about are hydrated; unknown keys are ignored so the
    loader does not need to track future additions to the frozen artefacts.
    """
    with open(path, "r", encoding="utf-8") as handle:
        records = json.load(handle)

    units: list[RetrievalUnit] = []
    for record in records:
        units.append(
            RetrievalUnit(
                chunk_id=record["chunk_id"],
                document_id=record["document_id"],
                chunk_index=record.get("chunk_index", 0),
                text=record["text"],
                heading_path=list(record.get("heading_path") or []),
                word_count=int(record.get("word_count", 0)),
                source_entity_id=record.get("source_entity_id", ""),
                product_id=record.get("product_id", ""),
                doc_type=record.get("doc_type", ""),
                version=str(record.get("version", "")),
                version_status=record.get("version_status", "current"),
                is_current=bool(record.get("is_current", True)),
                supersedes=list(record.get("supersedes") or []),
                superseded_by=record.get("superseded_by", ""),
                document_date=record.get("document_date", ""),
                entity_ids=list(record.get("entity_ids") or []),
            )
        )

    by_id: dict[str, RetrievalUnit] = {}
    by_document: dict[str, list[RetrievalUnit]] = {}
    for unit in units:
        by_id[unit.chunk_id] = unit
        by_document.setdefault(unit.document_id, []).append(unit)

    return RetrievalUnitSet(units=units, by_id=by_id, by_document=by_document)


@dataclass(frozen=True)
class Passage:
    """A passage handed to the generation model, built from a retrieval unit."""

    number: int
    retrieval_unit: RetrievalUnit

    def render(self) -> str:
        unit = self.retrieval_unit
        status = unit.version_status
        if unit.version_status == "superseded" and unit.superseded_by:
            status = f"superseded (replaced by {unit.superseded_by})"
        lines = [
            f"Passage {self.number}",
            f"Passage ID: {unit.citation}",
            f"Status: {status}",
            unit.text,
        ]
        return "\n".join(lines)


def render_passages(units: list[RetrievalUnit]) -> list[Passage]:
    """Wrap ranked units as the numbered passages the frozen prompt expects."""
    return [Passage(number=index + 1, retrieval_unit=unit) for index, unit in enumerate(units)]


def tokens(text: str) -> list[str]:
    """The single frozen tokeniser used by BM25 difficulty and BM25 retrieval.

    Frozen: unicode word tokens matching [\\w']+, lowercased, no stemming and
    no stopword removal (bm25_config.json text_handling). Keeping one shared
    function means the retriever and any token-count estimator cannot drift.
    """
    return re.findall(r"[\w']+", text.lower())
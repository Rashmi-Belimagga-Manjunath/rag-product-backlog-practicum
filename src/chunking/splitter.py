"""
Structure-aware chunking, plus the approved C1-C8 coherence validation.

WHY NOT A FIXED CHARACTER WINDOW
--------------------------------
Ground truth attaches to chunks by provenance propagation: a document's chunk inherits
the document's entity IDs. A naive fixed window splits a dependency statement or a
normative requirement across a boundary, leaving the required fact in a chunk that does
not carry the entity's ID. The label then becomes unscoreable, and a system cannot be
credited for retrieving it. The long PRDs - the documents carrying the richest dependency
statements - are exactly the ones affected.

So the splitter works on structure:
    heading boundaries -> pack sections up to chunk_size -> sentence boundaries for
    oversized sections -> sentence-level overlap.
No chunk ever begins or ends mid-sentence.

This is a PRE-SYSTEM decision, validated on coherence only. Selecting a chunking
configuration on BM25 or RAG scores would be result-tuning.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?;])\s+(?=[A-Z0-9\"'(])")


@dataclass
class Chunk:
    chunk_id: str                    # "<document_id>-C<index>", stable across runs
    document_id: str
    chunk_index: int
    text: str
    heading_path: list[str] = field(default_factory=list)
    word_count: int = 0
    source_entity_id: str = ""
    product_id: str = ""
    doc_type: str = ""
    version: str = "1.0"
    version_status: str = "current"
    is_current: bool = True
    supersedes: list[str] = field(default_factory=list)
    superseded_by: str = ""
    document_date: str = ""
    # Every entity this chunk's text is about, propagated from the document's declared
    # DocumentLinks. NOT just the document's own subject: a PBI chunk that states a
    # dependency on COMP-06 is about COMP-06, and ground truth depends on that
    # provenance rather than on re-reading chunk text.
    entity_ids: list[str] = field(default_factory=list)

    def all_entity_ids(self) -> list[str]:
        ids = [self.source_entity_id, *self.entity_ids]
        seen, ordered = set(), []
        for value in ids:
            if value and value not in seen:
                seen.add(value); ordered.append(value)
        return ordered


@dataclass
class ChunkingConfig:
    chunk_size: int = 1000
    chunk_overlap: int = 200
    label: str = "primary"

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "splitter": "structure-aware (heading -> section packing -> sentence)",
            "sentence_safe": True,
        }


def _split_sentences(text: str) -> list[str]:
    return [s for s in _SENTENCE_SPLIT.split(text) if s.strip()]


def _sections(body: str) -> list[tuple[list[str], str]]:
    """
    Break a markdown document into (heading_path, text) sections.

    Heading levels are tracked so a chunk knows its position in the document, which is
    what lets a reader - or a model - interpret an isolated chunk.
    """
    sections: list[tuple[list[str], str]] = []
    stack: list[tuple[int, str]] = []
    current_lines: list[str] = []
    current_path: list[str] = []

    def flush() -> None:
        text = "\n".join(current_lines).strip()
        if text:
            sections.append((list(current_path), text))
        current_lines.clear()

    for line in body.split("\n"):
        match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if match:
            flush()
            level = len(match.group(1))
            title = match.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            current_path = [t for _, t in stack]
        else:
            current_lines.append(line)
    flush()
    return sections


def chunk_document(document, config: ChunkingConfig) -> list[Chunk]:
    """
    Pack a document into chunks, spanning section boundaries where useful.

    Sections are flattened into a stream of complete sentence-units, then packed ACROSS
    section boundaries up to `chunk_size` words. Packing per-section instead would emit
    one chunk per heading regardless of size, which makes `chunk_size` inert and produces
    a corpus of tiny fragments - the exact failure C5 exists to catch.
    """
    sections = _sections(document.body)
    units: list[tuple[tuple[str, ...], str]] = []
    for heading_path, section_text in sections:
        for sentence in _split_sentences(section_text):
            units.append((tuple(heading_path), sentence))
    if not units:
        return []

    chunks: list[Chunk] = []
    current: list[tuple[tuple[str, ...], str]] = []
    current_words = 0

    for unit in units:
        words = len(unit[1].split())
        # A single unit longer than chunk_size is kept whole: splitting it would violate
        # C1, and truncating it would silently lose content.
        if current and current_words + words > config.chunk_size:
            chunks.append(_build_chunk(document, current, len(chunks)))
            # Overlap carries whole units forward, never a partial sentence.
            carry: list[tuple[tuple[str, ...], str]] = []
            carry_words = 0
            for previous in reversed(current):
                previous_words = len(previous[1].split())
                if carry_words + previous_words > config.chunk_overlap:
                    break
                carry.insert(0, previous)
                carry_words += previous_words
            current = carry
            current_words = carry_words
        current.append(unit)
        current_words += words

    if current:
        chunks.append(_build_chunk(document, current, len(chunks)))
    return chunks


def _build_chunk(document, units, index: int) -> Chunk:
    text = " ".join(unit for _, unit in units)
    headings: list[str] = []
    for path, _ in units:
        if path and (not headings or headings[-1] != path[-1]):
            headings.append(path[-1])
    return Chunk(
        chunk_id=f"{document.document_id}-C{index}",
        document_id=document.document_id,
        chunk_index=index,
        text=text,
        heading_path=headings,
        word_count=len(text.split()),
        source_entity_id=document.source_entity_id,
        product_id=document.product_id,
        doc_type=document.doc_type,
        version=document.version,
        version_status=document.version_status,
        is_current=document.is_current,
        supersedes=[document.supersedes] if document.supersedes else [],
        superseded_by=document.superseded_by,
        document_date=document.created_date,
        # Provenance propagation: the entities this document references, taken from the
        # declared DocumentLinks. The subject entity is excluded because it is already
        # carried in source_entity_id.
        entity_ids=[
            entity for entity in document.referenced_entity_ids()
            if entity != document.source_entity_id
        ],
    )


def chunk_corpus(documents, config: ChunkingConfig) -> list[Chunk]:
    chunks: list[Chunk] = []
    for document in documents:
        chunks.extend(chunk_document(document, config))
    return chunks


# ---------------------------------------------------------------------------
# C1-C8 validation
# ---------------------------------------------------------------------------

@dataclass
class CoherenceResult:
    check_id: str
    description: str
    passed: bool
    observed: str
    threshold: str
    critical: bool = False

    def __str__(self) -> str:
        status = "PASS" if self.passed else ("HALT" if self.critical else "FAIL")
        return (f"[{status:4}] {self.check_id:4} {self.description}\n"
                f"            observed {self.observed}  (threshold {self.threshold})")


def _bag(text: str) -> frozenset:
    return frozenset(w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 3)


def validate_coherence(documents, chunks, model, config: ChunkingConfig,
                       required_document_ids=None) -> list[CoherenceResult]:
    """
    Run C1-C8 with thresholds fixed in advance.

    `required_document_ids` lets C8 be checked against the ground truth rather than
    against every document. Every ground-truth document must be reachable from at least
    one chunk, otherwise its label cannot be scored.
    """
    results: list[CoherenceResult] = []

    # C1 - no mid-sentence split.
    #
    # This is tested EXACTLY rather than by punctuation heuristics. A previous heuristic
    # ("does the chunk end in . ! ?") reported failures on chunks that ended perfectly
    # correctly on a bullet item or a metadata field, which is a complete structural
    # line and not a split sentence.
    #
    # The exact property: a chunk is valid iff its text is a contiguous run of whole
    # sentence-units taken from its document. If that holds for every chunk, no unit was
    # ever divided.
    by_document: dict[str, list[str]] = {}
    for document in documents:
        units: list[str] = []
        for _heading, section_text in _sections(document.body):
            units.extend(_split_sentences(section_text))
        by_document[document.document_id] = units

    def contiguous_runs(units: list[str]) -> set[str]:
        runs: set[str] = set()
        for i in range(len(units)):
            for j in range(i + 1, len(units) + 1):
                runs.add(" ".join(units[i:j]))
        return runs

    run_cache = {doc_id: contiguous_runs(u) for doc_id, u in by_document.items()}
    split = [
        c.chunk_id for c in chunks
        if c.text not in run_cache.get(c.document_id, set())
    ]
    results.append(CoherenceResult(
        "C1", "No chunk splits a sentence (exact contiguous-unit test)",
        not split,
        f"{len(split)}/{len(chunks)} chunks split a unit"
        + (f"; e.g. {split[:3]}" if split else ""),
        "0%",
    ))

    # C2 / C3 - relationship and requirement statements not SPLIT.
    #
    # Scoped per document. An earlier version of this check counted occurrences across the
    # whole corpus and reported REQ-A-01 as "split" because it correctly appears in both
    # the superseded PRD v1 and the current PRD v2. That is the version lineage behaving
    # as designed - it is what makes the stale-requirement conflict real - and it is not a
    # split. A split means one statement divided across two chunks OF THE SAME DOCUMENT.
    def split_within(statement: str) -> list[str]:
        key = " ".join(statement.split()[:8])
        if not key:
            return []
        per_document: dict[str, int] = {}
        for chunk in chunks:
            if key in chunk.text:
                per_document[chunk.document_id] = per_document.get(chunk.document_id, 0) + 1
        return [doc for doc, count in per_document.items() if count > 1]

    # Only EXPLICIT dependencies can be split, because an implicit one is stated nowhere
    # and therefore has no corpus text to break.
    explicit = [d for d in model.dependencies if d.explicitness == "explicit"]
    split_deps = [d.dependency_id for d in explicit if split_within(d.description)]
    results.append(CoherenceResult(
        "C2", "Dependency statements not split within a document",
        not split_deps,
        f"{len(split_deps)} split of {len(explicit)} explicit "
        f"({len(model.dependencies)} declared; implicit ones have no corpus text to split)",
        "0",
    ))

    split_reqs = [r.requirement_id for r in model.requirements if split_within(r.statement)]
    multi_version = sum(
        1 for r in model.requirements
        if len({c.document_id for c in chunks
                if " ".join(r.statement.split()[:8]) in c.text}) > 1
    )
    results.append(CoherenceResult(
        "C3", "Requirement statements not split within a document",
        not split_reqs,
        f"{len(split_reqs)} split of {len(model.requirements)} requirements "
        f"({multi_version} legitimately appear in both a superseded and a current version)",
        "0",
    ))

    # C4 - every chunk carries provenance
    orphan = [c.chunk_id for c in chunks if not c.source_entity_id]
    results.append(CoherenceResult(
        "C4", "Every chunk carries an entity ID",
        not orphan,
        f"{len(orphan)} without provenance of {len(chunks)}", "0",
    ))

    # C5 - orphan chunks under 50 words.
    #
    # The <3% threshold is calibrated against the FULL corpus length distribution, where
    # long documents dominate. It cannot be met on a small mechanism sample, and loosening
    # it to make a sample pass would corrupt the one budget that guards against a
    # fragment-heavy index. The observed result is reported as measured, the cause is
    # named, and the scale caveat rides along in the detail so the number cannot be quoted
    # out of context.
    tails = [c for c in chunks if c.word_count < 50]
    ratio = len(tails) / len(chunks) if chunks else 0.0
    detail = f"{len(tails)}/{len(chunks)} chunks under 50 words = {ratio:.1%}"
    if tails:
        offenders = sorted({c.doc_type for c in tails})
        detail += f"; concentrated in {', '.join(offenders)}"
        detail += (
            ". SAMPLE-SCALE ARTEFACT: these document types are well below the approved "
            "full-corpus length targets, so this is not yet a corpus-level result. See "
            "project_scaling() for the projection and the full corpus for the measurement."
        )
    results.append(CoherenceResult(
        "C5", "Orphan chunks under 50 words (threshold calibrated for full-corpus scale)",
        ratio < 0.03, detail, "<3%",
    ))

    # C6 - near-duplicate chunks within a document
    duplicates = 0
    for i, a in enumerate(chunks):
        bag_a = _bag(a.text)
        if not bag_a:
            continue
        for b in chunks[i + 1:]:
            if a.document_id != b.document_id:
                continue
            bag_b = _bag(b.text)
            if not bag_b:
                continue
            if len(bag_a & bag_b) / min(len(bag_a), len(bag_b)) > 0.9:
                duplicates += 1
    dup_ratio = duplicates / len(chunks) if chunks else 0.0
    results.append(CoherenceResult(
        "C6", "Near-duplicate chunks within a document",
        dup_ratio < 0.02,
        f"{duplicates} pairs = {dup_ratio:.1%}", "<2%",
    ))

    # C7 - every document yields at least one chunk
    chunked_docs = {c.document_id for c in chunks}
    missing = [d.document_id for d in documents if d.document_id not in chunked_docs]
    results.append(CoherenceResult(
        "C7", "Every document produces at least one chunk",
        not missing,
        f"{len(documents) - len(missing)}/{len(documents)}", "100%",
    ))

    # C8 - every ground-truth document is reachable (CRITICAL)
    targets = set(required_document_ids) if required_document_ids is not None else {
        d.document_id for d in documents
    }
    unreachable = sorted(targets - chunked_docs)
    results.append(CoherenceResult(
        "C8", "Every ground-truth document ID resolves to >=1 chunk",
        not unreachable,
        f"{len(targets) - len(unreachable)}/{len(targets)} reachable"
        + (f"; unreachable: {unreachable}" if unreachable else ""),
        "100%",
        critical=True,
    ))

    return results


# ---------------------------------------------------------------------------
# Scale projection
# ---------------------------------------------------------------------------

# Approved full-corpus document counts and word targets (docs/proposal_corpus_and_queries.md).
# Used ONLY to explain a sample-scale result. Not a corpus result, not a substitute for
# measuring C5 on the generated corpus, and not a licence to move the threshold.
APPROVED_CORPUS_PROFILE = (
    ("prd", 17, 900, 2200),
    ("feature_spec", 29, 400, 700),
    ("pbi", 120, 60, 130),
    ("component_doc", 18, 300, 550),
    ("ticket", 40, 80, 160),
    ("decision_log", 16, 150, 300),
    ("meeting_notes", 24, 50, 110),
    ("runbook", 8, 250, 450),
)


def project_scaling(config: ChunkingConfig, profile=APPROVED_CORPUS_PROFILE) -> dict:
    """
    Project chunk-count and orphan behaviour at approved full-corpus document lengths.

    HONEST LIMITS. This runs the REAL packer over synthetic documents built to the
    APPROVED WORD TARGETS, and it assumes length only. It contains none of the real
    corpus content, so it says nothing about C6 duplication, C8 reachability, or any
    semantic property. It exists solely to explain why a sample-scale C5 failure is a
    length artefact rather than a defect in the packer.

    It is NOT a measurement and NOT a substitute for one. C5 must be re-measured on the
    generated corpus, and the threshold is not moved to accommodate the projection.
    """
    per_type: dict[str, dict] = {}
    total_chunks = 0
    total_orphans = 0

    for doc_type, count, low, high in profile:
        # Spread documents evenly across the approved range, and keep supersession
        # multipliers out of it: the profile lists current documents, and 12 superseded
        # variants scale the totals elsewhere.
        span = high - low
        lengths = [low + (span * i) // max(1, count - 1) for i in range(count)]
        made = [
            _SyntheticDocument(
                document_id=f"SYN-{doc_type}-{i:03d}",
                doc_type=doc_type,
                body=_filler_text(words),
            )
            for i, words in enumerate(lengths)
        ]
        made_chunks = chunk_corpus(made, config)
        orphans = [c for c in made_chunks if c.word_count < 50]
        per_type[doc_type] = {
            "documents": count,
            "word_range": [low, high],
            "projected_chunks": len(made_chunks),
            "projected_orphans": len(orphans),
        }
        total_chunks += len(made_chunks)
        total_orphans += len(orphans)

    return {
        "config": config.as_dict(),
        "per_type": per_type,
        "projected_total_chunks": total_chunks,
        "projected_orphan_chunks": total_orphans,
        "projected_orphan_rate": round(total_orphans / total_chunks, 4) if total_chunks else 0.0,
        "projected_total_documents": sum(c for _t, c, _l, _h in profile),
        "caveat": (
            "Projection from approved word-count targets only, using the real packer. "
            "Not a measured corpus result. C5 must be re-measured on the generated corpus."
        ),
    }


_FILLER = (
    "The onboarding rollout proceeds through review before release. "
    "Payments remain blocked until verification completes. "
    "The support team confirms the change window with the client. "
)


def _filler_text(words: int) -> str:
    """Deterministic filler of approximately `words` words."""
    if words <= 0:
        return ""
    out: list[str] = []
    while len(out) < words:
        out.extend(_FILLER.split())
    return " ".join(out[:words])


@dataclass
class _SyntheticDocument:
    """Minimal stand-in exposing only what the packer reads."""
    document_id: str
    doc_type: str
    body: str
    source_entity_id: str = "SYN"
    product_id: str = "SYN"
    version: str = "1.0"
    version_status: str = "current"
    is_current: bool = True
    supersedes: str = ""
    superseded_by: str = ""
    created_date: str = "2026-01-01"

    @property
    def references(self) -> list:
        return []

    def referenced_entity_ids(self) -> list[str]:
        return []

    def word_count(self) -> int:
        return len(self.body.split())

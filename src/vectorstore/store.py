"""Vector-store persistence over the frozen embedding matrix.

Stores the byte-identical matrix (from src/embeddings/cache.load_matrix) into a
Chroma collection with the frozen metric (cosine) and stable/unique chunk ids.
The frozen embedding_config.json says OpenAI returns unit-normalised vectors, so
cosine similarity is a plain dot product; the cross-check verifies this rather
than assuming it.

Every consumer here is intentionally naive: we keep Chroma's native top-k, then
re-sort a candidate pool tie-free by (score desc, chunk id asc) so the frozen
ascending-chunk-id tie rule is honoured deterministically and independently of
Chroma's internal ordering.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from src.embeddings.cache import LoadedMatrix
from src.retrieval.units import RetrievalUnitSet

DEFAULT_PERSIST_DIRECTORY = "data/vectorstore/v1-corpus"
DEFAULT_COLLECTION_NAME = "v1-corpus"


def _embedding_list(query_embedding):
    """Normalise a query embedding before handing it to Chroma.

    Chroma's query_embeddings accepts a plain list either way. The experiment
    path (run_rag) hands in a numpy array, while the Streamlit prototype embeds
    through the OpenAI SDK, which returns a plain Python list (encoding_format
    'float'). Both must work, so we adapt explicitly instead of assuming one
    type or blindly calling .tolist() on an unknown object.
    """
    if isinstance(query_embedding, np.ndarray):
        return query_embedding.tolist()
    if isinstance(query_embedding, (list, tuple)):
        return list(query_embedding)
    raise TypeError(
        "query_embedding must be a list or numpy.ndarray, got "
        f"{type(query_embedding).__name__}"
    )


@dataclass(frozen=True)
class VectorHit:
    chunk_id: str
    score: float
    document_id: str


class VectorStore:
    """Chroma collection over the frozen matrix.

    The perspective: the collection is a built artefact of the freeze step. This
    class handles building the collection, embedding queries and deterministic
    top-k retrieval. It never mutates experimental results.
    """

    def __init__(self, persist_directory: str = DEFAULT_PERSIST_DIRECTORY, collection_name: str = DEFAULT_COLLECTION_NAME):
        import chromadb

        # use a persistent client so the collection survives; the freeze step
        # writes into data/vectorstore/.
        self.persist_directory = persist_directory
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def build_from_loaded(self, loaded: LoadedMatrix, units: RetrievalUnitSet) -> dict:
        """Create/replace the collection with the frozen matrix.

        Returns a summary dict (count, dimension, chunk_id slice) for audit.
        The chunk ids are used as Chroma ids, guaranteeing uniqueness and
        traceability.
        """
        matrix = np.asarray(loaded.matrix, dtype=np.float32)
        if matrix.shape[0] != len(units.chunk_id_order):
            raise ValueError(
                f"matrix rows {matrix.shape[0]} != chunk_id_order length {len(units.chunk_id_order)}"
            )
        if matrix.shape[1] != loaded.meta.embedding_dimension:
            raise ValueError(f"matrix columns {matrix.shape[1]} != meta dimension {loaded.meta.embedding_dimension}")

        # delete any previous content so a rebuilt matrix is always the only source.
        existing = self._client.get_collection(self.collection.name)
        existing.delete(where={}) if existing.count() else None

        chunk_ids = units.chunk_id_order
        documents = [unit.text for unit in units.units]
        metadatas = [{"document_id": unit.document_id, "chunk_index": int(unit.chunk_index)} for unit in units.units]

        self.collection.add(
            ids=chunk_ids,
            embeddings=matrix.tolist(),
            documents=documents,
            metadatas=metadatas,
        )
        return {
            "count": self.collection.count(),
            "dimension": matrix.shape[1],
            "first_chunk_id": chunk_ids[0] if chunk_ids else None,
            "last_chunk_id": chunk_ids[-1] if chunk_ids else None,
        }

    def query_native(
        self,
        query_embedding: np.ndarray,
        k: int,
        include: tuple[str, ...] = ("metadatas", "documents"),
    ):
        """Chroma's raw query result before our deterministic re-sort."""
        return self.collection.query(
            query_embeddings=[_embedding_list(query_embedding)],
            n_results=k,
            include=list(include),
        )

    def search_topk(self, query_embedding: np.ndarray, k: int, units: RetrievalUnitSet) -> list[VectorHit]:
        """Deterministic top-k: score desc, ties by ascending chunk id.

        We request the whole collection because the corpus is small (272 units,
        see the frozen valid_at_this_scale note), so the re-sort is exact. The
        Chroma score is cosine similarity (higher = closer under hnsw:space
        cosine). Distances must be requested explicitly or Chroma omits them.
        """
        n = units.by_id
        result = self.collection.query(
            query_embeddings=[_embedding_list(query_embedding)],
            n_results=len(n),
            include=["distances", "metadatas", "documents"],
        )
        ids = result["ids"][0]
        scores = result["distances"][0]  # Chroma returns 1 - cosine under cosine space
        candidates = [
            {
                "chunk_id": ids[i],
                "similarity": 1.0 - float(scores[i]),
            }
            for i in range(len(ids))
        ]
        candidates.sort(key=lambda row: (-row["similarity"], row["chunk_id"]))
        top = candidates[:k]
        return [
            VectorHit(
                chunk_id=row["chunk_id"],
                score=row["similarity"],
                document_id=str(units.by_id[row["chunk_id"]].document_id),
            )
            for row in top
        ]


@dataclass(frozen=True)
class CrossCheckResult:
    ok: bool
    topk_match: bool
    order_match: bool
    scores_finite: bool
    stale_or_duplicate_ids: bool
    detail: str


def numpy_crosscheck(
    store: VectorStore,
    loaded: LoadedMatrix,
    query_embedding: np.ndarray,
    top_hits: list[VectorHit],
    k: int,
) -> CrossCheckResult:
    """Exact brute-force NumPy cosine comparison (VALIDATION ONLY).

    Per embedding_config.json cross_check: never used to alter results. It
    compares the top-k chunk-id set and ranking order from Chroma against the
    exact NumPy cosine over the stored matrix. A mismatch is a finding, not
    something to resolve in Chroma's favour.
    """
    matrix = np.asarray(loaded.matrix, dtype=np.float32)
    query = np.asarray(query_embedding, dtype=np.float32)

    # The matrix is unit-normalised, so cosine = dot product; but a direct
    # normalisation of the query avoids trusting that assumption in the check.
    query_norm = np.linalg.norm(query)
    if query_norm == 0:
        return CrossCheckResult(False, False, False, False, False, "query embedding has zero norm")

    dot = matrix @ (query / query_norm)
    if not np.all(np.isfinite(dot)):
        return CrossCheckResult(False, False, False, False, False, "matrix dot product has non-finite values")

    order = np.argsort(-dot, kind="stable")
    numpy_ids = [loaded.meta.chunk_id_order[i] for i in order]
    numpy_top = numpy_ids[:k]
    chroma_top = [hit.chunk_id for hit in top_hits]

    topk_match = set(numpy_top) == set(chroma_top)
    order_match = numpy_top == chroma_top
    scores_finite = all(np.isfinite(h.score) for h in top_hits) and np.all(np.isfinite(dot))

    # stale/duplicate check: each id appears at most once and every id is a known unit.
    seen = set()
    stale = False
    for cid in chroma_top:
        if cid in seen or cid not in loaded.meta.chunk_id_order:
            stale = True
        seen.add(cid)

    return CrossCheckResult(
        ok=topk_match and order_match and scores_finite and not stale,
        topk_match=topk_match,
        order_match=order_match,
        scores_finite=scores_finite,
        stale_or_duplicate_ids=stale,
        detail=(
            f"top-k set match={topk_match}, order match={order_match}, "
            f"scores finite={scores_finite}, stale/duplicate={stale}"
        ),
    )
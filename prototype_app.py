"""Layer 2: Interactive demonstration prototype (Streamlit).

Run with:  streamlit run prototype_app.py

This is a DEMONSTRATION interface, not a source of experimental measurements.
It calls the same frozen retrieval/RAG modules as the experiment (BM25 index,
frozen prompt, Chroma store) but works on a single user-entered question and
never touches the 32-query benchmark, ground-truth resolution, or the
results/experiments output directories.

Presentation-layer only: retrieval, embeddings, top-k, the frozen prompt,
generation settings, and the retrieved passage texts are frozen and untouched
by this file. It merely arranges what is already returned by the pipeline.
"""

from __future__ import annotations

import os
import re

import streamlit as st

from src.evaluation.classify import ABSTENTION_LINE
from src.prototype.pipeline import DemoPipeline
from src.retrieval.units import parse_citation

# Presentation-only: parenthesised document/chunk references in the generated
# answer, e.g. (DOC-FEAT-M-01-v2#C0). This is distinct from the frozen bracket
# citation extractor (src/rag/citations.py) and never changes validation.
_REF_GROUP_RE = re.compile(r"\(([^()]*)\)")
# Word characters + hyphens so variant doc ids like DOC-FEAT-M-01-v2#C0 match;
# anything that is not an exact supplied-evidence id is filtered downstream.
_DOC_REF_RE = re.compile(r"[A-Za-z][A-Za-z0-9-]*#C\d+")


def env_openai_key() -> str:
    """Return the key value or '' — the value is used live and never logged.

    Reads Streamlit Cloud Secrets first (	hosted deployment, key stored in the
    app's secrets vault), then falls back to the local environment / .env file.
    """
    try:
        value = st.secrets.get("OPENAI_API_KEY", "")
    except FileNotFoundError:
        value = ""
    return value or os.environ.get("OPENAI_API_KEY", "")


@st.cache_resource
def get_pipeline() -> DemoPipeline:
    return DemoPipeline()


def _evidence_card(rank: int, hit: dict, unit) -> None:
    """A compact, collapsed evidence card with the exact retrieved passage."""
    document_type = unit.doc_type or "unknown"
    title = unit.heading_path[-1] if unit.heading_path else ""

    meta_parts = [
        f"Rank {rank}",
        f"Document ID: `{unit.document_id}`",
        f"Chunk ID: `{unit.chunk_id}`",
        f"Retrieval score: `{hit['score']:.4f}`",
        f"Document type: `{document_type}`",
    ]
    if title:
        meta_parts.append(f"Heading: {title}")
    if unit.version_status:
        meta_parts.append(f"Status: `{unit.version_status}`")

    label = f"Rank {rank} — {unit.citation} — {document_type} — score {hit['score']:.3f}"
    with st.expander(label):
        st.caption(" · ".join(meta_parts))
        st.markdown(unit.text)


def _evidence_references(answer: str) -> list[str]:
    """Parenthesised DOCUMENT_ID#Cn refs in the answer (display-only).

    The frozen citation extractor only recognises the bracket form
    [DOCUMENT_ID#Cn] (rag_config.json). The model sometimes points at the same
    supplied passages in parentheses instead. This scanner surfaces those
    parenthesised references so the UI never shows a bare "none cited" next to
    an answer that already names its evidence. It is presentation only: nothing
    here feeds extraction, validation, or any metric, and only refs that match
    the supplied evidence are displayed downstream.
    """
    refs: list[str] = []
    for group in _REF_GROUP_RE.findall(answer):
        for token in _DOC_REF_RE.findall(group):
            try:
                document_id, chunk_index = parse_citation(token)
            except ValueError:
                continue
            refs.append(f"{document_id}#C{chunk_index}")
    return list(dict.fromkeys(refs))


def _citation_summary(result, supplied_citations: set[str]) -> None:
    """Grounded-citation reporting under the answer (unchanged semantics).

    Two distinct displays, kept separate on purpose:
      * "Citations in answer" — the formally extracted and validated bracket
        citations [DOCUMENT_ID#Cn] reported by the pipeline.
      * "Referenced evidence" — parenthesised DOCUMENT_ID#Cn references that
        appear in the answer and match the supplied retrieved evidence. These
        are evidence references only; they are never promoted to formal
        citations and unsupported ids are never invented.
    """
    formal = list(dict.fromkeys(result.rag_citations))
    referenced = [r for r in _evidence_references(result.rag_answer)
                  if r in supplied_citations]

    if result.fabricated_citations:
        st.error(
            "Fabricated citations detected (not supplied as evidence): "
            + ", ".join(result.fabricated_citations)
        )
        return

    if formal:
        chips = " ".join(f"`[{citation}]`" for citation in formal)
        st.markdown("**Citations in answer —** " + chips)
    else:
        st.caption("No formally extracted `[DOCUMENT_ID#Cn]` citations in the answer.")

    if referenced:
        chips = " ".join(f"`{citation}`" for citation in referenced)
        st.markdown("**Referenced evidence —** " + chips)
        st.caption(
            "Parenthesised document/chunk references in the answer that match "
            "the retrieved evidence. These are evidence references, not the "
            "formally extracted `[DOCUMENT_ID#Cn]` citations above."
        )

    if not formal and not referenced:
        st.caption("Citations — none cited in the answer.")
        st.caption(
            "Citation grounding verified against the retrieved evidence — "
            "no fabricated identifiers."
        )
    elif formal:
        st.caption(
            "Citation grounding verified against the retrieved evidence — "
            "no fabricated identifiers."
        )


def main() -> None:
    st.set_page_config(page_title="Product Documentation Assistant — Interactive Prototype",
                       layout="wide")
    st.title("Product Documentation Assistant")
    st.caption("RAG assistant prototype — separate from the frozen 32-query benchmark.")

    pipeline = get_pipeline()

    store_label = {"chromadb": "Chroma"}.get(
        pipeline.rag_config.vector_store_name,
        pipeline.rag_config.vector_store_name,
    )

    with st.sidebar:
        st.header("Configuration")
        st.caption("Frozen experiment settings — read-only")
        st.markdown(f"- **Top-k:** {pipeline.rag_config.top_k}")
        st.markdown(f"- **RAG model:** {pipeline.rag_config.model_name}")
        st.markdown(f"- **Vector store:** {store_label}")

    with st.container(border=True):
        st.markdown("**Ask a question about the product documentation**")
        question = st.text_input(
            "Question",
            label_visibility="collapsed",
            value="Does component M-01 have an unresolved dependency?",
            placeholder="e.g. Can you summarise what the Progressive Profiling feature does?",
        )
        run = st.button("Run assistant", type="primary", use_container_width=True)

    if not run:
        st.caption(
            "Enter a question above and click **Run assistant**. The assistant "
            "retrieves the top passages from the frozen Chroma store, then answers "
            "with the frozen RAG prompt and cites its evidence."
        )
        return

    key = env_openai_key()
    if not key:
        st.error("OPENAI_API_KEY is not set. Locally, set it in a .env file "
                 "(git-ignored) before running the app. On Streamlit Cloud, add "
                 "it under the app's Settings → Secrets.")
        return

    import openai

    client = openai.OpenAI(api_key=key)

    def embed_query(text: str):
        from src.embeddings.generate import EmbeddingConfig

        config = EmbeddingConfig.load()
        response = client.embeddings.create(
            model=config.model_name,
            input=[text],
            encoding_format=config.encoding_format,
        )
        return response.data[0].embedding

    with st.spinner("Retrieving and generating…"):
        result = pipeline.answer(question, client, embed_query)

    if result.status != "ok":
        st.error("The demo could not complete: " + result.error_message)
        return

    st.divider()
    st.markdown("## RAG Answer")
    if ABSTENTION_LINE in result.rag_answer:
        st.info(
            "The retrieved evidence does not contain enough information, so the "
            "assistant abstained instead of answering (frozen prompt behaviour)."
        )
    with st.container(border=True):
        st.markdown(result.rag_answer)

    supplied_citations = {
        pipeline.units.by_id[hit["chunk_id"]].citation
        for hit in result.rag_context
    }
    _citation_summary(result, supplied_citations)

    st.divider()
    st.markdown("## Retrieved Evidence")
    st.caption(
        f"Top {len(result.rag_context)} passages returned by the frozen Chroma "
        f"store (top-k = {pipeline.rag_config.top_k}), collapsed for readability."
    )
    for hit in result.rag_context:
        unit = pipeline.units.by_id[hit["chunk_id"]]
        _evidence_card(hit["rank"], hit, unit)

    with st.expander("BM25 baseline — same frozen units, lexical retrieval"):
        st.caption("Default BM25 retrieval over the identical evidence set, for comparison.")
        for hit in result.bm25_hits:
            unit = pipeline.units.by_id[hit["chunk_id"]]
            _evidence_card(hit["rank"], hit, unit)

    st.divider()
    st.caption("Interactive prototype. Benchmark results are evaluated separately using "
               "the frozen 32-query experiment.")


if __name__ == "__main__":
    main()
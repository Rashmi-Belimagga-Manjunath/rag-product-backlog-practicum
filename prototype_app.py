"""Layer 2: Interactive demonstration prototype (Streamlit).

Run with:  streamlit run prototype_app.py

This is a DEMONSTRATION interface, not a source of experimental measurements.
It calls the same frozen retrieval/RAG modules as the experiment (BM25 index,
frozen prompt, Chroma store) but works on a single user-entered question and
never touches the 32-query benchmark, ground-truth resolution, or the
results/experiments output directories.

Built for a non-programmer to explore: BM25 and RAG side by side, evidence
passages shown, citations validated, and provenance visible.
"""

from __future__ import annotations

import os

import streamlit as st

from src.prototype.pipeline import DemoPipeline


def env_openai_key() -> str:
    """Return the key value or '' — the value is used live and never logged."""
    return os.environ.get("OPENAI_API_KEY", "")


@st.cache_resource
def get_pipeline() -> DemoPipeline:
    return DemoPipeline()


def main() -> None:
    st.set_page_config(page_title="RAG vs BM25 — Product Documentation Demo",
                       layout="wide")
    st.title("Product Documentation Assistant")
    st.caption("BM25 baseline vs RAG assistant, demo prototype (Layer 2). "
               "Not part of the 32-query benchmark.")

    pipeline = get_pipeline()

    with st.sidebar:
        st.header("Configuration")
        st.write(f"Top-k (frozen): {pipeline.rag_config.top_k}")
        st.write(f"RAG model: {pipeline.rag_config.model_name}")
        st.write(f"Vector store: {pipeline.rag_config.vector_store_name} "
                 f"({pipeline.rag_config.persist_directory})")
        key = env_openai_key()
        st.write("API key: " + ("configured" if key else "not configured"))

    question = st.text_input(
        "Ask a question about the product documentation",
        value="Does component M-01 have an unresolved dependency?",
    )

    if st.button("Run assistant", type="primary"):
        if not key:
            st.error("OPENAI_API_KEY is not set in your environment. Set it in a "
                     "local .env file (ignored by git) before running the demo.")
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

        st.subheader("RAG assistant")
        st.markdown(result.rag_answer)

        if result.fabricated_citations:
            st.error("Fabricated citations detected (not supplied as evidence): "
                     + ", ".join(result.fabricated_citations))
        else:
            st.info("All citations were supplied as evidence.")

        st.markdown("**Citations:** " + (", ".join(result.rag_citations) or "none"))

        with st.expander("RAG retrieved evidence (top passages)"):
            for hit in result.rag_context:
                unit = pipeline.units.by_id[hit["chunk_id"]]
                st.write(f"**Rank {hit['rank']}** — {unit.citation} — "
                         f"similarity {hit['score']:.4f}")
                st.text(unit.text[:1200])

        with st.expander("BM25 baseline — top passages"):
            for hit in result.bm25_hits:
                unit = pipeline.units.by_id[hit["chunk_id"]]
                st.write(f"**Rank {hit['rank']}** — {unit.citation} — "
                         f"score {hit['score']:.4f}")
                st.text(unit.text[:1200])


if __name__ == "__main__":
    main()
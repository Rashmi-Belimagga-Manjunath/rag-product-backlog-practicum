# Experiment Freeze Checklist — moved

The authoritative freeze checklist is now the repository-root file:

**[`EXPERIMENT_FREEZE_CHECKLIST.md`](../EXPERIMENT_FREEZE_CHECKLIST.md)**

It was promoted to the repository root so the freeze gate sits alongside
`PROJECT_SPECIFICATION.md`, `DECISIONS.md` and `CHUNKING_DECISION.md` rather than buried
in `docs/`. This file is kept only as a pointer so existing links do not break.

Two supporting documents carry the detail:

- `docs/rag_configuration.md` — RAG top-k, generation model, system prompt and citation format
- `docs/bm25_configuration.md` — BM25 k1/b, tokenisation and result presentation
- `docs/evaluation_metrics.md` — exact operational definitions of the eight metrics (D-009, frozen)
- `docs/reproducibility.md` — reproducibility artefact and hash specification (D-012, frozen)
- `CHUNKING_DECISION.md` — the frozen C6 measure and the frozen 1000/200 configuration

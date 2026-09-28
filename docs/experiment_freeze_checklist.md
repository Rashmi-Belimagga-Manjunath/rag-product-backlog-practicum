# Experiment Freeze Checklist — moved

The authoritative freeze checklist is now the repository-root file:

**[`EXPERIMENT_FREEZE_CHECKLIST.md`](../EXPERIMENT_FREEZE_CHECKLIST.md)**

It was promoted to the repository root so the freeze gate sits alongside
`PROJECT_SPECIFICATION.md`, `DECISIONS.md` and `CHUNKING_DECISION.md` rather than buried
in `docs/`. This file is kept only as a pointer so existing links do not break.

Two supporting documents carry the detail:

- `docs/rag_configuration.md` — RAG top-k, generation model, system prompt and citation format
- `docs/bm25_configuration.md` — BM25 k1/b, tokenisation and result presentation
- `docs/evaluation_metrics.md` — the eight metric formulas and procedures

# Experiment Log

Append-only. Never edit or delete an existing entry — including failed and abandoned
runs, which are themselves data.

**Experiment ID format:** `EXP-YYYYMMDD-NNN`

## Required fields per experiment

| Field | Notes |
|---|---|
| Experiment ID | |
| Date | |
| Purpose | What question does this run answer? |
| Configuration | Full config: embedding model, generation model, chunking strategy, chunk size, overlap, top-k, BM25 k1/b, prompt version |
| Dataset version | Must match a `data/versions/MANIFEST.json` entry |
| Query-set version | |
| Ground-truth version | |
| Seed | |
| Library versions | `pip freeze` output or `requirements.lock` |
| Results | Path to `results/EXP-YYYYMMDD-NNN/{raw,processed,tables,figures}/` |
| Observations | What the numbers appear to show |
| Known limitations | What this run cannot establish |

**Rule:** never report a metric whose underlying data does not exist. If a metric could
not be computed, record it as *not computed*, with the reason.

---

## Experiments

_No experiments have been run yet._

Implementation has not started. The first run cannot happen until the open decisions in
`DECISIONS.md` are resolved — in particular the dataset, query-set, and ground-truth
versions, which do not exist yet.

---

## Template

```markdown
### EXP-YYYYMMDD-NNN — <short purpose>

**Date:**
**Purpose:**

**Configuration**
| Parameter | Value |
|---|---|
| Embedding model | |
| Generation model | |
| Chunking strategy | |
| Chunk size / overlap | |
| Retrieval top-k | |
| BM25 k1 / b | |
| Prompt version | |
| Seed | |

**Versions**
| Artefact | Version |
|---|---|
| Dataset | |
| Query set | |
| Ground truth | |

**Library versions:** see `results/EXP-YYYYMMDD-NNN/requirements.lock`

**Results:** `results/EXP-YYYYMMDD-NNN/`

**Observations:**

**Known limitations:**

**Notes on validity:**
```

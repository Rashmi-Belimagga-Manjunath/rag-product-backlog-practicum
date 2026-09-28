# Query Specification — 32 Approved Slots

**Status:** Specification only. No query wording generated, no ground truth built.
**Frozen:** the *distribution* is approved and frozen. Query *wording* is authored at
generation time, then difficulty is measured and labels are confirmed before either
system is evaluated.

## Approved distribution

| Category | Total | Easy | Moderate | Hard |
|---|---:|---:|---:|---:|
| Information retrieval | 6 | 3 | 2 | 1 |
| Feature context | 5 | 2 | 2 | 1 |
| Dependency identification | 8 | 2 | 3 | 3 |
| Cross-document reasoning | 5 | 1 | 1 | 3 |
| Conflict identification | 3 | 1 | 1 | 1 |
| Backlog analysis | 5 | 2 | 2 | 1 |
| **TOTAL** | **32** | **11** | **11** | **10** |

Dependency-related: **13** = dependency identification (8) + cross-document reasoning (5).

| Category | Total | Explicit | Implicit |
|---|---:|---:|---:|
| Dependency identification | 8 | 4 | 4 |
| Cross-document reasoning | 5 | 2 | 3 |
| **Total** | **13** | **6** | **7** |

Version queries: **3** (Q-SUP-1 … Q-SUP-3), occupying slots inside information retrieval
and feature context. **Not additional to the 32.**

## Slot register

`Slot` is the position 1–32. `Cat` = category abbreviation:
`IR` information retrieval · `FC` feature context · `DI` dependency identification ·
`CDR` cross-document reasoning · `CI` conflict identification · `BA` backlog analysis.

| Slot | Query ID | Cat | Intended difficulty | Dependency | Target | Version query |
|---:|---|---|---|---|---|---|
| 1 | Q-01 | IR | easy | — | a high-traffic PBI | — |
| 2 | Q-02 | IR | easy | — | a runbook | — |
| 3 | Q-03 | IR | easy | — | a feature spec | — |
| 4 | Q-04 | IR | moderate | — | a decision record | — |
| 5 | Q-SUP-1 | IR | moderate | — | current PRD | **recency** |
| 6 | Q-05 | IR | hard | — | a colloquial ticket | — |
| 7 | Q-06 | FC | easy | — | a feature summary | — |
| 8 | Q-07 | FC | easy | — | a requirement statement | — |
| 9 | Q-SUP-3 | FC | easy | — | current spec limit | **current_value** |
| 10 | Q-08 | FC | moderate | — | a ruled-out option | — |
| 11 | Q-SUP-2 | FC | hard | — | superseded spec claim | **provenance** |
| 12 | Q-09 | DI | easy | explicit | a stated component dependency | — |
| 13 | Q-10 | DI | easy | explicit | a stated feature dependency | — |
| 14 | Q-11 | DI | moderate | explicit | a stated ordering constraint | — |
| 15 | Q-12 | DI | moderate | explicit | a third-party dependency | — |
| 16 | Q-13 | DI | moderate | implicit | an unstated component dependency | — |
| 17 | Q-14 | DI | hard | implicit | an unstated ordering constraint | — |
| 18 | Q-15 | DI | hard | implicit | an unstated cross-feature dependency | — |
| 19 | Q-16 | DI | hard | implicit | a dependency behind a runbook | — |
| 20 | Q-17 | CDR | easy | explicit | a dependency visible in one document | — |
| 21 | Q-18 | CDR | moderate | explicit | a dependency split across two documents | — |
| 22 | Q-19 | CDR | moderate | implicit | a relationship from the meeting notes | — |
| 23 | Q-20 | CDR | hard | implicit | an ordering inferred from the PRD sequence | — |
| 24 | Q-21 | CDR | hard | implicit | a dependency behind a superseded document | — |
| 25 | Q-22 | CI | easy | — | a resolved conflict | — |
| 26 | Q-23 | CI | moderate | — | an unresolved conflict | — |
| 27 | Q-24 | CI | hard | — | a conflict whose resolution lives in a later version | — |
| 28 | Q-25 | BA | easy | — | a documented prioritisation decision | — |
| 29 | Q-26 | BA | easy | — | a stated non-goal | — |
| 30 | Q-27 | BA | moderate | — | the rationale behind a changed decision | — |
| 31 | Q-28 | BA | moderate | — | a deprioritised item's reason | — |
| 32 | Q-29 | BA | hard | — | a synthesis across a feature and its decision record | — |

**Totals:** 32 slots · 11 easy · 11 moderate · 10 hard · 13 dependency-related
(6 explicit, 7 implicit) · 3 version queries.

## Slot design notes

**Hard queries are concentrated in DI and CDR on purpose.** 6 of the 10 hard queries sit
in the two dependency categories. If difficulty clustered in information retrieval, the
experiment would measure lexical mismatch rather than reasoning, and would flatter
whichever system tolerates paraphrase.

**Q-SUP-2 is in the hard band by construction.** Its target claim lives in a *superseded*
document, so overlap with the current version is deliberately low.

**Q-SUP-2 is relevant-in-superseded.** It is the query that defeats the degenerate
strategy of always retrieving the newest document. Its ground truth is both the
superseded spec (which states the claim) and the current spec (which supersedes it), so
`relevance_basis = "both"`.

## Constraint on backlog-analysis slots

Slots 28–32 must be answerable from **documented rationale and requirement priority** —
decision records, non-goals, stated prioritisation. If a drafted backlog question turns
out to require dependency reasoning, it is **reclassified into the dependency-related set
before the experiment** and recorded in `DECISIONS.md`. Backlog questions must not
silently become dependency questions.

## Difficulty classification

`overlap = |content_words(Q) ∩ content_words(G)| / |content_words(Q)|`

`content_words` = lowercased, stopword-removed, length > 2, using the frozen `STOPWORDS`
set in `src/ground_truth/schema.py`.

| Band | Overlap |
|---|---|
| Easy | ≥ 40% |
| Moderate | 20–39% |
| Hard | < 20% |

> **Required framing for the methodology.** Lexical overlap is a
> **benchmark-construction measure**. It creates controlled variation in lexical alignment
> between a query and the information that answers it. It is **not** a validated
> psychological or cognitive measure of task difficulty. "Hard" means only that lexical
> alignment is low — not that the question is cognitively demanding.

**Procedure.** Wording is authored to target a band, then verified against the generated
corpus. A query not falling into its intended band is revised **before** either system is
evaluated. Difficulty labels are **never** reclassified after seeing results.

## Reporting constraints

- n=32 is **not** intended to support statistical significance testing. No statistical
  generalisability may be claimed from it.
- Results are interpreted through descriptive statistics, direction and effect of
  differences, category-level analysis, and error analysis.
- The 7-query implicit subset is **descriptive evidence only**.

# Runbook: Streak Calculator: inconsistent streak state

Document: DOC-RBK-T-04
Component: COMP-T-02 (Streak Calculator)
Owner: platform
Last reviewed: 2026-08-25

## Steps

1. Two reads of the same log disagree on streak length.
2. Purge duplicate log writes, then recompute from the canonical log.
3. Freeze tokens must be rebalanced after any recompute.

## Notes

Computes streak state from the log. Pure function over logged entries.


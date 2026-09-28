# Runbook: Habit Store: repairing a split log

Document: DOC-RBK-T-01
Component: COMP-T-01 (Habit Store)
Owner: platform
Last reviewed: 2026-08-18

## Steps

1. A split log shows two streak states for one user.
2. Merge the log entries by timestamp and recompute the streak.
3. Advise the user if recovery prompts were skipped while broken.

## Notes

Primary store for habits, logs and streak state.


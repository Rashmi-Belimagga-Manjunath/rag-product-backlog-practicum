# Runbook: Prompt Scheduler: silent schedule drift

Document: DOC-RBK-T-03
Component: COMP-T-05 (Prompt Scheduler)
Owner: platform
Last reviewed: 2026-08-22

## Steps

1. Schedules drift when the store write failed silently.
2. Recompute the next fire time from the habit schedule.
3. Recovery prompts are only valid before the streak breaks.

## Notes

Schedules and fires reminder and recovery prompts.


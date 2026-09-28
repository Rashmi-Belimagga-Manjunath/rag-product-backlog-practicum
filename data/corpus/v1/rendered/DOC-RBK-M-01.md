# Runbook: Domain Event Bus: recovering a delayed event

Document: DOC-RBK-M-01
Component: COMP-M-05 (Domain Event Bus)
Owner: platform
Last reviewed: 2026-08-05

## Steps

1. A delayed event shows up in the bus metrics as lag above 5 seconds.
2. Check the consumer group lag and restart the stalled consumer.
3. Do not drop the event; the ledger update depends on it completing.
4. If lag persists after two restarts, page the platform team.

## Notes

Carries domain events between services.


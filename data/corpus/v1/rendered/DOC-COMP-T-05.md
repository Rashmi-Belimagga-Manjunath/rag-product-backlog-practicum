# Prompt Scheduler

Document: DOC-COMP-T-05
Component: COMP-T-05
Type: service
Owner: platform

## Description

Schedules and fires reminder and recovery prompts.

## Adjacent components

These components are technically related but are NOT dependencies of this one:

- COMP-T-04
- COMP-T-06

## Dependencies

- Prompt Scheduler depends on the habit store to perform its work, as stated in this component document.
- Prompt Scheduler depends on the push notification gateway to perform its work, as stated in this component document.

## Operational notes

The component is monitored through the shared alerting channel; the owning team reviews capacity and latency trends before every release.


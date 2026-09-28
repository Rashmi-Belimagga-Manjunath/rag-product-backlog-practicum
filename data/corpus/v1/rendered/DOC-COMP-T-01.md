# Habit Store

Document: DOC-COMP-T-01
Component: COMP-T-01
Type: database
Owner: platform

## Description

Primary store for habits, logs and streak state.

## Adjacent components

These components are technically related but are NOT dependencies of this one:

- COMP-T-02

## Dependencies

- Habit Store depends on the push notification gateway to perform its work, as stated in this component document.

## Operational notes

The component is monitored through the shared alerting channel; the owning team reviews capacity and latency trends before every release.


# Streak Calculator

Document: DOC-COMP-T-02
Component: COMP-T-02
Type: service
Owner: platform

## Description

Computes streak state from the log. Pure function over logged entries.

## Adjacent components

These components are technically related but are NOT dependencies of this one:

- COMP-T-01
- COMP-T-03

## Dependencies

- Streak Calculator depends on the habit store to perform its work, as stated in this component document.
- Streak Calculator depends on the prompt scheduler to perform its work, as stated in this component document.

## Operational notes

The component is monitored through the shared alerting channel; the owning team reviews capacity and latency trends before every release.


# Social Graph Service

Document: DOC-COMP-T-07
Component: COMP-T-07
Type: service
Owner: platform

## Description

Manages friend relationships and shared-streak state.

## Adjacent components

These components are technically related but are NOT dependencies of this one:

- COMP-T-06
- COMP-T-08

## Dependencies

- Social Graph Service depends on the habit store to perform its work, as stated in this component document.
- Social Graph Service depends on the push notification gateway to perform its work, as stated in this component document.

## Operational notes

The component is monitored through the shared alerting channel; the owning team reviews capacity and latency trends before every release.


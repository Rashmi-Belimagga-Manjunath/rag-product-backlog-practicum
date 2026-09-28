# Digest Notification Worker

Document: DOC-COMP-M-04
Component: COMP-M-04
Type: service
Owner: platform

## Description

Builds and sends scheduled email digests.

## Adjacent components

These components are technically related but are NOT dependencies of this one:

- COMP-M-03
- COMP-M-05

## Dependencies

- Digest Notification Worker depends on the domain event bus to perform its work, as stated in this component document.

## Operational notes

The component is monitored through the shared alerting channel; the owning team reviews capacity and latency trends before every release.


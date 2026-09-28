# Domain Event Bus

Document: DOC-COMP-M-05
Component: COMP-M-05
Type: queue
Owner: platform

## Description

Carries domain events between services.

## Adjacent components

These components are technically related but are NOT dependencies of this one:

- COMP-M-04
- COMP-M-06

## Dependencies

- Domain Event Bus depends on the verisign identity verification api to perform its work, as stated in this component document.

## Operational notes

The component is monitored through the shared alerting channel; the owning team reviews capacity and latency trends before every release.


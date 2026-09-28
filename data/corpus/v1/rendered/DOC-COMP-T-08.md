# Export Bundle Service

Document: DOC-COMP-T-08
Component: COMP-T-08
Type: service
Owner: platform

## Description

Packages a user's habit history into a portable export bundle.

## Adjacent components

These components are technically related but are NOT dependencies of this one:

- COMP-T-07

## Dependencies

- Export Bundle Service depends on the habit store to perform its work, as stated in this component document.
- Export Bundle Service depends on the prompt scheduler to perform its work, as stated in this component document.

## Operational notes

The component is monitored through the shared alerting channel; the owning team reviews capacity and latency trends before every release.


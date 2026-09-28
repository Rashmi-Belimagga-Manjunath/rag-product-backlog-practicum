# Verisign Identity Verification API

Document: DOC-COMP-M-01
Component: COMP-M-01
Type: third_party
Owner: external vendor

## Description

Third-party identity document verification. The team does not own this service; failures surface only as a timeout.

## Adjacent components

These components are technically related but are NOT dependencies of this one:

- COMP-M-02

## Dependencies

- Verisign Identity Verification API depends on the domain event bus to perform its work, as stated in this component document.

## Operational notes

The component is monitored through the shared alerting channel; the owning team reviews capacity and latency trends before every release.


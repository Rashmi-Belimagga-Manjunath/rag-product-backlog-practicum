# TaxBand Rate Service

Document: DOC-COMP-M-06
Component: COMP-M-06
Type: third_party
Owner: external vendor

## Description

Resolves tax bands for a given jurisdiction. Rate-limited, 20 calls/min.

## Adjacent components

These components are technically related but are NOT dependencies of this one:

- COMP-M-05
- COMP-M-07

## Dependencies

- TaxBand Rate Service depends on the domain event bus to perform its work, as stated in this component document.

## Operational notes

The component is monitored through the shared alerting channel; the owning team reviews capacity and latency trends before every release.


# Email Digest Worker

Document: DOC-COMP-T-04
Component: COMP-T-04
Type: service
Owner: platform

## Description

Assembles and sends email digests on a schedule.

## Adjacent components

These components are technically related but are NOT dependencies of this one:

- COMP-T-03
- COMP-T-05

## Dependencies

- Email Digest Worker depends on the habit store to perform its work, as stated in this component document.

## Operational notes

The component is monitored through the shared alerting channel; the owning team reviews capacity and latency trends before every release.


# MyMeridian Employee App

Document: DOC-COMP-M-08
Component: COMP-M-08
Type: service
Owner: platform

## Description

The employee-facing web application surface.

## Adjacent components

These components are technically related but are NOT dependencies of this one:

- COMP-M-07
- COMP-M-09

## Dependencies

- MyMeridian Employee App depends on the timesheet approval engine to perform its work, as stated in this component document.
- MyMeridian Employee App depends on the domain event bus to perform its work, as stated in this component document.

## Operational notes

The component is monitored through the shared alerting channel; the owning team reviews capacity and latency trends before every release.


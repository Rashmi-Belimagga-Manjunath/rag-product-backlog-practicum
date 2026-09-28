# Payroll Ledger Database

Document: DOC-COMP-M-02
Component: COMP-M-02
Type: database
Owner: platform

## Description

System of record for approved hours, overtime and payroll totals.

## Adjacent components

These components are technically related but are NOT dependencies of this one:

- COMP-M-01
- COMP-M-03

## Dependencies

- Payroll Ledger Database depends on the domain event bus to perform its work, as stated in this component document.

## Operational notes

The component is monitored through the shared alerting channel; the owning team reviews capacity and latency trends before every release.


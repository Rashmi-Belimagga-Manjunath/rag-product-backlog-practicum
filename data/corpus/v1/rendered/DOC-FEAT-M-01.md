# Progressive Profiling - specification

Document: DOC-FEAT-M-01
Status: SUPERSEDED. Version 1.0, last modified 2026-02-10. This version was replaced by DOC-FEAT-M-01-v2 and is retained for history only. Do not implement from this document.

Product: Meridian (PROD-M)
Feature: FEAT-M-01
Lifecycle status: launched
Priority: 1

## Purpose

Collects additional employee details progressively after first login rather than in a single mandatory form.

## Terminology

Within this document the feature is referred to as: Progressive Profiling.
Users describe the same thing as: onboarding ramp, new-user activation, first-run setup.

## Behaviour

When progressive profiling is active, the product behaves as follows.

## Dependencies

- Progressive Profiling depends on the taxband rate service to provide this behaviour, as stated in this specification.
- FEAT-M-01 relies on the third-party service Verisign Identity Verification API; stated in the specification.

## Approval limit

Under version 1.0, the approval limit for Progressive Profiling was $2,500.

## Related features

The following features are adjacent in scope and are sometimes confused with this one:

- FEAT-M-02
- FEAT-M-08

## Historical behaviour

Under version 1.0, tax documentation was collected during initial account registration, before the employee had used the product. This was replaced in version 2.0.


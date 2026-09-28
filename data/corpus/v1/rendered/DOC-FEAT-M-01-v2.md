# Progressive Profiling - specification

Document: DOC-FEAT-M-01-v2
Status: current. Version 2.0. Last modified 2026-07-22.

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

The current approval limit for Progressive Profiling is $5,000.

## Related features

The following features are adjacent in scope and are sometimes confused with this one:

- FEAT-M-02
- FEAT-M-08


# Identity Verification Window - specification

Document: DOC-FEAT-M-02
Status: current. Version 1.0. Last modified 2026-03-04.

Product: Meridian (PROD-M)
Feature: FEAT-M-02
Lifecycle status: launched
Priority: 2

## Purpose

Requires identity document verification before an employee can be granted payment privileges.

## Terminology

Within this document the feature is referred to as: ID check stage.
Users describe the same thing as: ID check stage, KYC prompt, the verification pop-up.

## Behaviour

When id check stage is active, the product behaves as follows.

## Dependencies

- Identity Verification Window depends on the verisign identity verification api to provide this behaviour, as stated in this specification.
- FEAT-M-02 is ordered to run before FEAT-M-01 in the product sequence; stated in the specification.

## Related features

The following features are adjacent in scope and are sometimes confused with this one:

- FEAT-M-01
- FEAT-M-03


# Identity Verification Window - specification

Document: DOC-FEAT-A-02
Status: current. Version 1.0. Last modified 2026-03-04.

Product: Meridian (PROD-A)
Feature: FEAT-A-02
Lifecycle status: launched
Priority: 2

## Purpose

Requires identity document verification before an employee can be granted payment privileges.

## Terminology

Within this document the feature is referred to as: Identity Verification Window.
Users describe the same thing as: ID check stage, KYC prompt, the verification pop-up.

## Behaviour

When identity verification window is active, the product behaves as follows.

## Dependencies

- Identity Verification Window calls the third-party identity verification service. Stated in the feature specification.
- Payment privileges are granted only once the employee is payroll-ready, so this follows from the first PRD. Stated in that PRD.

## Related features

The following features are adjacent in scope and are sometimes confused with this one:

- FEAT-A-01
- FEAT-A-03


# Tax Band Adjustments - specification

Document: DOC-FEAT-M-08
Status: current. Version 1.0. Last modified 2026-03-04.

Product: Meridian (PROD-M)
Feature: FEAT-M-08
Lifecycle status: launched
Priority: 7

## Purpose

Resolves and applies tax band adjustments for individual employees.

## Terminology

Within this document the feature is referred to as: Tax Band Adjustments.
Users describe the same thing as: tax code changes, payroll bracket update.

## Behaviour

When tax band adjustments is active, the product behaves as follows.

## Dependencies

- Tax Band Adjustments depends on the taxband rate service to provide this behaviour, as stated in this specification.
- FEAT-M-08 relies on the third-party service TaxBand Rate Service; stated in the specification.
- FEAT-M-08 is ordered to run before FEAT-M-01 in the product sequence; stated in the specification.

## Related features

The following features are adjacent in scope and are sometimes confused with this one:

- FEAT-M-07
- FEAT-M-01


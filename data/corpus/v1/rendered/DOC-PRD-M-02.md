# Meridian manager approval and payroll export

Document: DOC-PRD-M-02
Status: SUPERSEDED. Version 1.0, last modified 2026-02-02. This version was replaced by DOC-PRD-M-02-v2 and is retained for history only. Do not implement from this document.

Author: Product Manager
Product: Meridian (PROD-M)

## Background

Covers bulk timesheet approval and recurring payroll file export to external payroll providers.

## Goals

Reduce the friction between signing up and keeping a first habit going, while keeping the streak mechanic predictable and honest for every user.

## Non-goals

This document does not cover habit template curation or social features. Those are specified separately.

## Requirements

### REQ-M-03: Managers approve timesheets in bulk

A manager must be able to approve multiple timesheets in one action where all selected timesheets are complete.

This requirement is normative for Meridian. Where another document disagrees, this statement takes precedence.

### REQ-M-04: Payroll exports follow a fixed schedule

Payroll exports must run on a fixed, pre-configured schedule and must not be triggered ad hoc by end users.

This requirement is normative for Meridian. Where another document disagrees, this statement takes precedence.

## Success measures

Measured as: thirty-day streak survival, share of recovery prompts accepted, and repeat-week retention after a prompt is offered.

## Open questions

How forceful should the first recovery prompt be? The current answer of a single light suggestion is provisional.


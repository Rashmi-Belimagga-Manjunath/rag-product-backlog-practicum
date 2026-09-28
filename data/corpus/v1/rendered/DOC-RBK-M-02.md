# Runbook: Payroll Ledger: overnight reconciliation

Document: DOC-RBK-M-02
Component: COMP-M-02 (Payroll Ledger Database)
Owner: platform
Last reviewed: 2026-08-10

## Steps

1. Verify the ledger and the export totals match within tolerance.
2. Re-run the export job if totals diverge; do not edit records by hand.
3. Record the drift in the audit trail before closing the run.

## Notes

System of record for approved hours, overtime and payroll totals.


# Runbook: Verisign identity verification: timeout handling

Document: DOC-RBK-M-04
Component: COMP-M-01 (Verisign Identity Verification API)
Owner: external vendor
Last reviewed: 2026-08-15

## Steps

1. A timeout means the verification did not return a decision.
2. Requeue the verification with a fresh correlation id.
3. Never auto-approve on timeout; the payment privilege must wait.

## Notes

Third-party identity document verification. The team does not own this service; failures surface only as a timeout.


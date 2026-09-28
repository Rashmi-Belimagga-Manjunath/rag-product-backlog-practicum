# Runbook: Push gateway: quiet-hours deliveries

Document: DOC-RBK-T-02
Component: COMP-T-03 (Push Notification Gateway)
Owner: external vendor
Last reviewed: 2026-08-20

## Steps

1. The gateway may delay pushes outside control.
2. Treat a delayed push as delivered-late, not failed.
3. Do not retry the same prompt; a second copy reads as nagging.

## Notes

Third-party push delivery. Delivery timing cannot be fully controlled.


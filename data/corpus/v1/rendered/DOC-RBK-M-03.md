# Runbook: TaxBand rate service: handling rate-limit responses

Document: DOC-RBK-M-03
Component: COMP-M-06 (TaxBand Rate Service)
Owner: external vendor
Last reviewed: 2026-08-12

## Steps

1. A 429 from the rate service means the 20 calls/minute budget is exhausted.
2. Back off for 30 seconds, then retry the single call. Do not retry the batch.
3. If three consecutive batches fail, raise an operations alert; the tax step cannot complete without resolved rates.

## Notes

Resolves tax bands for a given jurisdiction. Rate-limited, 20 calls/min.


# 0020. Recover generation across client navigation

**Date**: 2026-11-09
**Decision**: CONFIRMED by the Supervisor's instruction to fix the investigated defect.
**Progress**: DONE implementation, local verification and Render web deployment. Authenticated GPU acceptance NEEDS VERIFICATION.

## Summary

Keep manual studio drafts and accepted jobs outside the route component. Recover the same job after navigation or refresh using status reads. Preserve existing generation contracts, model settings and salon enhancements.

## Requirements

1. Hair, Makeup and Nails retain uploaded photo, selected style, progress and result when leaving and returning.
2. Persist admitted ticket metadata before polling and recover with GET only after refresh. Persist bounded photo and result drafts in browser IndexedDB, isolated by authenticated account. Storage failure must be visible and must not replay a POST.
3. Prevent concurrent manual generation within a tab and coordinate tabs using Web Locks where available plus shared active ticket metadata. The server remains the authoritative admission gate.
4. Preserve uncertain admission as uncertain. Never silently retry a generation POST. Expired or missing jobs must explain recovery failure and require explicit new generation.
5. Clear local drafts on logout, reject account mismatches, ignore old async completions, and bound retention to 30 minutes.
6. Restore normal consultation from its signed handle after navigation using status reads. Preserve guest trial behavior.
7. Verify route departure in all three manual studios, refresh recovery, interruption, expiry, storage failure and account isolation without GPU inference. Verify surrounding existing contracts and TypeScript.

## Decision and rationale

Use a shared client generation store with a React provider in the authenticated client layout. Use built in browser storage and locks, with no new dependency or backend infrastructure. Keep large portraits and generated data out of localStorage. Expose optional admission observation and explicit resume on the existing browser client. Existing API callers remain compatible.

Page navigation guards alone would prevent ordinary use and do not recover refresh. Changing the model cannot correct lost browser state. A durable server queue is unnecessary for this bounded correction and would change deployment responsibilities.

The current gateway retains three results for 30 minutes and does not survive worker restarts. Recovery cannot promise a result beyond those limits. Admission interrupted before a ticket is received cannot be reconciled through the current API and must remain blocked until its bounded window expires.

## Build and verification

Implement admission and resume helpers, account scoped browser persistence, shared studio state, and consultation handle recovery. Migrate the three manual pages without redesigning them. Convert the investigation reproduction into regression tests and cover recovery boundaries. Keep deployment separate from local verification.

## Evidence

153 focused tests, TypeScript and the production build pass. All three manual pages pass browser navigation and refresh with native IndexedDB and synthetic API responses. Live cloud acceptance and consultation recovery on the client's browser remain separate. [Implementation and limits](../experiments/generation-recovery-20261109.md).

The Supervisor authorized deployment. Main and Render now contain release4689b4c; dashboard Live status, public health/authentication boundary and actual recovery JS assets verify. No new GPU request. [Deployment receipt](../experiments/generation-recovery-deployment-20261109.md).

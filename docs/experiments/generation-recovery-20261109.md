# Generation recovery correction

Date: 9 November 2026. Implementation DONE. Local verification VERIFIED. Production deployment NOT STARTED.

## Cause and source

Client branch `codex/beautycore-enhancements`, base `efd63d763ce5b194e2df9eb1b742593d87c81060`, loses studio photo, style, loading and output state when the page unmounts. Generation can finish on an abandoned component while the returning page has lost its ticket. Another studio owns a different submission guard and can receive busy while the original job runs.

The fix is isolated on `codex/generation-recovery`. The original checkout and client branch are preserved. No model, training data, catalog, generation setting, GPU worker, AI backend API, deployment configuration or database schema changed.

## Correction

The authenticated client layout now owns a shared `GenerationProvider` and `GenerationStore`. Hair, Makeup and Nails retain their drafts and accepted jobs independently of page lifetimes. Progress offers Continue browsing, with a shared notice linking back to the running preview.

The existing browser client accepts an optional admission observer and exposes `resumeCustom`. Recovery only reads the original job status and result. It never silently repeats generation. Admission interrupted before a ticket arrives stays uncertain, blocking replacement until the recovery window expires. Missing or expired worker results report recovery failure.

Small ticket metadata is journaled synchronously in localStorage. Photo and result drafts use native browser IndexedDB, isolated by authenticated account and matched to job ID. An observer tab cannot pair an old portrait with a new output or overwrite the submitted portrait with its empty state. Storage notices synchronize assets after their transaction commits. Web Locks coordinate submissions where supported; shared ticket checks and the unchanged server admission gate remain additional controls.

Recovery lasts 30 minutes. Expired manual drafts clear during the active session or restoration. Browser drafts do not automatically Save Look to an account. Logout clears drafts, journals and the one time photo handoff, stops tracking and ignores late completions. Focus and session notices refresh identity, and stale responses cannot undo logout. A temporary session service failure returns HTTP 503 and preserves an existing workspace; a confirmed signed out session still returns user null and clears it. These controls do not cancel GPU work already admitted.

Normal consultation uses the shared workspace for its view and running refs, so existing async callbacks survive route departure. Refresh restores its signed handle and available photo/view, then checks server state and existing results. The handle is journaled before asynchronous photo storage. Transient flags are normalized on refresh. Guest trial state and allowance recovery stay separate. Manual and consultation generation coordinate within the workspace.

## Verification

The final focused suite passes **153 tests, zero failures**, including recovery and existing AI adapter, browser flow, job, runtime registration, auth response, guest trial and business UI tests. Existing save, booking, pricing and salon behavior passes. TypeScript and the full default Next.js production build pass with a dummy local database URL. No salon database or GPU was accessed.

Three regressions exercise actual pages and the actual browser client: Hair to Makeup to Hair, Makeup to Nails to Makeup, and Nails to Hair to Nails. They preserve photo/style/progress, prevent the competing POST and deliver the original completed output. Other tests cover refresh, cached completion, uncertain admission, expiry, missing results, storage failure, account isolation, late admission after logout, stale auth responses, matching source photos across tabs and consultation persistence.

A browser fixture exercises the actual pages, progress/result dialogs, provider, browser client and native IndexedDB. Only framework routing/auth adapters and API responses are synthetic. All three running jobs survive route departure and full refresh, then display completion. Another tab sees busy and the matching source photo. Cached results also survive refresh. Final counts are **3 generation POSTs**, 61 status reads and 6 result reads, including the observer tab. These establish recovery behavior, not model quality.

Local evidence is preserved in the original workspace at `artifacts/generation-recovery-20261109/`: `focused-tests.log`, `production-build.log`, browser fixture source, final DOM/counts and three final recovered result screenshots. An initial dependency junction failed Next resolution. A local copy of the same installed dependencies allowed the ordinary production build to pass. No build configuration or package dependency was changed to bypass that issue.

From `beautycore`, repeat targeted checks with:

```powershell
npm run test:recovery
npm run typecheck
npm run build
```

Build requires the repository's normal configuration. Verification used a nonfunctional local DATABASE_URL to avoid contacting the salon database.

## Remaining boundary and deployment

Live Render to Runpod generation on this fix remains NEEDS VERIFICATION. Live authenticated consultation recovery and behavior on the client's particular mobile browser remain to be checked. A worker restart or gateway expiry can still remove an old result. The UI now reports that boundary without creating a replacement.

After review, deploy the web source through Render's configured deployment branch. This correction needs no Runpod image change, Kaggle notebook, dataset upload, adapter update or training. No production merge, cloud redeployment or GPU request was performed during verification.

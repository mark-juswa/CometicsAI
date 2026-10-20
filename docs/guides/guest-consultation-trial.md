# Guest consultation trial: local review and release guide

Date: 2026-10-20
Status: development DONE; isolated verification VERIFIED; production deployment NOT STARTED.

## What was added

- Public `/try-consultation` using the shared Consultation component.
- Three existing text recommendations; guests choose just one recommendation to generate.
- Hair, Makeup and Nails stay available. Existing model settings and Nails-only optimization are unchanged.
- Separate `/api/ai-trial/[...path]` policy; the normal `/api/ai` still requires a current database client.
- Opaque persistent HttpOnly cookie plus a small Neon allowance ledger. No guest account, image database copy or booking record is created.
- Short atomic database admission before external work. An admitted attempt cannot be repeated from another tab or a new consultation.
- Guest-specific signed handle audience, server-derived owners and exact consultation/job binding.
- Signup/login invitations open a fresh full consultation. Exact-image transfer into a new account is not included.

The feature is OFF by default. No migration, Render deployment, live database query, live GPU request, Kaggle change or GitHub push was performed for this development task.

## Defaults and policy

| Setting or action | Implemented default |
| --- | --- |
| Browser allowance | One admitted generation attempt per fixed30-day identity; configurable1-90days |
| New trial identities per network | 2 within24hours; configurable1-10 |
| New trial identities globally | 12 within24hours; configurable1-100 |
| New generation admissions globally | 4 within24hours; configurable1-50 |
| Consultation starts | 2 per trial; conservative global6 per24hours |
| Photo uploads / preference updates | 2 / 4 per trial |
| Conversational turns | 6 per trial, including opening question; conservative global24 |
| Explicit recommendation calls | 2 per trial; conservative global12 |
| Generation submission attempts | Maximum8 per trial, including busy rejections; only one can be admitted |
| Polling / reading results | Does not spend another image credit |
| Known facade busy rejection | Releases the image reservation because no generation started |
| Unknown timeout/429/failure | Keeps reservation locked; no automatic replacement |
| Accepted job | Persists its ticket; repeated same-attempt submissions return the ticket without another upstream POST |

Global text/start accounting sums bounded lifetime counters for recently active trial rows. It is deliberately conservative and may reject earlier than an exact rolling event ledger. Network accounting uses new identity timestamps. These controls are for a small scheduled demo, not a full public-campaign anti-bot platform.

A cookie is not proof of a person. Clearing it, changing devices or networks can obtain another identity within the abuse budgets. Shared Wi-Fi can cause false positives. Existing public demo login shortcuts and unverified-email signup behavior are unchanged and should be reviewed before marketing the site publicly.

## Storage and interruptions

`0006_guest_consultation_trial.sql` adds only `ai_guest_trials` plus indexed admission metadata and the atomic `beautycore_guest_trial` function. It does not modify users, saved looks, appointments, reviews or inventory.

Stored data is token hash, internal guest owner, keyed network tag, timestamps, bounded counters and consultation/recommendation/job bindings. Photos, outputs and chat content remain in the existing temporary Kaggle runtime.

Cookie expiry is fixed from issuance and does not slide on refresh. Expired ledger records are cleaned opportunistically during new trial issuance after an additional day; there is no background cleanup scheduler. Rotating the handle secret also changes network tags; plan such changes as operational events.

If Render loses the response after Kaggle accepts a job, the attempt can remain reserved without a recoverable ticket. If a non-generation request crashes before its completion is recorded, preparation can remain locked. Both cases fail closed and direct the visitor to an account rather than making unbounded replacement work. No automated staff refund endpoint is included.

Refresh recovery reads the bound consultation/job while it exists. Kaggle restart, expiry or eviction can remove the image without restoring credit. Its existing job retention is30minutes with possible earlier eviction after other jobs; consultations have their own temporary lifetime. Do not promise permanent access to the guest preview.

## Local verification

From `I:/HAIR/beautycore`:

```powershell
npm run test:guest-trial
npm run test:business
npm run build
```

Guest tests use isolated PGlite plus synthetic browser/API responses. They need no live Neon connection, Kaggle GPU, client photo or key. Existing business tests also use isolated fixtures.

The completed verification covers23guest tests,58existing AI tests and47business tests,128total, plus the production build/TypeScript. This is not live browser, real Gemini inference, live proxy verification or GPU acceptance.

## Future release sequence: requires separate deployment approval

1. Keep `AI_GUEST_TRIAL_ENABLED=false`. Finish the current release's deferred member walkthrough before enabling new anonymous workload.
2. Review public demo-account shortcuts and the shared-GPU capacity budget.
3. Review the additive migration; rehearse with an isolated development database first. The production database has NOT received0006.
4. Explicit migration commands, when release is approved and the database target is verified:

```powershell
# Read-only schema metadata check:
npm run db:check:guest-trial
# Explicit opt-in write; NEVER runs during build/start:
node --import tsx scripts/apply-guest-trial.ts --apply
```

The standalone guest migration is atomic and repeatable. The existing saved-look migration runner remains separate. Do not use schema push/seed to enable the trial.

5. Deploy reviewed source with the flag still off. Existing homepage links and member access remain as before while off.
6. Privately verify the actual production ingress/proxy chain and that public callers cannot control the selected trusted address. Configure ONE of:
   - `AI_GUEST_TRIAL_TRUSTED_IP_HEADER=cf-connecting-ip` only if that header is authoritatively overwritten by the verified ingress.
   - `AI_GUEST_TRIAL_TRUSTED_IP_HEADER=x-forwarded-for` with verified `AI_GUEST_TRIAL_TRUSTED_PROXY_HOPS`; selection counts from the right. Do not guess the hop count or trust a user-supplied leftmost address.

   Missing/invalid IP configuration blocks new production trials. Local non-production defaults use one shared loopback network identity for tests. Actual Render header behavior remains Needs verification.
7. Reuse existing server-only backend key, consultation-handle secret and registered endpoint configuration. No new API secret or Kaggle notebook is required.
8. Set conservative budgets and enable `AI_GUEST_TRIAL_ENABLED=true` only for a scheduled supervised test.
9. In an unsigned browser, open the homepage trial link; provide an approved test photo, choose a recommendation, generate once, refresh, check the same result, and attempt a second image. Verify the second image is blocked. Check a second already-initialized tab and a registered-client session.
10. Verify Hair/Makeup/Nails and conversational consultation with a small authorized set of real requests. Confirm same-origin checks, key secrecy and trusted IP behavior. Shared busy responses are expected; this change does not add member priority or a GPU queue.

Optional configuration keys are documented in `beautycore/.env.local.example`:
`AI_GUEST_TRIAL_DAYS`, `AI_GUEST_TRIAL_NETWORK_DAILY_LIMIT`, `AI_GUEST_TRIAL_DAILY_LIMIT`, `AI_GUEST_TRIAL_GENERATIONS_DAILY_LIMIT`.

## Disable / rollback

Set `AI_GUEST_TRIAL_ENABLED=false` to stop guest access and remove the homepage trial destination after reload. Leave the additive ledger in place so quota history is not lost. Do not delete current records to simulate a refresh test or weaken member authorization. Normal client consultation, saving/booking and the current Kaggle notebook remain available.

Future options, not included: exact guest-image account handoff, CAPTCHA, verified-person identity, durable GPU idempotency/reconciliation, a priority queue, new registered-user quotas or changes to training/models.


## Release progress, 2026-10-20

Deployment is now authorized. Migration0006 is applied and independently verified. Optional proxy probe added to availability;24guest tests and production build pass. No raw IPs, credentials or client records returned. GitHub publication/operator Render deploy are in progress; guest access is not yet enabled.

After Render is Live, run node scripts/probe-guest-trial.mjs from beautycore. It performs three bounded GETs, including two reserved test-address headers. Enable only when readyForCfConnectingIpConfiguration is true, using AI_GUEST_TRIAL_TRUSTED_IP_HEADER=cf-connecting-ip. Keep AI_GUEST_TRIAL_ENABLED=false until that check. Existing optimized Kaggle notebook needs no update; connection was offline at preflight. [Receipt](../experiments/guest-consultation-trial-release-20261020.json).

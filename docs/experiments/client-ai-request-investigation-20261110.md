# Client AI request investigation, 10 November 2026

Progress: IN PROGRESS. Root cause: UNKNOWN, failed client request evidence pending.

User reports generation works for the operator but fails for a client, including while using Runpod. Supplied screenshot shows the authenticated consultation Direction step with the exact message AI request could not be completed. The user clarified image generation is affected, but the failed endpoint, HTTP status and response remain unavailable.

Verified observations:

* The Next adapter replaces multiple upstream statuses below500 with the same message in beautycore/lib/ai/adapter-core.ts. These include400,401,403,404,409,413,415,422 and some429 responses. Browser transport failures and backend unavailability normally have different messages. Screenshot alone does not establish transport failure.
* Read only query of the existing configured ai_runtime_endpoints primary slot found an active lease, expiring2026-11-10T01:21:09.891Z. The registered endpoint's public /health returned200 and healthy; website /api/health returned200. An active lease and liveness do not establish successful image generation.
* A protected readiness read using the existing local environment credential returned401. Local credential parity with current Render was not established, so this is not proof that Render's credential or the client's credential is wrong. No secret or endpoint was printed.
* Signed in Render application logs available for the last hour show startup readiness, including08:22 and08:50 Manila, without a correlated failed request. Request logs are disabled in this service view. No restart, setting change or deployment performed.
* All23 existing adapter tests pass, covering client authorization, principal bound handles, same origin forwarding, controlled upstream errors, job reads and recognized generation busy responses. These synthetic checks do not reproduce the client's incident.

Source confirmed distinctions requiring the failed response: backend image validation rejects dimensions outside64 to4096px, while ordinary client upload checks MIME and8MB; expired upstream consultation ownership returns404; generation busy admission returns429; provider rate limits can also return429. These are candidates, not proven causes. Do not bypass ownership, loosen image protection, retry unresolved generation or change GPU from this evidence.

Requested the client's failed Request URL, Status Code and Response error from browser Network, excluding cookies and authorization headers. No image, consultation provider call or GPU generation was sent. No application code changed. Next correlate that response and incident time with Runpod facade logs before making a root cause fix.

## Diagnostic correction after client could not supply browser details

The client cannot provide Network details. Implemented a bounded website adapter correction rather than guessing their failure. Exact inspected public photo validation errors, expired consultation responses and consultant rate limits receive actionable messages. Other upstream rejections and transport failures receive a random reference shown in the browser and logged with only a fixed route template, status, original upstream status where available and category. No bodies, image data, user IDs, job/recommendation IDs, signed handles, endpoint addresses or keys are logged. Unknown, oversized and mismatched error details remain suppressed.

Generation busy recognition, ambiguous admission handling, authentication, ownership, request limits and no automatic retry remain unchanged.71 focused tests pass, covering new safe diagnostics and existing adapter, browser flow, jobs, guest trials and generation store. TypeScript passes. This corrects the demonstrated inability to diagnose the generic error, not the unproven client incident. One fresh failure screenshot containing its reference should permit correlation in Render application logs without client developer tools. Deployment verification is recorded separately below when observed.

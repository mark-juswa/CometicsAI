# Review, codex/consultation-chat-ui, 2026-11-16

**Reviewed by** Codex independent reviewer.

**Scope** Six uncommitted implementation and test files against `23b2555a7e3b86acd2458ebeb865b782b37f0308`. The sixth file adds journal removal to the existing account cleanup path.

**Verdict** Approve.

## Summary

The final source addresses the reported recovery and interaction defects. Guest recovery recognizes renewed handles for the same consultation, while API requests use the current server issued handle. The adapter's expired access response enables an explicit fresh start, and a temporary failed state read leaves the guest's manual status check operable.

## Strengths

- A synchronous write records the pending text and its expected position before the turn is sent. Canonical history confirms the message. The real signing helper produces the renewed guest handles used in regression coverage.
- The existing account cleanup routine now erases the journal even after a dashboard refresh. The account lifetime check rejects late writes after sign out. Member restore preserves explicitly empty optional notes when the shared store already owns that field.
- Result hydration gates selection and download until the image arrives. JPEG results retain the correct extension. Service correction and photo disclosure retain the local direction.

## Test coverage

VERIFIED by independent execution of the 32 consultation UI and recovery tests before the final two small cleanup and notes changes. All passed. Source inspection verified those two final changes in `beautycore/lib/ai/generation-storage.ts` and `beautycore/components/consultation.tsx`. The coordinator owns the final production build and complete test rerun.

The browser verification receipt records controlled HTTP responses and emulated mobile sizes. A physical mobile software keyboard remains NEEDS VERIFICATION for AC-9. This review makes no claim about live AI generation, deployment or appointment creation.

# Consultation results in chat release, 22 November 2026

Implementation DONE locally, browser and regression evidence VERIFIED. Deployment IN PROGRESS. Supervisor explicitly approved v4 and requested implementation on the deployed website.

## Change and preserved behavior

The actual existing result subtree moved into the existing transcript in beautycore/components/consultation.tsx. The separate side rail and its collapse toggle are removed. Recommendations include their existing reasons; the active preview and its existing service/complement information use an inline card. Select, Download, Retry, Check status, Continue, guest unlock and Custom actions retain the original handlers and guards. SavedLookActions remains the actual component, with the same selected recommendation key and sourceKind. Booking still saves if needed and opens /booking?look=<saved id>; it never submits an appointment from the chat. Guided preferences, camera/source picker, shared owner, preparation journal and recovery are retained.

Consultation stylesheet rules remain scoped. The transcript is the results scroll owner. Following readers land at the beginning of recommendations, while people reading older messages retain their scroll. Explore My Looks focuses the results without moving the whole page.

## Verification

Artifacts are in I:/HAIR/artifacts/consultation-inline-implementation-20261122. Baseline source hashes are in baseline-hashes.json. Saved look actions, booking form, guest policy, preparation and API adapter source hashes remain unchanged. Source and test diff is limited to consultation.tsx, consultation.css and two existing UI suites.

- 200 relevant tests passed across AI transport, guest controls, recovery, camera, UI, saved image/retry and look information.
- After the scroll correction, all 78 affected consultation and business UI tests passed again.
- TypeScript checking and the final normal Next production build passed using process only dummy local configuration.
- Seven controlled browser journeys against the actual production build passed. Coverage includes all three services, deterministic Nails, one chosen guest preview, retained initial direction, uncommitted turn refresh with no replay, old message scroll, six viewport widths and a short viewport. Member Save/Book remains inside the log and routes to the selected saved look. A saved preview is reused, no appointment POST occurs, and expected generation counts remain three for members and one for guests.
- Dashboard and all three studios had identical sampled computed styles before/after removing consultation CSS rules. Zero browser page errors.
- Independent fresh model code review initially identified the recommendation scroll issue, which was fixed. Final verdict Approve, no remaining findings.

Screenshots and JSON/log receipts preserve local evidence. Images in these browser journeys are controlled one pixel fixtures, not AI quality evidence. Physical keyboards/cameras and live AI generation are not established by these tests. No live account, appointment, quota, model, database, serving runtime or deployment setting changed during verification.

## Publication and deployment

Release base is origin/main78f06a0. The existing consultation checkout contains unrelated Kaggle handoff edits; these are preserved and excluded from publication. Only the four scoped website/test files, spec0021 and this release record are selected for the release commit. No force push or schema/configuration change is required.

Existing Render service srv-db4ftmbbc2fs73blpkr0 serves beautycore-demo.onrender.com from main/beautycore. render.yaml explicitly sets autoDeployTrigger off. Browser automation stopped because it could not confidently determine Chrome's URL, and no preconfigured Render CLI/API credential or repository deployment hook was found. The manual deployment click therefore remains pending, followed by live public asset/page checks. A Git push alone is not a deployment.

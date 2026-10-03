# MOBILE-02A — Product UX/UI evidence

2026-10-03. Baseline `2837e22` on `codex/mobile-01` verified before changes. New branch `codex/mobile-02`. Pre-existing untracked `context/designs/` is preserved and excluded.

**Implementation DONE; local checks VERIFIED; physical Android acceptance BLOCKED, NEEDS VERIFICATION.** Supervisor replied “ill do this later” to the new manual Android checklist. MOBILE-01 remains DONE with its earlier acceptance. The changed MOBILE-02A UI cannot inherit that runtime acceptance. No remote phone taps/navigation/screenshots or security-setting changes were performed. Existing PC API/Expo session is left running for later manual testing.

## Implemented product experience

Home now prioritizes AI Beauty Consultation with a gold bordered card and primary CTA; image cards for Custom Hair, Makeup and Nails are secondary. The normal header gear opens Settings. Health status, API address and explicit recheck moved there, with the existing query/error handling; `/connection` redirects to `/settings`. Generator/worker internals are omitted.

All three studios share compact Photo → Style → Review, a scrolling active stage and a safe-area bottom action. Photo owns gallery/preview/replace/remove; Style owns real catalogs and selection; Review owns summary/Generate preview. Header and focused Android Back handlers move between stages while preserving the draft; pending mock work is canceled on leaving the focused studio. Real Android behavior remains pending manual verification.

Result is a dedicated route with Original/Result controls, selected style and an explicit unchanged mock image. Save/Share are disabled, explained placeholders. Try Another Style keeps photo/style and returns Style; Start Over clears only that feature and returns Photo. Result Back returns the studio without clearing it.

Consultation has local Service → Direction → Your Looks. Actual web preference vocabulary, custom occasion/vibe text, maintenance/intensity/finish, avoids and notes are supported. The brief is editable; compatible Hair/Makeup portraits are retained, switching portrait↔Nails requires a new photo. Your Looks explicitly awaits recommendations, shows the user's brief and offers custom-studio photo handoff. There is no fake chat, recommendation, estimate or generation.

Visual sources inspected: BeautyCore AI CSS/shared components, Client dashboard, Consultation and three studio pages, plus current native theme/components/drafts. Purple/gold values and native serif/system sans remain the same. Bundled service imagery is copied from actual BeautyCore public assets. Editorial copy is adapted for mobile; no external placeholder service or new dependency was introduced. Solid-color local test images below are synthetic fixtures, not generated beauty results or personal photos.

## Before/after visual review

These are **PC Expo web previews**, not newly captured Android screens. Before images were captured from the baseline before source edits; after images were visually inspected. Browser typography differs from Android's native serif. The 1080×2400 image is explicitly a browser pixel-dimension proxy (360×800 at scale 3), not a claim about the phone's logical density.

| Screen | Before | After |
| --- | --- | --- |
| Home | [Before](mobile-02a-assets/before-home-390.png) | [After](mobile-02a-assets/after-home-390.png) |
| Diagnostics → Settings | [Before](mobile-02a-assets/before-connection-390.png) | [After](mobile-02a-assets/after-settings-390.png), [error](mobile-02a-assets/after-settings-error-390.png) |
| Custom Studio | [Old stacked flow](mobile-02a-assets/before-hair-390.png) | [Photo](mobile-02a-assets/after-photo-390.png), [Style](mobile-02a-assets/after-style-390.png), [Review](mobile-02a-assets/after-review-390.png) |
| Result | [MOBILE-01 archived comparison](mobile-01-assets/result-390.png) | [Dedicated result](mobile-02a-assets/after-result-390.png) |
| Consultation | [Before](mobile-02a-assets/before-consultation-390.png) | [Service](mobile-02a-assets/after-consultation-service-390.png), [Direction](mobile-02a-assets/after-consultation-direction-390.png), [Your Looks](mobile-02a-assets/after-consultation-looks-390.png) |
| Smaller widths | — | [Home 320](mobile-02a-assets/after-home-320.png), [Photo 320](mobile-02a-assets/after-photo-320.png), [1080×2400 browser proxy](mobile-02a-assets/after-home-1080x2400-browser-proxy.png) |

Visual audit found no horizontal overflow. Long catalog lists scroll inside the active stage while actions stay visible. Result/brief metadata may scroll on short phones; primary actions do not. Selected borders, contrast, disabled placeholders and explicit preview labels are visible. Screenshot review led to clearer empty-catalog copy and an explicit Refresh styles action. No new UX defect is known from local checks; native findings remain pending.

## Validation

| Check | Result |
| --- | --- |
| `mobile`: `npm run typecheck`, `npm run lint` | Passed on final source |
| `mobile`: `npm test` | 14 passed: existing 8 plus 6 draft/transition/compatibility/isolation tests |
| `npx expo install --check` | Dependencies up to date |
| `npx expo-doctor` | 21/21 passed |
| Android and web exports | Passed on final source; no native dependency/config change |
| Existing Expo session + Edge browser preview | Loaded real changed UI successfully |
| Browser integration | 10 scenario groups passed; Hair 6, Makeup 10, Nails 5 actual API styles; zero page errors; observed requests GET only |
| Layout | 320×640, 360×844, 390×844, 430×844, plus 360×800 proxy; no horizontal overflow, active bottom actions inside viewport |
| Settings and catalogs | Actual health/catalogs; controlled browser transport/API errors, explicit retry/recovery and empty catalog refresh passed |
| Existing backend suite | 408 passed in 81.80s, one existing multipart deprecation warning; CPU/mock configuration |
| Existing BeautyCore AI adapter/client/integration tests | 26 passed, mocked upstreams |
| Bundle private-value scan | See [machine result](mobile-02a-assets/bundle-scan.json), values never printed |
| Protected diff | No changes to backend, frontend, BeautyCore, models/data/datasets/notebooks/training, existing scripts or root/mobile launchers versus baseline |
| Physical Android changed-UI acceptance | PENDING, Supervisor deferred manual checklist |

Initial backend invocation from repository root failed collection because its tests import `app`; the corrected command ran from `backend/` and passed. Initial browser selection assertions expected a DOM attribute not emitted by React Native Web; the corrected check asserts the visible selected checkmark and preserved subsequent review state. Neither required a backend/source fix.

Reproduce while the existing mobile launcher is running:

```powershell
# F:\HAIR
node docs/experiments/mobile-02a-assets/ui-check.cjs
python docs/experiments/mobile-02a-assets/scan-bundles.py
# F:\HAIR\mobile
npm run typecheck
npm run lint
npm test
npx expo install --check
npx expo-doctor
npm run export:android
npm run export:web
# F:\HAIR\backend
python -m pytest tests -q
# F:\HAIR\beautycore
npx tsx --test tests/ai*.test.ts
```

Browser defaults are the existing USB session addresses; optional `MOBILE_TEST_URL` and `MOBILE_TEST_API_URL` change only the test harness. Application API configuration still comes from the unchanged launcher. Do not recapture “before” images after implementing the redesign.

## Native checklist still owed

Supervisor will reload the project manually in Expo Go on the already accepted Xiaomi Android 12 device and verify:

1. Consultation primary/Home service hierarchy; gear/Settings connection and recheck.
2. Consultation photo, preferences, brief, Back preservation and honest unconnected looks.
3. Each Hair/Makeup/Nails gallery choose/cancel/replace/remove, three stages, style scrolling, hardware Back and photo/style preservation.
4. Review, unchanged mock comparison, Original/Result, Try Another Style retaining photo and Start Over reset.
5. Phone-width content, bottom actions and Back between screens.

No real GPU request is required or authorized in this phase. MOBILE-02 authenticated real generation remains NOT STARTED. Do not report MOBILE_02A_READY until this changed-UI manual gate passes.

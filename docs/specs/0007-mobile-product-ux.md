# MOBILE-02A — BeautyCore mobile product experience

**Decision: CONFIRMED** by Supervisor brief, 2026-10-03. **Status**: IN PROGRESS at combined MOBILE-02B native acceptance; implementation DONE, local checks VERIFIED.

## Summary

Bring the accepted native shell into the BeautyCore product hierarchy before real AI is connected. Consultation leads Home, custom studios move through focused stages, and results receive their own screen. Keep the existing visual system, local photo handling and read only development API.

## Context

MOBILE-01 is accepted on a physical Xiaomi Android phone. This additive UI slice precedes authenticated real generation. Continue the existing Expo SDK 57 / React Native / TypeScript / Expo Router, TanStack Query and in-memory Zustand architecture. No new native dependencies, API mutations, connectivity architecture or backend changes are needed. Implementation skills: architect and develop.

## Decision and rationale

Documenting the Supervisor's already supplied UX decision. Shared native flow components and per-feature drafts replace repeated vertical controls, keeping interaction and reset rules consistent. The existing backend boundary and launcher are sufficient for this UI-only phase. Optional independent spec cross-check was offered; Supervisor selected Skip. No new architecture approval is owed.

## Product source and composition

Actual sources: `beautycore/app/ai-studio.css`, `beautycore/components/ai-studio.tsx`, Client dashboard, Consultation and three studios. Retain Andrea's clinic branding, aubergine layered cards, gold emphasis/selected borders, editorial serif headings and native sans controls. Token values remain in `mobile/constants/theme.ts`.

- Home: clinic eyebrow and short editorial introduction; dominant AI Beauty Consultation card, Service / Direction / Your Looks journey and primary Start Consultation; secondary Custom Services with Hair, Makeup and Nails cards. Header gear opens Settings. No diagnostics on Home.
- Settings: compact title, connection status/recheck group, restrained configured application API address and local-photo/privacy information. Relocate the existing health query; omit generator internals. Old connection route redirects here.
- Custom studios: compact Photo / Style / Review progress beneath native header, single active stage, scrolling content above a safe-area bottom action. Photo stage owns gallery and compact preview; Style owns real API choices, loading/error/retry/empty; Review owns photo/style summary and explicitly labeled mock Generate preview. Preserve feature-specific portrait/hand guidance and nail swatches.
- Result: dedicated route, Original / Result comparison tabs, contained image, selected style, explicit unchanged mock notice, disabled Save / Share placeholders, Try Another Style and Start Over. No fabricated generated image.
- Consultation: flagship Service / Direction / Your Looks progress. Service selects Hair/Makeup/Nails and local portrait/hand photo. Direction captures actual web occasion/vibe and service-specific maintenance/intensity/finish choices, optional avoids/notes. Your Looks shows the user's brief and an honest unconnected recommendations state; no fake recommendations, chat, estimates or generation. Offer a custom-studio handoff using the existing photo.

## State and navigation

Studio drafts remain feature-local, in memory, with photo, style ID, preview style and stage. Photo replacement/removal invalidates mock preview; removal returns to Photo. Style selection invalidates preview. Forward transitions require photo then photo plus style. Previous stage preserves both. Header and Android Back traverse Review → Style → Photo → previous route. Unmounting/focus changes cancel pending preview timers. Try Another Style clears preview, retains photo/style and returns Style; Start Over resets only that feature and returns Photo. Result Back returns Review without clearing work. Gallery cancellation preserves the draft.

Consultation has a separate temporary draft and no server state. Hair/Makeup may reuse a portrait; switching between portrait and Nails clears an incompatible photo, with explanatory copy. Preferences are feature-specific; changing service clears only its service preference. Back preserves the brief. Forward requires service/photo before Direction; Direction fields are optional. No recommendation client is introduced.

## Feature design and value sourcing

| Displayed or produced value | Source |
| --- | --- |
| Brand colors, type, borders, spacing | Actual web AI CSS and existing native theme tokens |
| Service imagery | Bundled copies of BeautyCore public hairextension.jpg, makeup.png, nails.jpg |
| Service names, portrait/hand guidance | Actual web service cards and existing native feature presentation |
| Catalog names, descriptions, IDs and status | Existing typed FastAPI GET catalogs |
| Connection status and errors | Existing typed health query and ApiError parser |
| Application API origin | Existing process-only EXPO_PUBLIC_API_BASE_URL configuration |
| Studio stage, selected style, original/mock image | Temporary feature draft, selected gallery URI, unchanged same URI for mock |
| Consultation preference choices and limits | Actual web Direction fields: occasion/vibe 80, avoids 160, notes 500 characters |
| Consultation brief | User's local selections and text, absent values labeled No preference |
| Pending recommendations and Save/Share copy | Explicit scope limitation, no server result or invented AI data |

Critical scenarios: forward without photo/style is blocked (AC-3/4); canceled picker and Back preserve draft (AC-4); Try Another retains photo and Start Over isolates reset (AC-5); service switching keeps compatible portrait and clears incompatible hand/portrait (AC-6); unavailable/empty catalog disables Review and permits explicit retry (AC-2/3); scrollable stage keeps safe-area action visible at narrow widths (AC-7); all requests remain GET and no generation (AC-10).

## Requirements and acceptance criteria

- AC-1: Home makes Consultation primary, custom services secondary; normal header Settings entry; no health/debug controls on Home.
- AC-2: Settings retains health, explicit recheck, readable errors and recovery; no secrets or worker details.
- AC-3: All three studios use shared Photo → Style → Review and fixed bottom actions; catalog data comes from existing GET API; gates, errors and empty states are clear.
- AC-4: Gallery choose/cancel/replace/remove, stage Back and navigation preserve/reset state as specified; no photo persistence/upload.
- AC-5: Dedicated mock comparison, selected style, Save/Share placeholders, Try Another Style and Start Over work as specified.
- AC-6: Consultation presents the three web concepts, actual preference vocabulary and editable local brief, without fake AI or recommendations.
- AC-7: Phone-width touch/layout audit at 320, 360, 390 and 430 points plus the accepted physical phone; no horizontal overflow or hidden bottom controls.
- AC-8: TypeScript, lint, mobile tests, Expo dependency/doctor checks and Android export pass. Record browser before/after screenshots and reproducible GET-only interaction checks.
- AC-9: Supervisor manually verifies physical Android flows, Back, photo preservation, style scrolling, result actions, Settings and Consultation. No remote taps/navigation/new phone captures due the existing explicit restriction. Browser exports alone cannot satisfy this gate.
- AC-10: Protected backend, web, launchers, AI models/settings/prompts/Kaggle/Gemini/datasets remain unchanged; no GPU call or new private value in bundle.

## Build plan

1. Capture baseline browser previews, implement shared flow shell/progress/back behavior and draft transitions (AC-3/4/7/8).
2. Compose Home/Settings, studio stages/result and Consultation local shell within existing tokens (AC-1/2/3/5/6/7).
3. Run state/API tests, typecheck/lint, real-catalog browser flows and responsive visual audit; capture after screenshots (AC-2/3/4/5/6/7/8/10).
4. Expo checks/Android export and manual native acceptance, then evidence/context/scope and commit (AC-8/9/10).

## Consequences and next gate

Local previews remain intentionally unchanged images. Save/Share and Consultation recommendations await real output. MOBILE-02 real generation/authentication is a separate authorized phase, never started automatically. No second design system or desktop DOM reuse.

## Verification

Evidence is recorded in [mobile-02a.md](../experiments/mobile-02a.md). TypeScript/lint, 14 mobile tests, Expo compatibility/Doctor, Android/web exports and 10 browser scenario groups passed. Existing backend 408 and BeautyCore 26 regressions passed; protected sources are unchanged. Native status remains NEEDS VERIFICATION: Supervisor replied “ill do this later” to the new manual checklist. MOBILE-01 acceptance remains complete and does not prove this changed UI.

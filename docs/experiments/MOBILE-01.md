# MOBILE-00 / MOBILE-01 evidence

## Completion, 2026-10-03

**MOBILE-01 DONE, MOBILE_01_READY.** The previously pending native gate is closed on one physical Xiaomi Android 12 phone with Expo Go 57. Ordinary mobile launcher USB reverse, native loading, connected/mock health and catalog transport were observed. Supervisor performed and confirmed gallery lifecycle, navigation/back, mock comparison, phone layout, unavailable API error/recovery and Consultation overview manually after prohibiting remote taps for security. No app/backend/model/launcher source changed and no GPU generation ran. [Native evidence and acceptance limits](mobile-native-android.md). Earlier dated checkpoint results below remain historical evidence, including the original no-device block.

Date: 2026-10-02. Implementation: VERIFIED locally. Android acceptance: NEEDS VERIFICATION. Progress: BLOCKED only at native device acceptance; Supervisor explicitly chose to leave it pending.

## Configuration and protection

Starting commit `e05b832`, branch `codex/beautycore-original-ai-ui`; only pre-existing untracked `context/designs/` was present. New branch: `codex/mobile-01`. Those design files are preserved and excluded from the mobile commit. Official `create-expo-app@5.0.0` blank TypeScript initializer selected Expo `57.0.26` / React Native `0.86.3`; Expo Router `57.0.24`. Expo-compatible animation peers pinned to Reanimated `4.5.1` / Worklets `0.10.1` after npm's default transitive resolution produced a peer mismatch. `npm ls` then showed no invalid dependency. No image manipulation dependency remains.

The separate test API used system Python with `GENERATION_ENGINE=mock`, `MAKEUP_GENERATION_ENGINE=mock`, `NAILS_PREVIEW_MODE=mock`, `CONSULTATION_PROVIDER=deterministic`, and preview-only `FRONTEND_ORIGINS`. It bound `127.0.0.1:8001`. Expo started on 8091 with process-only `EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8001`; no local address is hardcoded in application code or committed env configuration. Working server `.env`, root launchers and Kaggle workflow were not changed.

The existing backend `.venv` lacked pytest; validation used the inspected system Python, which is the existing demo interpreter. No backend dependency or environment was installed/changed.

## Results

| Check | Result |
| --- | --- |
| `npm run typecheck` | VERIFIED, passed |
| `npm run lint` | VERIFIED, passed |
| `npm test` | VERIFIED, 8 contract/state tests passed |
| `npx expo install --check` | VERIFIED, dependencies up to date |
| `npx expo-doctor` after final dependency pins | VERIFIED, 21/21 checks passed |
| `npm run export:android` | VERIFIED, 1,334 modules, Hermes bundle exported; bundling does not prove device load |
| `npm run export:web` | VERIFIED, 873 modules exported |
| `npx expo start --web --port 8091` | VERIFIED, Metro started and app loaded in Edge |
| Existing backend `python -m pytest tests -q` | VERIFIED, 408 passed, one existing multipart deprecation warning, 95.24 seconds |
| BeautyCore `npm run typecheck` | VERIFIED, passed |
| BeautyCore `npx tsx --test tests/ai*.test.ts` | VERIFIED, 26 passed |
| Browser UI journey | VERIFIED, 11 checks, zero page errors; health/catalog requests were actual FastAPI GETs |
| Secrets and protected path inspection | VERIFIED, current 13 long private config values absent from Android/web bundles; zero forbidden server config tokens in app source; zero protected path changes versus `e05b832` |
| Android native environment load/gallery/navigation/network | NEEDS VERIFICATION; SDK installed, `adb devices` empty and `emulator -list-avds` empty |

The UI check exercises Hair, Makeup and Nails at 320, 360, 390 and 430 px widths; selection, preview, replace, remove, reset, unchanged original/mock comparison, sample failure, Consultation overview, health and injected catalog HTTP 503 with explicit retry. All observed application API requests are GET, with no generation/upload/consultation/worker calls. Actual development catalogs returned 6 Hair, 10 Makeup and 5 Nails rows in this mock configuration; these are observed configuration-specific counts, not frozen catalog assumptions or claims about deployed worker support.

The first browser harness run failed at its final retry assertion because the test hardcoded a differently capitalized display label. It recorded zero page errors and all earlier journey checks. The corrected harness derives the label from the actual API catalog and passes. The failure record is retained as provenance. Final sample-failure copy does not assume that a photo/style remains selected after a reset.

## Reproducible evidence

- [Integration contracts](../guides/mobile-00-contracts.md)
- [UI runner](mobile-01-assets/ui-check.cjs), [final results and observed requests](mobile-01-assets/ui-results.json)
- [Protection runner](mobile-01-assets/protection-check.py), [bundle hashes and inspection results](mobile-01-assets/protection-results.json)
- [Recorded validation output excerpts](mobile-01-assets/validation-excerpts.txt), [Android export log](mobile-01-assets/export-android.log), [web export log](mobile-01-assets/export-web.log), [TypeScript log](mobile-01-assets/typecheck.log), [lint log](mobile-01-assets/lint.log)
- [Home](mobile-01-assets/home-390.png), [mock comparison](mobile-01-assets/result-390.png), [Nails and sample failure](mobile-01-assets/nails-390.png)

UI reproduction uses the existing `frontend/node_modules/@playwright/test` and installed Edge. Start the separate CPU-only FastAPI and Expo web processes as described above; create the two synthetic 256×320 PNG fixtures under ignored `.tmp/mobile-01/` (`portrait.png`, `replacement.png`) before `node docs/experiments/mobile-01-assets/ui-check.cjs`. These are colored test fixtures, not generated AI output. Run `python docs/experiments/mobile-01-assets/protection-check.py` after both exports; it compares private config internally and never prints secret values.

## Remaining gate

Connect an Android device or provision an emulator, load the SDK-compatible Expo environment, set a reachable development API origin, and verify native gallery selection/cancel/replace/remove/reset, Android back/navigation, real health/catalog requests, network failure, portrait/hand preview and phone-width layout. No GPU generation belongs to this gate. Physical LAN reachability, Android cleartext policy and native gallery lifecycle are not proven by web tests. Until then the correct completion marker is `MOBILE_01_BLOCKED`.

# 0006. Additive mobile studio foundation

**Date**: 2026-10-02
**Decision**: CONFIRMED by the Supervisor's MOBILE-00/MOBILE-01 instruction and API-boundary answer
**Status**: DONE (2026-10-03, physical Android acceptance observed and confirmed manually by the Supervisor)

## Summary

Create the mobile application in `mobile/` using Expo, React Native, TypeScript and Expo Router. Reuse the existing application API and beauty studio design. MOBILE-01 connects only development health and catalogs and shows an unchanged local mock photo for results.

## Context

The active web frontend is BeautyCore with an authenticated application adapter to private FastAPI. The Supervisor explicitly selected direct existing FastAPI for development MOBILE-01, with BeautyCore authentication deferred to MOBILE-02. The Kaggle worker, foundation, LoRAs, style prompts, model settings, Nails processing and recommendations remain protected.

This records the Supervisor's supplied design rather than proposing a new product or inference architecture. The focused inspected contracts are in [MOBILE-00](../guides/mobile-00-contracts.md).

## Requirements

- **AC-1**: Add an isolated `mobile/` app and safe branch without changing working web/backend inference behavior.
- **AC-2**: Application shell, navigation and service selection reproduce existing studio colors, typography hierarchy, spacing, cards and buttons through native equivalents.
- **AC-3**: Gallery selection previews a local JPEG/PNG photo, supports replacement/removal/reset, and clears stale mock results without uploading or persisting photos.
- **AC-4**: One typed API layer uses configurable `EXPO_PUBLIC_API_BASE_URL`, verifies response shapes, checks health and loads all three existing feature catalogs. UI files contain no backend route strings.
- **AC-5**: Loading, empty, API error, explicit retry and mock result states are clear. No automatic request retry or expensive generation in this slice.
- **AC-6**: Consultation remains an overview of Service, Direction and Your Looks. Complete Consultation and camera capture are deferred.
- **AC-7**: TypeScript, lint, Expo startup/bundling and relevant regression checks pass; no server secret enters the bundle.
- **AC-8**: Android Expo environment loads, native navigation and gallery selection/preview/reset work, configured health/catalog GETs work and no horizontal overflow occurs at common phone widths. Browser evidence cannot close this criterion.

## Decision and rationale

Use the explicitly requested stack, with TanStack Query for server reads and Zustand for small temporary per-service drafts. Keeping application requests in one read-only API layer makes the no-generation boundary enforceable. Reuse existing API catalogs and design sources to avoid duplicating model or product logic. Direct development FastAPI was selected over implementing native BeautyCore identity in MOBILE-01; it is not approval to expose unauthenticated generation publicly.

## Feature design

| Value or action | Source |
| --- | --- |
| Brand, colors, panel hierarchy, typography and service copy | Existing BeautyCore AI studio and original feature screens, translated into `mobile/constants/theme.ts` and service presentation modules |
| Hair service ID | Existing registry ID `hairstyle`, displayed as Hairstyle |
| Service availability/description | GET `/features`; local route presentation retains the web service identities |
| Styles and status labels | GET `/features/{hairstyle,makeup,nails}/styles`, never hardcoded/mock catalog fallback |
| API origin | `EXPO_PUBLIC_API_BASE_URL`, complete HTTP(S) origin without credentials/path/query/fragment; no fallback |
| Connectivity | GET `/health`; status `ok` and generator string, not GPU readiness |
| Photo URI, name, MIME, size, dimensions | Expo system gallery selection and local file metadata, checked against existing upload limits |
| Mock result image | Same local photo URI, explicitly labeled unchanged; no synthetic transformation or recommendation |
| Result selection | Current style from live catalog and in-memory per-feature draft |
| Errors | Safe parsed FastAPI/adapter messages, controlled network/timeout/invalid-response errors |
| Consultation stages | Existing Service, Direction, Your Looks presentation; no session creation in this phase |

Routes: home, Hair, Makeup, Nails, Consultation overview, API connection and mock comparison. Each studio uses hero → photo panel → catalog panel → preview action. Read requests have a 12-second deadline, no automatic retries and explicit retry controls. Photos/style changes invalidate the previous mock result. Drafts are feature scoped, with no persistence middleware. Read response validation rejects unsupported feature IDs or incomplete catalog rows.

The app directory structure follows the Supervisor's requested `app/`, `components/`, `features/{hair,makeup,nails,consultation}/`, `lib/{api,config,image}/`, `store/`, `constants/`, `assets/`. Browser File inputs, object URLs, DOM dialogs and Next.js components are replaced by native equivalents. Gallery-only configuration blocks camera and microphone permissions.

Data model: each of the three temporary drafts holds nullable `photo`, `styleId` and `previewStyle`. Photo contains local URI, display name, validated MIME, width, height and byte size. PreviewStyle is the live catalog row used for the unchanged mock comparison. Setting photo/style clears previewStyle; reset clears that service draft only. No schema, database, migration or durable device storage is introduced.

Critical scenarios: replace/remove/reset after preview and feature isolation (AC-3); healthy, missing-config, network, timed-out, malformed and HTTP-error API reads with explicit recovery (AC-4, AC-5); three real catalog journeys and mock comparison with zero mutation calls (AC-2, AC-3, AC-5, AC-6); final exports/private-value scan and protected-path comparison (AC-1, AC-7); native device loading, picker lifecycle, Android back and connectivity (AC-8, completed on one physical phone through observed load/API and Supervisor manual interaction evidence).

Security: development FastAPI is unauthenticated; keep it on a trusted development network. Existing BeautyCore Client identity/roles and signed consultation ownership remain authoritative for the later authenticated generation phase. Only the application API origin is public client configuration. No worker or server secrets are imported.

## Build plan and acceptance

- [x] Inspect relevant actual sources and record contracts before mobile integration (AC-1, AC-4).
- [x] Preserve starting Git state and create `codex/mobile-01`; scaffold the isolated Expo project (AC-1, AC-7).
- [x] Connect read-only API, health and three catalogs with controlled failures (AC-4, AC-5).
- [x] Build native shell, navigation, photo state and mock result journey using existing design (AC-2, AC-3, AC-5, AC-6).
- [x] Verify TypeScript, lint, contract tests, Expo startup, Android/web exports, phone-width browser checks, protected paths and secret exclusion (AC-7; supporting evidence for AC-2 through AC-6).
- [x] Complete native Android device acceptance (AC-8). On 2026-10-03, physical Xiaomi Android 12/Expo Go 57 loaded through ordinary USB launcher reverse and reached health/catalogs. Supervisor manually confirmed gallery lifecycle, mock preview, Back, width, API error/recovery and Consultation overview. Remote phone interaction is prohibited by Supervisor preference. [Native evidence](../experiments/mobile-native-android.md).

## Consequences and follow-up

### Windows mobile launcher addendum, 2026-10-03

**Decision: CONFIRMED**, Supervisor explicitly requests automatic development connectivity before MOBILE-02. `START_MOBILE.bat` and `STOP_MOBILE.bat` are additive entry points backed by `scripts/mobile_launch.py` and a read-only PowerShell network inventory. Existing root launchers and all application/model code remain protected.

Value sources: authorized devices come from SDK/PATH ADB `devices -l`; loopback comes from verified reverse mappings for API 8001 and Metro 8081. LAN IPv4 comes from a connected physical default-route interface with a Private/domain Windows profile, RFC1918 address and lowest route-plus-interface metric. Virtual/VPN/disconnected/Public interfaces and ambiguous priorities/sources are rejected. SDK lookup uses configured environment/PATH or the standard per-user installation. No developer address is stored in source.

Startup binds a separate existing FastAPI instance to `0.0.0.0:8001` with process-only mock/deterministic engines, verifies its mock health, then starts normal Expo Go mode on 8081 with the chosen advertised host. Expo receives only whitelisted OS/tooling variables and the process-only API origin, with dotenv loading disabled and Metro cache cleared. No env file, server configuration, firewall/profile or tunnel is changed. No public Internet exposure is authorized. Ordinary startup requires USB authorization or a trusted Windows Private/domain LAN; marking an actually trusted network Private may be a one-time OS setup.

Runtime data: ignored `.tmp/mobile/control.json` holds a random session identity, controller token/loopback port and non-secret connection metadata; `launch.lock` serializes startup. Stop verifies controller identity before requesting shutdown. A kill-on-close Windows job owns only newly spawned suspended children, assigned before they can spawn descendants. Stored PIDs never authorize termination. ADB cleanup removes only newly created, unchanged reverse mappings. Duplicate start retains a live session; stale state never grants process authority.

Launcher acceptance: unrelated occupied ports, no transport, unhealthy FastAPI and failed Expo must fail clearly, without restart loops or killing unrelated processes. Confirm real CPU API/Expo start and owned stop, native job child/grandchild isolation, route/ADB failure cases and unchanged env files. A controlled resolver fixture may validate process startup when no phone/trusted route exists, but cannot close AC-8. Native Android acceptance remains an independent required gate.

MOBILE-01 is implemented, locally verified and accepted on one physical Android phone. Report `MOBILE_01_READY` from the observed and explicit Supervisor manual acceptance, without implying testing on all phones. Ordinary USB debugging is sufficient; further remote phone input/navigation/capture remains prohibited. Existing spec 0005 and its web privacy boundary remain valid; the development exception is limited to this mobile slice. No major inference architectural change or drift was found.

MOBILE-02 first integrates the existing BeautyCore authenticated Client/session boundary and native Origin behavior. Then implement typed native multipart manual generation through the existing application adapter, explicit serialized user actions, elapsed loading, safe failure/ambiguity handling, original/generated comparison and native save/share. Validate one authorized result for each feature using unchanged existing engines, including Nails hybrid routing. Full Consultation and camera are separate future scope.

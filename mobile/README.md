# HAIR CAPSTONE mobile

MOBILE-01 uses Expo SDK 57, React Native, TypeScript and Expo Router. It is additive and uses the existing FastAPI application API for development, as explicitly approved. It never calls Kaggle. Native Android acceptance is recorded separately from browser checks in `docs/experiments/MOBILE-01.md`.

## Start

```powershell
Set-Location F:\HAIR\mobile
npm ci
Copy-Item .env.example .env.local
# Edit .env.local and set EXPO_PUBLIC_API_BASE_URL to the reachable application API origin.
npm start
```

Open the project in an Expo Go environment compatible with SDK 57, or use a matching Android development build. `npm run android` requires Android tooling or a connected device. There is no bundled backend address. Restart Expo after changing environment configuration. Only `EXPO_PUBLIC_API_BASE_URL` belongs in the public client configuration. No database, Gemini, session, adapter or Kaggle credentials belong here.

## Device connectivity

Keep the working root launcher and its private FastAPI binding unchanged. For mobile development, run a separate instance of the same FastAPI source on an unused port (for example 8001). Start the backend from `F:\HAIR\backend` with the inspected system Python environment (the existing backend `.venv` lacks pytest and is not the verified demo interpreter):

```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

This reuses the existing backend configuration. MOBILE-01 sends only health/catalog GET requests even if that configuration has real engines. For an entirely CPU-only development instance, set `GENERATION_ENGINE=mock`, `MAKEUP_GENERATION_ENGINE=mock`, `NAILS_PREVIEW_MODE=mock`, `CONSULTATION_PROVIDER=deterministic` in that terminal before starting it. Do not edit the working server `.env` or start the Kaggle workflow for this phase.

| Client | `.env.local` API example | Connection |
| --- | --- | --- |
| Android emulator | `EXPO_PUBLIC_API_BASE_URL=http://10.0.2.2:8001` | Standard Android emulator alias reaches the host PC |
| Physical Android on same LAN | `EXPO_PUBLIC_API_BASE_URL=http://<PC-LAN-IP>:8001` | Same Wi-Fi; use the PC IPv4 from `ipconfig`; server binds `0.0.0.0` |
| Expo browser preview | `EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8001` | Separate dev backend permits the actual preview origin in `FRONTEND_ORIGINS` |

Allow the selected API port and Expo's Metro port (normally 8081) through Windows Firewall only on your trusted private network if needed. A Metro tunnel carries the app bundle, not the backend API. Android emulator addresses are not reachable from physical phones. Public deployments need HTTPS and BeautyCore authentication, deferred to MOBILE-02. Do not expose the unauthenticated development FastAPI publicly. A standalone Android build may need a development-only cleartext policy for local HTTP; Expo Go transport and a release HTTPS build must each be verified on the target device.

## Scope and structure

`app/` contains service navigation, connectivity, consultation overview and mock comparison. `components/` has native studio panels, buttons, gallery picker and catalog cards. `features/{hair,makeup,nails,consultation}/` retains service presentation and stages. `lib/api/` owns all routes, runtime validation and Query hooks. `lib/config/` owns public origin validation. `lib/image/` validates JPEG/PNG gallery selections against existing limits. `store/` keeps per-service drafts in memory. `constants/` translates existing studio tokens; `assets/` contains the official scaffold icons.

Catalogs never use mock fallback. Failed API requests show an explicit retry action; automatic retries are disabled. Photos are local URI references, never persisted by the app or uploaded in MOBILE-01. The OS picker may create temporary cache files. Replace/remove/reset releases app state references and invalidates mock results. No camera permission or capture, complete Consultation, download action, authentication or real generation is implemented in this phase.

## Validation

```powershell
npm run typecheck
npm run lint
npm test
npx expo install --check
npm run export:android
npm run export:web
```

On Android: load, visit all services, check configured API connection, verify real catalogs, choose/cancel/replace/remove a gallery photo, select a style, view unchanged mock comparison, navigate back, reset, test unavailable API and small-width layouts. Browser validation supports UI checks but does not prove native gallery or Android runtime acceptance.

Contracts: [MOBILE-00 inspection](../docs/guides/mobile-00-contracts.md). Reference APIs: [Expo Router setup](https://docs.expo.dev/router/installation/), [SDK 57 ImagePicker](https://docs.expo.dev/versions/v57.0.0/sdk/imagepicker/).

## MOBILE-02: Real Feature Generation

First connect the existing BeautyCore Client identity/session boundary with a tested native session and Origin strategy, preserving fresh roles and user-bound consultation handles. Then add one typed native multipart generation method (`image`, `style_id`) through the existing application adapter, never Kaggle. Implement explicit single-request generation, truthful elapsed loading, controlled errors and manual retry; reconcile ambiguous response loss without blindly duplicating work. Display the returned image with original comparison and native save/share. Validate one authorized Hair, Makeup and Nails real result, preserving Nails hybrid paths and all existing settings/prompts. Full conversational Consultation and camera capture stay separate future slices unless explicitly added to scope.

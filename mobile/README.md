# HAIR CAPSTONE mobile

MOBILE-01 uses Expo SDK 57, React Native, TypeScript and Expo Router. It is additive and uses the existing FastAPI application API for development, as explicitly approved. It never calls Kaggle. Native Android acceptance is recorded separately from browser checks in `docs/experiments/MOBILE-01.md`.

## Normal Windows startup

```powershell
Set-Location F:\HAIR
.\START_MOBILE.bat
```

Connect an Android phone by USB and authorize this PC for debugging, or put the phone and PC on the same trusted Wi-Fi. Run `START_MOBILE.bat`, wait for `MOBILE_DEV_RUNNING`, then open the printed QR/address in Expo Go compatible with SDK 57. USB mode uses `exp://127.0.0.1:8081`; the address reaches the PC through ADB. The launcher window stays open with Expo's normal console. Ctrl+C or `F:\HAIR\STOP_MOBILE.bat` closes only that mobile session. The working root `START.bat` and `STOP.bat` remain separate.

No `.env.local` creation or editing, `ipconfig`, fixed LAN address or persistent environment change is needed. The launcher supplies `EXPO_PUBLIC_API_BASE_URL` to its Expo child only and sets `EXPO_NO_DOTENV=1`, so stale mobile env files cannot override the address or supply other public values. Only the non-secret application API origin is public. No database, Gemini, session, adapter or Kaggle credentials are supplied to Expo.

One-time prerequisites: install Node.js, the existing backend's Python dependencies, and run `npm ci` in `F:\HAIR\mobile`. Python on PATH must be the interpreter with those backend dependencies. For USB, install Android SDK Platform Tools and set `ANDROID_HOME` or `ANDROID_SDK_ROOT`, or put `adb.exe` on PATH. The standard `%LOCALAPPDATA%\Android\Sdk` location is also detected. No administrator window is ordinarily required. A matching Android development build remains an option for native development.

## Device connectivity

The launcher starts a separate instance of the unchanged FastAPI source on `0.0.0.0:8001`. Its process uses `GENERATION_ENGINE=mock`, `MAKEUP_GENERATION_ENGINE=mock`, `NAILS_PREVIEW_MODE=mock`, `CONSULTATION_PROVIDER=deterministic`. Existing backend env files, the private working backend and the Kaggle workflow are untouched. It checks `/health` for the mock engine before starting Expo on port 8081. MOBILE-01 continues to send only health/catalog GET requests.

| Mode | Automatic API origin | Connection |
| --- | --- | --- |
| Authorized ADB Android device, physical or emulator | `http://127.0.0.1:8001` | Reverse API 8001 and Expo 8081; Wi-Fi is unnecessary |
| Physical Android on trusted LAN | `http://<resolved-IPv4>:8001` | Lowest effective-metric usable physical IPv4 default route; Expo advertises that same address |
| Expo browser preview | Same origin as the chosen mode | Separate dev backend allows that preview origin in its process-only CORS configuration |

ADB discovery ignores unauthorized/offline devices and tries authorized devices in the order reported by ADB. The console identifies the selected device. Reverse setup uses `--no-rebind`, verifies both mappings, preserves an existing identical mapping and refuses to overwrite a different target. Failed setup falls back to another authorized device or LAN. Stop removes only mappings created by this session that still have their original target; it never uses `--remove-all` or `kill-server`. If the phone disconnects before cleanup, an identical leftover mapping can be reused on the next start.

LAN selection combines route and interface metrics and excludes disconnected, VPN/virtual, Hyper-V/Docker, link-local and public-address adapters. It requires a physical default route with an RFC1918 IPv4 address and a Windows Private or DomainAuthenticated network profile. Equal-priority usable routes or ambiguous source addresses fail clearly. If your trusted home network is marked Public, you can mark that network Private once in Windows Settings > Network & internet, or use USB. The launcher does not change profiles, firewall rules, router forwarding or start a tunnel. Keep this unauthenticated API on the trusted development network. Windows Firewall may require a one-time Private-network allowance for Python/Node and ports 8001/8081. Do not enable a Public-network allowance or Internet port forwarding.

Startup rejects occupied ports 8001/8081 without killing their owners, fails if neither transport works, and closes its own session if FastAPI health or Expo startup fails. It performs bounded readiness polling without restarting either process. Logs and authenticated ownership data are ignored local files under `.tmp/mobile/`; backend errors are in `backend.log`. Repeated Start keeps the existing session; Stop then Start resolves a changed connection. Stop never reconstructs ownership from stored PIDs. Closing the launcher window also closes its Windows job and child processes; a subsequent start checks free ports before removing stale ownership data.

For advanced manual launches, the app still supports `EXPO_PUBLIC_API_BASE_URL` supplied by the caller, including the standard emulator host alias `http://10.0.2.2:8001`. This is unnecessary with `START_MOBILE.bat`. Public deployment HTTPS, native BeautyCore authentication and standalone-build local HTTP policy remain MOBILE-02/device verification concerns.

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
# From F:\HAIR, launcher-only regression checks:
python -m unittest discover -s tests -p test_mobile_launcher.py -v
```

On Android: load, visit all services, check configured API connection, verify real catalogs, choose/cancel/replace/remove a gallery photo, select a style, view unchanged mock comparison, navigate back, reset, test unavailable API and small-width layouts. Browser validation supports UI checks but does not prove native gallery or Android runtime acceptance.

Contracts: [MOBILE-00 inspection](../docs/guides/mobile-00-contracts.md). Reference APIs: [Expo Router setup](https://docs.expo.dev/router/installation/), [SDK 57 ImagePicker](https://docs.expo.dev/versions/v57.0.0/sdk/imagepicker/).

Launcher evidence: [automatic connection and owned shutdown](../docs/experiments/mobile-launcher.md). Runtime tests using a controlled resolver fixture cannot prove physical USB transport, LAN phone access or native Android acceptance.

## MOBILE-02: Real Feature Generation

First connect the existing BeautyCore Client identity/session boundary with a tested native session and Origin strategy, preserving fresh roles and user-bound consultation handles. Then add one typed native multipart generation method (`image`, `style_id`) through the existing application adapter, never Kaggle. Implement explicit single-request generation, truthful elapsed loading, controlled errors and manual retry; reconcile ambiguous response loss without blindly duplicating work. Display the returned image with original comparison and native save/share. Validate one authorized Hair, Makeup and Nails real result, preserving Nails hybrid paths and all existing settings/prompts. Full conversational Consultation and camera capture stay separate future slices unless explicitly added to scope.

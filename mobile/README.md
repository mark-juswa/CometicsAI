# HAIR CAPSTONE mobile

MOBILE-02B retains the accepted MOBILE-01 foundation and MOBILE-02A product UI. It adds existing BeautyCore Client authentication, real feature generation and native result actions. Real Android acceptance is recorded separately from local tests in [MOBILE-02B evidence](../docs/experiments/mobile-02b.md). Earlier [MOBILE-01 acceptance](../docs/experiments/mobile-native-android.md) and [MOBILE-02A screenshots](../docs/experiments/mobile-02a.md) remain historical evidence.

## Normal Windows startup

With the existing unified Kaggle session ready:

```powershell
Set-Location F:\HAIR
.\START.bat
# Wait for BEAUTYCORE CAPSTONE READY, then in another terminal:
.\START_MOBILE.bat
```

Connect and authorize an Android phone by USB, wait for `MOBILE_DEV_RUNNING`, and open `exp://127.0.0.1:8081` yourself in SDK 57 Expo Go. Sign in with an existing BeautyCore Client account. No `.env.local` editing, IP discovery or persistent environment changes are needed. The mobile launcher verifies existing BeautyCore on loopback 3000 and anonymous AI denial, reverses 3000/8081, and starts only Expo. Its process receives `EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:3000` and `EXPO_NO_DOTENV=1`. No server secret is supplied to Expo.

`STOP_MOBILE.bat` or Ctrl+C stops only its owned Expo process and newly created reverse mappings. It never stops the existing BeautyCore, private FastAPI or Kaggle worker. Use existing root `STOP.bat` separately when you intend to stop that application. Occupied Expo ports or an incorrect application on 3000 fail clearly without killing unrelated processes.

One-time prerequisites: Node.js, `npm ci` in `mobile/`, the existing root stack's Python dependencies and Android SDK Platform Tools. Set `ANDROID_HOME`/`ANDROID_SDK_ROOT` or put `adb.exe` on PATH; the standard local Android SDK location is also detected. Ordinary USB debugging and PC authorization suffice. The separate Xiaomi security switch is unnecessary. All phone taps and navigation are manual; remote phone actions/captures remain prohibited.

## Device connectivity and application boundary

The existing root application intentionally binds BeautyCore 3000 and private FastAPI 8000 to loopback. Normal authenticated mobile development therefore uses USB/ADB reverse, including authorized emulators. Wi-Fi alone fails clearly in this mode; there is no LAN fallback that exposes FastAPI or changes root startup. The earlier trusted LAN/mock-8001 resolver remains an internal historical launcher test mode and is not the authenticated mobile app boundary. A future LAN application transport requires its own secure approval; do not forward private FastAPI or Kaggle ports.

ADB uses `--no-rebind`, verifies mappings, preserves identical existing mappings and refuses conflicting targets. Cleanup removes only mappings this mobile session created that still have the original target, never `--remove-all` or `kill-server`.

All client routes live in `lib/api/`: login/session/logout and allowlisted `/api/ai/features` catalogs/generation. Native fetch retains the HttpOnly session in the OS cookie jar; JavaScript keeps only public user identity. Login verifies a follow-up session and protected catalog. Native mutation Origin matches NextURL's localhost normalization for loopback transport. Production hosts retain their configured Origin. Browser role/session/Origin protection is unchanged. Use HTTPS for an eventual deployed application; this USB development acceptance is not a production deployment claim.

Mobile → BeautyCore application authentication/adapter → private FastAPI → existing Kaggle unified worker. Multipart includes `image` and `style_id`. SDK 57 globally uses Expo fetch, so native uploads use supported filesystem File blobs, not older React Native URI descriptors. No direct FastAPI fallback or Kaggle URL/credential is included.

## Product flow and safety

Consultation leads Home. Settings owns account/connection checks. Hair, Makeup and Nails share Photo → Style → Review → Generating → Result. Photos, selected styles and Consultation direction remain temporary app memory; the OS picker may create local cache files. Generation sends a photo only on the explicit action. Logout clears local drafts/results and verifies the session is gone.

One global operation blocks duplicate Generate and draft changes across services. It survives ordinary rendering/navigation; keep the app open while processing. Elapsed time is truthful, with no percentage or short generation deadline. App termination/reloading is not a durable job/status system. Never reload or retry while server work might still run. Reads/auth use a 12 second deadline. No generation request automatically retries.

Definitive validation/auth rejection permits manual correction/retry. Response loss, unreadable output, 409 or server failures retain an uncertainty lock. The existing manual contract has no status endpoint. An operator must confirm processing ended before you explicitly release that lock and retry.

Result comparison uses the real inline result and local original. Try Another Style retains the photo; Start Over clears that studio. Android Save opens the system folder chooser and writes only to the granted folder, with cancellation/failure feedback and no broad gallery permission. Share opens the native sharing sheet using an app-cache image removed when the action finishes. iOS Save uses add-only photo permission with denial/settings feedback; iOS runtime acceptance is not claimed. Expo Go's supported legacy media module avoids an unavailable ExpoMediaLibraryNext import.

Consultation remains the local Service → Direction → Your Looks brief. Real conversation/recommendations are MOBILE-02C, not part of this phase. No camera capture or model changes.

## Validation

```powershell
npm run typecheck
npm run lint
npm test
npx expo install --check
npx expo-doctor
npm run export:android
# From F:\HAIR:
python -m unittest discover -s tests -p test_mobile_launcher.py -v
```

Use the existing non-secret BeautyCore origin for exports. Local/mocked tests, exports and PC browser width checks do not substitute for actual Android login, gallery, Save/Share or real generation acceptance. See [integration contracts and safety](../docs/guides/mobile-02b-integration.md).

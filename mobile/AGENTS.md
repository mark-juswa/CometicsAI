This is an Expo/React Native mobile application. Prioritize mobile-first patterns, performance, and cross-platform compatibility.

## Expo has changed — do not trust your training data

Expo ships breaking changes every SDK release. APIs you remember are likely renamed, moved, or removed. Before writing any code that touches an Expo, EAS, or React Native API:

1. Read the major version of the `expo` package in `package.json`.
2. Fetch the matching versioned docs: `https://docs.expo.dev/versions/v<major>.0.0/`
3. For anything else, fetch https://docs.expo.dev/llms.txt — an index of all Expo docs with corrections to common LLM misconceptions. Follow its links to the specific page you need; never answer from memory.

## Commands

Use `bunx` instead of `npx` if the project uses bun (`bun.lock` present).

```bash
npx expo install <package>  # ALWAYS use instead of npm/yarn/pnpm/bun add — resolves SDK-compatible versions
npx expo start              # start the dev server
npx expo lint               # lint
npx tsc --noEmit            # typecheck
npx expo-doctor             # diagnose dependency and config issues
npx expo install --fix      # fix incompatible package versions
```

Run lint and typecheck before declaring any task done.

## Navigation & Routing

- Use **Expo Router** for all navigation. Routes live in `app/`, as explicitly requested by the Supervisor. Every file there is a screen; `_layout.tsx` defines the navigator. Keep non-route code outside `app/`.
- Import `Link`, `router`, and `useLocalSearchParams` from `expo-router`.
- Docs: https://docs.expo.dev/router/introduction.md

## Building with EAS

Use EAS to build, sign, and submit the app in the cloud (`eas build`, `eas submit`) and to ship over-the-air updates (`eas update`) — no local Xcode or Android Studio required. Run EAS CLI as `bunx eas-cli <command>` in Bun projects, or `npx eas-cli@latest <command>` otherwise; substitute that for bare `eas` in docs examples.
Docs: https://docs.expo.dev/eas/index.md

## Rules

- Read `../context/state.md` first and `../docs/guides/mobile-00-contracts.md` for inspected integration contracts. The governing mobile direction is `../docs/specs/0006-mobile-foundation.md`.
- Product UI direction is `../docs/specs/0007-mobile-product-ux.md`: Consultation leads Home, diagnostics are in Settings, studios share focused stages and temporary drafts, and result comparison is a dedicated route. Explicit MOBILE-02B/02C authorization supersedes the original mock/GET and local brief boundaries. Preserve the visual flow and existing authenticated real contracts. `../docs/guides/mobile-02c-integration.md` owns inspected native Consultation contracts and `../docs/experiments/mobile-02c.md` records current acceptance; standalone Android Makeup visual and Nails generation acceptance remain explicitly deferred.
- Historical MOBILE-01 checkpoint was development only: existing FastAPI health/catalog GET requests, local gallery photos and explicitly labeled unchanged mock results. No generation, camera, direct Kaggle connection, public server secrets or persisted photos.
- Current generation uses SDK 57 global Expo fetch and filesystem File multipart. Never restore the old RN URI descriptor or automatic generation retry. Custom and Consultation share one temporary generation guard. Consultation uses opaque handles and existing per look status GET to recover response loss; pending/unknown remains locked and confirmed failure permits explicit retry. Manual Custom retains its existing operator confirmation because it has no status route. Do not reload/terminate during GPU work. Browser/export checks do not prove native acceptance.
- API routes live only in `lib/api/`. Client configuration is only `EXPO_PUBLIC_API_BASE_URL`, with no default address. TanStack Query owns server state; `store/studio.ts` owns temporary drafts.
- Native visual source is the existing BeautyCore AI studio; `constants/theme.ts` and `design.md` document its translation. User architecture and directory instructions outrank scaffold defaults.
- Run `npm run typecheck`, `npm run lint`, `npm test`, and Expo exports. Browser checks and Android bundling do not prove Android runtime acceptance.
- Normal Windows development uses `../START_MOBILE.bat` and `../STOP_MOBILE.bat`. Current authenticated mode requires the existing root BeautyCore stack and authorized ADB reverse for 3000/8081, supplies the application origin only to Expo, disables dotenv for that child and owns only Expo. LAN alone is refused because the root application/private API are loopback. The older mock/LAN helper mode remains historical test support. Preserve the working root launchers. Launcher tests: `python -m unittest discover -s tests -p test_mobile_launcher.py -v` from the repository root. See `README.md` for one-time OS/tooling prerequisites.
- Physical phone actions are manual by Supervisor instruction. Do not issue remote taps, navigation or further phone screenshots, and do not enable/bypass Xiaomi security debugging permissions. PC launcher/API assistance is allowed. MOBILE-01 native acceptance on one phone is recorded in `../docs/experiments/mobile-native-android.md`, distinguishing observed checks from Supervisor manual reports.

- If `ios/` and `android/` directories do not exist, they are generated (Continuous Native Generation). Never create or edit them by hand — configure native behavior in `app.json` and config plugins.
- Expo Go only includes its bundled native modules. After adding a library with native code, the app needs a development build: `npx expo run:ios|android` locally, or `eas build --profile development`.
- Prefer recommended Expo modules over third-party libraries, and check your available skills before adding dependencies. Docs: https://docs.expo.dev/versions/latest/index.md

# MOBILE-01 automatic Windows development launcher

2026-10-03. Parent revision `dac88f7`, branch `codex/mobile-01`.

**Launcher: DONE, LOCAL VERIFIED. Native Android: BLOCKED, NEEDS VERIFICATION.** No authorized Android device was available. The actual default route uses physical Wi-Fi, but Windows marks that network Public, so ordinary LAN startup correctly refuses it. No network profile or firewall setting was changed. You can use authorized USB or mark an actually trusted LAN Private once; neither requires finding an IP or editing an env file.

## Implemented behavior

Additive `START_MOBILE.bat` and `STOP_MOBILE.bat` call `scripts/mobile_launch.py`. A read-only PowerShell helper supplies Windows route, interface, adapter, profile and source-address facts. Selection uses the lowest route-plus-interface metric among usable trusted physical default routes, rather than the first IPv4. Virtual/VPN, disconnected, Public, non-RFC1918 and ambiguous candidates are excluded.

Authorized ADB devices are preferred. API 8001 and Expo 8081 are reversed without rebinding an existing different target. Both mappings are verified; identical pre-existing mappings remain owned by their original creator. Failed partial setup releases only the session's new mappings before trying another device or LAN. USB advertises loopback; LAN advertises its discovered source IPv4. Physical transport remains unverified without a phone.

The separate unchanged FastAPI source starts on `0.0.0.0:8001` with process-only mock Hair/Makeup/Nails and deterministic Consultation settings. Expo starts after mock health succeeds. Expo receives the resolved public API origin only for its process, an OS/tooling environment whitelist, disabled dotenv loading and a cleared Metro cache. Backend/mobile env files are byte unchanged. There is no GPU discovery, inference request, public tunnel, firewall modification or permanent address setting.

The foreground manager holds a Windows job and an exclusive session lock. Newly spawned children are suspended and assigned to the job before they can create descendants. Stop verifies a random session identity and token through the loopback controller, then closes that job. Stored PIDs cannot authorize a kill. ADB cleanup removes only new mappings whose targets are still unchanged. Duplicate Start preserves the running session. Occupied ports fail without touching their owners. Startup deadlines are 45 seconds for FastAPI and 60 seconds for Expo, with readiness polling and no restarts.

## Reproducible validation

```powershell
# Repository root, existing system Python dependencies:
python -m unittest discover -s tests -p test_mobile_launcher.py -v
python docs/experiments/mobile-launcher-assets/validate_launcher.py
python -m pytest backend/tests/test_capstone_startup.py -q
# mobile/:
npm run typecheck
npm run lint
npm test
```

The integration harness substitutes only the connection resolver with a controlled loopback fixture; production exposes no fixture or Public-network bypass flag. It starts real FastAPI and Expo. A failed-Expo case starts an owned process exiting 23. An unhealthy-API case starts an owned non-API HTTP server and shortens the test wait to 2 seconds; the production deadline stays 45. These cases validate failure cleanup without GPU calls. The actual batch wrappers are exercised for Stop, occupied-port failure and no-transport failure.

| Check | Observed result |
| --- | --- |
| Launcher unit/native Windows job tests | 12 passed, including child/grandchild shutdown, unrelated process/listener survival, auth/state checks, route priority and ADB cleanup/conflict/fallback |
| Real loopback-fixture startup | Existing mock FastAPI health HTTP 200; actual Expo Metro ready and Android development bundle built |
| Actual catalogs | Hair 6, Makeup 10, Nails 5 styles, all from existing GET API routes |
| Process API origin | Android bundle contains `http://127.0.0.1:8001`; Expo Android manifest advertises `127.0.0.1:8081` |
| Existing private-value bundle scan | 13 current long private values inspected, zero matches; values are never printed |
| Repeated Start | Existing session retained, no restart |
| Actual Stop batch | Owned API/Expo ports released, ownership state removed; unrelated Python process survives |
| Failed Expo / unhealthy API | Clear errors, owned session closed, ports released, unrelated process survives |
| Actual Start with unrelated port 8001 listener | Fails clearly; listener remains usable |
| Actual Start with no device and Public Wi-Fi | Fails clearly before starting API/Expo; no usable trusted route |
| Environment files | Existing backend `.env` and mobile `.env.local` remain byte unchanged |
| Mobile TypeScript and lint | Passed |
| Mobile contract/state tests | 8 passed; initial sandbox child-process EPERM resolved by the permitted test execution outside that sandbox |
| Existing capstone startup regressions | 54 passed |
| Protected source comparison to `dac88f7` | No backend/frontend/BeautyCore, model/data/notebook, existing script, root START/STOP or mobile application source change |
| Native Android | PENDING: authorized device list empty; no claim of loading, picker, Android back, phone connectivity or layout acceptance |

Runtime artifacts: [results](mobile-launcher-assets/results.json), [startup](mobile-launcher-assets/startup.log), [Expo failure](mobile-launcher-assets/expo-failure.log), [API unhealthy](mobile-launcher-assets/api-unhealthy.log), [port conflict](mobile-launcher-assets/occupied-port.log), [no transport](mobile-launcher-assets/no-transport.log), [integration harness](mobile-launcher-assets/validate_launcher.py). No bundle, ownership token or private configuration is committed.

## Correction during validation

Installed Expo SDK 57 binds `localhost` directly for `--localhost`. Windows initially chose IPv6, so an IPv4 readiness probe timed out even though Metro had started. USB mode now starts Node with `--dns-result-order=ipv4first`; the subsequent real Metro readiness, Android manifest and bundle checks passed with the fixed IPv4 address. This changes only the launcher child command, not Expo dependencies or application code.

## Remaining gate

An authorized physical phone must still load the app, reach health and all three catalogs, choose/cancel/replace/remove/reset a gallery photo, exercise Android navigation/back, show unavailable-API errors and fit phone widths. Neither ADB command mocks nor Android bundle compilation closes those native checks. No GPU generation is needed for that gate. Real feature generation and authenticated BeautyCore integration remain MOBILE-02 scope.

Official command references: [Android ADB reverse](https://developer.android.com/develop/ui/views/layout/webapps/access-local-server), [Expo environment loading](https://docs.expo.dev/guides/environment-variables/), [Expo CLI connection modes](https://docs.expo.dev/more/expo-cli/).

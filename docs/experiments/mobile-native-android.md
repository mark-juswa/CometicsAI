# MOBILE-01 physical Android acceptance

2026-10-03, `codex/mobile-01`, application and launcher revision `dc5e96a`.

**MOBILE-01 DONE; NATIVE ACCEPTANCE VERIFIED ON THIS DEVICE.** Supervisor installed Expo Go, enabled Developer options and USB debugging, connected the phone and authorized this PC. ADB detected a physical Xiaomi M2101K7AG running Android 12 (API 31), physical display 1080 × 2400, with Expo Go 57.0.9. Native load/USB/API proof was observed by the assistant; interaction, error and recovery checks were performed and confirmed by the Supervisor. The full device serial is intentionally omitted from durable evidence. This is acceptance on one physical phone, not a claim of testing all Android devices.

## Actual runtime proof

`START_MOBILE.bat` selected USB/ADB, configured API 8001 and Expo 8081 reverse mappings and started the isolated existing CPU mock FastAPI plus Expo. The Android app was opened with ADB ACTION_VIEW for `exp://127.0.0.1:8081`. Its home screen rendered, and its service GET reached the backend. Native route links `/--/connection`, `/--/hair`, `/--/makeup`, `/--/nails` opened their actual Expo Router screens without changing application code.

| Native behavior | Evidence | Verdict |
| --- | --- | --- |
| Expo Android environment loads actual studio | [Home screenshot](mobile-native-assets/home-initial.png), [UI tree](mobile-native-assets/home-initial.xml) | VERIFIED |
| Phone reaches existing API through USB reverse | [Connection screenshot](mobile-native-assets/connection.png), [UI tree](mobile-native-assets/connection.xml), [backend request log](mobile-native-assets/backend-get-requests.log), UI says `Connected · ok`, generator `mock` | VERIFIED |
| Hair screen mounts and requests active catalog | [Hair screenshot](mobile-native-assets/hair-loaded.png), [UI tree](mobile-native-assets/hair-loaded.xml), GET `/features/hairstyle/styles` HTTP 200 | VERIFIED for mount and catalog request, selection/scrolling still pending |
| Makeup screen mounts and requests active catalog | [Makeup screenshot](mobile-native-assets/makeup-loaded.png), [UI tree](mobile-native-assets/makeup-loaded.xml), GET `/features/makeup/styles` HTTP 200 | VERIFIED for mount and catalog request, selection/scrolling still pending |
| Nails screen mounts and requests active catalog | [Nails screenshot](mobile-native-assets/nails-loaded.png), [UI tree](mobile-native-assets/nails-loaded.xml), GET `/features/nails/styles` HTTP 200 | VERIFIED for mount and catalog request, selection/scrolling still pending |
| Native gallery choose/cancel/preview/replace/remove/reset | Supervisor answered “It all works” to the manual checklist covering these actions, including Replace cancellation | VERIFIED by Supervisor report, not automated observation |
| Android service navigation, mock comparison and Android Back | Same explicit manual checklist and “It all works” reply | VERIFIED by Supervisor report, not automated observation |
| Consultation overview | Supervisor answered “Both checks pass” to recovery plus Service, Direction and Your Looks confirmation | VERIFIED by Supervisor report |
| Unavailable API error | PC owned session stopped, Supervisor answered “The app shows a clear API error” | VERIFIED by Supervisor report |
| Recovery after ordinary PC Start | [Restarted backend GET log](mobile-native-assets/backend-recovery.log), real API/Expo host readiness, Supervisor answered “Both checks pass” | VERIFIED by Supervisor report |
| Scrolled text/cards fit this phone width | Supervisor confirmed the manual checklist, including scrolling and width | VERIFIED by Supervisor report for this device; earlier 320/360/390/430 browser evidence remains supporting evidence only |

## Device permission limitation

ADB could launch Expo Go, read UI hierarchy and capture its app screens, but `adb shell input tap` failed with `java.lang.SecurityException: Injecting to another application requires INJECT_EVENTS permission`. The test tried only visible studio controls; failed taps did not perform gallery selection or alter phone settings. Supervisor then explicitly chose manual testing and instructed: “I will do it myself. dont do remote taps. I have security concerns”. Remote taps, navigation and further phone screenshots stopped immediately. Do not attempt to enable or bypass the extra security permission. Ordinary USB debugging remains sufficient for launcher connectivity; the separate security debugging switch may remain off. The manual checklist and actual Supervisor outcomes are recorded below. Selection of a testing method alone was never counted as acceptance.

The assistant selected, copied or uploaded no private photos. Gallery testing was performed by the Supervisor, with images staying in the phone's local MOBILE-01 state. No images were generated, no GPU/Kaggle request was made and no backend, model, mobile application or launcher source was modified in this acceptance run. Saved screenshots predate manual gallery testing and contain only the studio app and device status/navigation bars. The ordinary existing source/tests and launcher evidence from [MOBILE-01](MOBILE-01.md) and [launcher validation](mobile-launcher.md) remain applicable. The remaining native gate is now closed by the observed and explicit manual evidence below.

## Manual acceptance sequence

Supervisor was asked to verify all three style lists, gallery opening/cancel/selection/preview, Replace including cancel, Remove, Reset photo/style, style selection, unchanged mock preview, Android Back and scrolled width. Exact reply: “It all works”. This is explicit human native acceptance evidence for those named checks; there is no assistant-driven gallery or post-restriction phone screenshot.

For the unavailable API check, the assistant ran only PC `STOP_MOBILE.bat`. It reported owned-session shutdown and the foreground launcher exited successfully. Supervisor was asked to tap the app's Check connection while the API was stopped and distinguish the app's controlled API error from Expo's Metro-disconnected notice. Exact reply: “The app shows a clear API error”.

The assistant then ran ordinary PC `START_MOBILE.bat`, with no phone input/navigation/capture commands. It selected the same USB connection, reported MOBILE_DEV_RUNNING and returned mock health plus Metro running. Supervisor was asked to manually confirm Check connection recovers and the Consultation overview presents Service, Direction and Your Looks. Exact reply: “Both checks pass”. The USB development session is left running for the Supervisor to use, with normal STOP_MOBILE available. No remote phone interaction resumes.

## Acceptance criteria and limits

| Criterion | Completion evidence |
| --- | --- |
| AC-1 additive/protected system | Source comparison to `dc5e96a` shows no app/backend/launcher/model change in this acceptance slice; earlier additive branch and protection checks remain valid |
| AC-2 native design/navigation | Actual native home/service screenshots plus Supervisor's service, mock-preview, Back and scrolled-layout confirmations |
| AC-3 local gallery lifecycle | Supervisor's explicit checklist confirmation; existing image/state unit tests remain supporting evidence |
| AC-4 typed health/catalog API | Native connected/mock UI, actual three catalog HTTP 200 requests, manual catalog and recovery confirmations, existing API contract tests |
| AC-5 controlled loading/errors/mock | Existing controlled error tests and browser mock flow, native mock comparison and unavailable API/recovery confirmed manually |
| AC-6 Consultation remains overview | Supervisor confirms Service, Direction, Your Looks; no real Consultation/recommendation/generation call |
| AC-7 local checks/no secrets | Unchanged application/dependency source retains passed typecheck/lint, 8 mobile tests, exports/Doctor and prior regressions; launcher Android bundle scan checked 13 private values with zero matches |
| AC-8 actual Android acceptance | Observed native launch/USB/health/catalog transport plus explicit Supervisor gallery, navigation/back, phone-width and error/recovery results |

No application code changed, so the prior passing checks were not rerun merely for documentation. Browser widths 320/360/390/430 provide earlier supporting layout evidence; the physical-device verdict is limited to this phone and the Supervisor's manual report. Camera, full Consultation, authentication and real GPU generation remain outside MOBILE-01. Next authorized design scope is MOBILE-02 through the existing BeautyCore authenticated application adapter, preserving all models and worker behavior.

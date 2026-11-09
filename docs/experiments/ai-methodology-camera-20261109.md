# AI methodology and camera photo entry

Date: 9 November 2026. Implementation DONE. Local checks VERIFIED. Production integration NOT STARTED.

Supervisor requests an explanation of AI methodology and training, plus a direct camera option when selecting an image. Implemented on `codex/ai-methodology-camera`, based on main at `ba077964e87b7f6b5b481ecc55d4dc6f7083a408`, which already includes the client enhancements and deployed generation recovery fix.

## Changes

The public `/how-ai-works` page explains dataset preparation, paired editing examples, source separation, pretrained FLUX and project trained LoRA adapters, evaluation, and client generation. It distinguishes the two Hair adapters, corrective Makeup adapter and hybrid Nails paths. It does not call every style a separately trained model or imply an upload retrains the model. Technical notes retain the actual corrective run counts and the reused validation identity limitation. Content is grounded in the corrective training/model report, released catalog and the inspected project defense explanation. About and every studio shell link to it, with a footer link retained for narrow layouts.

`components/camera-capture.tsx` adds one reusable Use camera control to Hair, Makeup, Nails and consultation, including guest consultation. It requests video only after a click, shows preview and camera switching, captures a JPEG with longest edge at most1600px, offers review/retake/Use photo, and calls the existing File acceptance callback only after selection. It does not submit a generation or upload by itself. Portrait capture prefers the front camera and Nails prefers the rear camera. A native camera picker is a best effort fallback. Ordinary file upload and existing image selection remain.

Tracks stop on capture, dismissal, departure and disabled state. Delayed permission or canvas callbacks cannot resurrect a closed capture. Permission denial, unavailable hardware, unsupported preview and capture failure have controlled fallback messages. Existing8MB JPG/PNG validation remains. Browser secure context and permission requirements follow [MDN getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia).

No model, adapter, catalog, generation recovery, GPU package, API contract, production database or provider configuration changed. Profile and product inventory uploads are outside this AI photo scope. No new dependency was added.

## Verification

**163 focused checks pass, zero failures**, including ten new camera/methodology cases, existing generation recovery, AI authorization, guest limits, save/book and business UI tests. TypeScript and the default Next production build pass, with47 static pages. Build uses a dummy local database URL. Logs and screenshots are retained in `artifacts/ai-methodology-camera-20261109/`.

Initial wider tests exposed two existing clock dependent booking lifecycle fixtures at23:29 Manila. Their next minute bookings crossed the90 minute allocation boundary into the next day. Both failures were reproduced on the untouched client snapshot at efd63d7. The tests now use a controlled midday clock through the existing time dependency and no show procedure time argument. Their original lifecycle assertions remain. Product booking rules and database migrations are unchanged. Initial failing output is retained separately; the final complete suite passes at night.

The actual built methodology page was visually inspected in the browser, including expandable technical notes and navigation from About. A local synthetic canvas MediaStream exercised the actual camera component, capture/review/selection and cleanup without requesting real hardware access. It produced a valid15,832byte JPEG, required Use photo, and reported stopped tracks for both captures. No upload or GPU call occurred.

The browser viewport override did not change the measured1265px page width, so no mobile browser layout pass is claimed. The override was reset. Real phone camera permissions, native picker behavior and device switching on physical hardware remain NEEDS VERIFICATION. The new features are not yet on Render; the existing recovery release remains live.

Commands from `beautycore`:

```powershell
npm run test:camera
npm run test:recovery
npm run typecheck
npm run build
```

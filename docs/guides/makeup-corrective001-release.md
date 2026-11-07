# Corrective Makeup release review and rollout

Date: 6 November 2026. Release candidate `styles-20261106-01`. Status: APPROVED FOR ROLLOUT by the Supervisor on 6 November. Source applied and local checks pass; publication, Render deployment and Kaggle registration are tracked separately.

## What passed

The real application completed all 13 Makeup styles. Every returned Makeup PNG is exactly the same file as its corresponding previously accepted real model output. Both Hair adapters and the Nails adapter also completed, with active tensor verification and one Base load. No more target audit, repeated model gallery review or training is needed for this gate.

The matching deployment candidate contains 18 Hair, 13 Makeup and 8 Nails styles. Its Makeup checkpoint, exact style captions, generation code and full adapter scaling checks are unchanged from the tested application. The three expanded Makeup styles receive matching catalog and booking metadata using the existing Makeup Application service. No new service price, UI redesign, database migration or secret is introduced.

The production candidate has passed actual archive/manifest checks, fresh installation of the worker overlay, all 13 staged application API routes, execution profile corruption guards, 25 staged Makeup API/runtime tests and five Render capability/business metadata tests. All three older releases retain their actual ten style Makeup catalogs as explicit fallbacks. Current application sources, old bundles, live website connection and cloud settings remain unchanged.

## Review files

Prepared directory: `I:/HAIR/artifacts/makeup-corrective-supervision-20261105/release-candidate-03/`.

| File | Responsibility |
|---|---|
| `release.json` | Exact new release, package hashes and before/after hashes of proposed publication files |
| `source/` | Reviewable proposed source copies, including matching Render JSON and tests |
| `publication.patch` | Source diff against the current checkout |
| `notebooks/render_kaggle_makeup_corrective_demo.ipynb` | Final deployment starter with normal authenticated website registration |
| `beautycore_makeup_release_20261106.bin` | Matching CPU input with the tested corrective checkpoint and worker overlay |
| `cpu-preflight.json`, `profile-verification.txt`, `verification.json` | Local candidate check results |

The final serving notebook is in the repository `notebooks/` folder. It includes the verified Makeup capability startup correction; the earlier candidate notebook remains preserved. Use the final serving notebook for deployment.

The new CPU input is 75,246,586 bytes, SHA256 `0c657ae4d2b62e11bd8c5728321330d5416fbfd1d36354d8482ac548f1449357`. Use the unchanged existing GPU input `capstone_train002_20260928_v1.bin`, SHA256 `f0d1fed52e00b6c5a1da2cade3731237675cdebbfc0b2cde3b2dbda99a4019ac`. Preserve old notebooks and inputs.

Release manifest SHA256: `f7f2e8cbb3d72b6a10dbe471e3e8081c4813c413529071359baae7291f3c625e`.

## After project lead approval

1. Apply the exact proposed source files after checking their current hashes against `release.json`. Publish only the reviewed release work, preserving existing unrelated repository changes. The code publication and cloud deployment must be recorded separately.
2. Deploy the matching BeautyCore version on the existing Render service. Keep its root directory, environment, secrets, Neon database and normal commands. The new Render metadata recognizes all three exact preserved releases, allowing the existing older runtime during the transition. Publishing alone does not establish a Live Render deployment.
3. Retain the original successful Kaggle notebook environment when importing `notebooks/render_kaggle_makeup_corrective_demo.ipynb`. The supplied file does not contain a Kaggle image pin. A fresh notebook or unverified copy can select an incompatible host. Before continuing, Cell 1 must verify Python 3.12.13, Torch 2.10.0+cu128, CUDA 12.8 and Tesla T4. Preserve the original code and outputs. Attach exactly one new CPU input and the unchanged GPU input. Use Internet plus the same three existing Kaggle secrets. A suitable dataset title is `BeautyCore Makeup Release 20261106`. Keep the actual CPU filename unchanged. See the [reported mismatch and recovery limits](../experiments/makeup-serving-runtime-mismatch-20261106.md).
4. Once ready to switch, stop the older serving session and let its active registration lease expire naturally, up to 180 seconds. Do not force endpoint/database changes. Run the three new code cells once. The new starter restores normal automatic authenticated website registration. Wait for `CONNECTED TO WEBSITE` and the matching release/capability evidence.
5. Confirm 18 Hair, 13 Makeup and 8 Nails styles in the signed-in website. Upload a fresh portrait and generate a complete Makeup look. Confirm the result records checkpoint `991a1037...`, then test a second distinct Makeup style and a Hair request after Makeup. A fresh identity is required because the existing validation subjects were reused in development.
6. Exercise an added Nail design on a clear full hand photo, consultation generation, Save Look, refresh, and booking with the existing matching service/stylist. Confirm the saved image and booking reach the intended client/stylist pages. These live operations remain unverified until actually run. Mobile acceptance stays explicit and separate.

Keep the new Kaggle session running while serving the website. Stop on a generation failure and preserve its admitted job ID/status/logs. Do not automatically replay an uncertain generation.

## Rollback

The old complete Hair/Nails notebook and its original matching CPU/GPU inputs remain byte-for-byte intact. Stop the new session before starting that fallback. Let the lease expire and let the old notebook register normally. The proposed Render metadata explicitly recognizes its original 18 Hair/10 Makeup/8 Nails capability catalog. Earlier French/Nails releases are also preserved. Do not remove saved looks, appointments, datasets or weights.

## Limits

The model now reproduces the accepted complete looks through the application. That establishes the tested model/application path. It does not prove fresh identity generalization, a live website connection, full hand Nails behavior, save/book or mobile operation. The deployment candidate only changes release/catalog wiring around the tested generation code; it has not been run against the live website. Production rollout is now authorized. Publication, deployment, Kaggle registration and live acceptance must still be verified individually.

See [the actual application result](../experiments/makeup-corrective-application-results-20261106.md) for raw return bindings, timings and limitations.

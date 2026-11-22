# BeautyCore current Kaggle backup

Prepared 13 November 2026. Local preparation is not a successful Kaggle GPU rehearsal. Keep your existing Pod until its important files are backed up. You can stop an unused Pod to end GPU billing while retaining its volume disk, but storage still bills and GPU availability on restart is not guaranteed. Terminating a Pod destroys its local volume. A separately created network volume has independent billing and persistence.

## What this backup contains

The same accepted model release, 18 Hair, 13 Makeup and 8 Nails, including expanded styles. The new notebook includes the current CPU application files, local face detection asset and preference based consultation. Gemini remains text only. Camera capture and the training explanation are website features and are already on Render. No model training is needed.

The ZIP includes the new notebook, the two unchanged private input archives, hashes, this guide and the existing 16 case application probe. Keep this ZIP private. Do not upload it to the public GitHub repository. No credentials or new user portraits are included.

## Set up Kaggle

1. Extract the private backup ZIP on your computer. Import `beautycore_kaggle_backup_20261113.ipynb` into a copy of your previously successful notebook. Retain that successful notebook's original environment. Verify it is Python3.12.13, Torch2.10.0+cu128, CUDA12.8 and Tesla T4. The setup cell checks these exactly. Importing a notebook file alone does not pin a historical Kaggle image. A newly created notebook's Original setting may be too new. Do not remove guards if a mismatch appears. This remains a real host compatibility gate until a successful session is observed.
2. Enable Internet and the T4 accelerator configuration used by the successful notebook. The serving worker uses one GPU; a second T4 is not combined into one larger GPU. At least30GiB system RAM is required. Kaggle availability, quota, runtime duration and exact container are not guaranteed by this package.
3. Attach exactly one copy of each file: `capstone_train002_20260928_v1.bin` and `beautycore_makeup_release_20261106.bin`. Existing private datasets can be reused. Do not attach duplicates or the older CPU package. If recreating a private dataset, upload the two extracted binaries, not the outer backup ZIP.
4. In Kaggle Secrets enable the existing `AI_BACKEND_API_KEY`, `AI_REMOTE_API_KEY` and `GEMINI_API_KEY`. The backend key must match Render. Never paste values into cells or screenshots.
5. Run the first code cell once. It verifies archives, the original worker/release pair and the new CPU inventory. It does not start a GPU. A mismatch stops setup; resolve the stated cause before proceeding.
6. Run the second code cell once. It installs isolated CPU dependencies, checks the face/hand/segmenter assets, starts the unchanged GPU model release and CPU API, and verifies the complete catalog. Expect `KAGGLE_BACKUP_READY_FOR_VALIDATION`. It does not register with Render. Do not start another worker if startup fails; inspect the saved stage log or use a clean session after stopping owned services.
7. Run the third code cell. Expect `SUBJECT_REJECTION_PASS` for blank incorrect subjects across all three services. This does not prove acceptance of correct photos or completed generation.

## Rehearse before calling it a working backup

Upload `makeup_corrective_application_probe.py` using Kaggle's file controls. In a separate code cell, execute it against the already running session:

```python
import runpy
probe = runpy.run_path('/kaggle/working/makeup_corrective_application_probe.py')
result = probe['run'](CLIENT_WORK)
```

Use the actual uploaded script path if different. This runs16 real generation cases, all13 Makeup looks, two expanded Hair routes and one prepared Nails crop. It consumes GPU quota. Do not automatically retry generation. Review `CLIENT_WORK/application-results/review.html` and download the returned results ZIP. The Nails crop proves the existing worker path; a real full hand remains a separate required acceptance check. Also exercise a suitable portrait, a full hand, a hand submitted as Makeup and a portrait submitted as Nails. Rehearse consultation preferences and a real Gemini dialogue, then fresh website generation/save/booking after connection. Model output acceptance from the older Runpod session is not evidence that this new Kaggle session passed.

The final connection cell refuses connection unless the local negative checks and all16 real cases pass and you explicitly set `VISUAL_ACCEPTANCE_CONFIRMED = True`. It is deliberately safe against Run All. Stop the other provider's serving process and allow its registration lease to expire first. Run only that final connection cell. Expect `CONNECTED TO WEBSITE`. It reuses the running worker and does not load the GPU again. No Render URL edit is required. If registration fails, inspect the connection error rather than rerunning startup. New sessions require fresh temporary consultation handles.

## Before terminating the old Runpod Pod

Preserve off Runpod: both private binaries, this backup ZIP, any unique outputs/logs/uploads, and your private provider settings. Do not share keys or place them in a public archive. The original model weights are already in the verified private archives; Base weights can download again from the pinned revision. The Pod's downloaded Base cache saves startup time but is not the only copy of a custom adapter.

Check the existing `/workspace` for anything created only there. This local package cannot establish that all Pod files are backed up. Do not terminate based solely on a successful ZIP build. Once backed up, terminating an unused Pod avoids its retained local disk charge; separately retained network volumes continue billing until deliberately deleted. Do not delete a network volume holding the only copy of needed files.

Kaggle is a scheduled backup, not a server that remains available for the next two or three weeks. Save the notebook and private datasets, stop the session when unused, and start/rehearse before the presentation. Keep sufficient time for downloads and provider availability. No live Kaggle readiness, production cutover, Pod termination or cloud deletion is claimed by these instructions.

Provider references: [Kaggle notebook environments](https://www.kaggle.com/docs/notebooks), [Runpod storage](https://docs.runpod.io/pods/storage/types).

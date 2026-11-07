# Isolated pretrained Makeup test

This is a four-image evaluation of the author's Stable-Makeup model. It does not change the BeautyCore website or train a model.

## Files

- notebooks/stable_makeup_trial.ipynb
- artifacts/makeup-render-20261030/stable-makeup-pilot/beautycore-stable-makeup-pilot.bin

Input file size:3,767,075bytes. SHA256:4a3ec034bb433efaa5bf9a6d764909cbe004ec8248134286a4dd956009ad95d1.
The bin is a small verified ZIP container with a different extension so Kaggle keeps it as one input file.

## Run

1. Create a NEW PRIVATE Kaggle notebook and import stable_makeup_trial.ipynb.
2. Upload beautycore-stable-makeup-pilot.bin as a PRIVATE dataset/input and attach it. These two files are sufficient; no old BeautyCore datasets or Secrets are required.
3. Enable Internet. Select GPU T4. Use an independent notebook; do not replace the working demo notebook.
4. Run the two code cells in order once. Cell1 verifies/extracts into a new temporary folder and displays the reference crop. Cell2 creates an isolated Python3.10.20 environment, installs pinned dependencies, downloads model assets, loads the model, and attempts exactly4images.
5. Download the ZIP linked at the end of Cell2 and return it for review. Download it even if a stage fails.
6. After downloading, Stop the Kaggle session to stop consuming GPU quota.

The first run downloads about6.4GB of model assets PLUS Python/PyTorch dependencies. The bundle itself does not contain the large checkpoints. Models/cache stay in /tmp, separate from /kaggle/working outputs. ThirtyGiB scratch space is required. Twenty-second stage heartbeats show elapsed time/log bytes. There is a two-hour hard stop for the entire Cell2 process group.

Do not keep rerunning a failed attempt. The result ZIP has the failing stage log, traceback and status for a targeted correction. A workspace marker prevents accidental repeated generation.

## What to review

Output sheets show original / makeup reference / raw model result. Check clearly visible makeup, natural lashes/edges, preserved identity/expression, and whether skin/neck still match. Reject white cast, face replacement or artificial cosmetics. Existing photos may already have cosmetics; these reused development photos are not bare-face ground truth or final generalization evidence.

Model-loading/import success is not visual acceptance. No styles or production contracts will change automatically. The model's external pretrained contribution must remain truthful in the capstone; this trial does not use the project's trained MAKEUP-001 adapter.

## Verified before handoff

- Four CPU SPIGA/RetinaFace controls actually generated with author-compatible preprocessing.
- Public base and learned-checkpoint ranges accessed; no new key needed in local checks.
- All434makeup and340eachcontrol parameter names match model definitions.
- Imports and empty-tensor model construction pass on local CPU Torch2.10.
-47Linux Python3.10 dependencies resolve; GPU uses an isolated Torch2.0.1 runtime.
-23focused integrity/failure/timeout tests pass.
- Actual bundle CRC, round-trip checksums, input RGB512 sizes and notebook syntax pass.

Actual T4 loading, memory, latency and image quality remain untested until this notebook runs. FP16 is an explicit trial choice differing from the published FP32 entry script. No production GPU compatibility or improvement is claimed yet.

Source audit/experiment record:docs/experiments/stable-makeup-trial-20261030.json.

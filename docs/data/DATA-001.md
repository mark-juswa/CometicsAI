# DATA-001 — Real hairstyle paired dataset V1

**Status: IN PROGRESS, V1 bulk generation ready for Supervisor execution.** Source inspection and selection are complete. The three-image TRAIN pilot generated its counterparts on the Supervisor's Kaggle T4 on 2026-09-23 and its ZIP passed file/provenance checks. The Supervisor has since adopted a practical V1 review threshold and authorized the remaining 27 generations with the same global edit method. No official acceptance, full generation, pair finalization, or real LoRA training has occurred. Use the [current V1 handoff](DATA-001-v1-bulk-handoff.md).

## Source and license evidence

- Repository: [yikaiwang/FaceSketches-HairStyle40](https://huggingface.co/datasets/yikaiwang/FaceSketches-HairStyle40), pinned revision [`45de974926fe64551fc2d0b80973335e20ca10e2`](https://huggingface.co/datasets/yikaiwang/FaceSketches-HairStyle40/tree/45de974926fe64551fc2d0b80973335e20ca10e2).
- The dataset card declares `apache-2.0` and says the photographs are original reference images derived from the Hairstyle30k collection. It does **not** provide individual photograph provenance or rights documentation; keep this limitation explicit when publishing or distributing derivatives. No independent license for the upstream photographs was established here.
- The source archive is `FaceSketches-HairStyle40.zip`, 222,928,302 bytes. Its `image/<class>/` folders contain original photographs. `sketches/` is excluded. The ZIP also contains macOS `__MACOSX/._*` metadata entries, which are not photographs. The selected folders each contain **30 actual decodable originals**, despite 60 ZIP entries when metadata is counted.
- Exact original photo folders verified: `CrewCut`, `BobHair`, `LayeredHair`; 30 photos each, all 90 opened and converted to RGB successfully.

The source archive and extracted photographs are ignored by Git under `data/source/` and `data/dataset_v1/`. No third-party photos or generated outputs are committed.

## Selection and split

All 30 thumbnails per class were reviewed in [candidate inventory](DATA-001-candidates.json). [Pinned selection](DATA-001-selection.json) records eight train and two validation original identity groups per class and the fixed `CrewCut → BobHair → LayeredHair → CrewCut` generation cycle. Of 90 photos, **30 are provisionally selected** (10 per class), and **60 are excluded from V1** with a per-candidate reason or reserve status. One exact duplicate, `CrewCut/4.jpg` and `CrewCut/23.jpg`, was detected by SHA256; only `23.jpg` is selected. The final visual quality of every generated counterpart remains to be reviewed.

Local selection sheets (ignored generated artifacts):

```text
data/dataset_v1/contact_sheets/candidates_CrewCut.jpg
data/dataset_v1/contact_sheets/candidates_BobHair.jpg
data/dataset_v1/contact_sheets/candidates_LayeredHair.jpg
data/dataset_v1/contact_sheets/selected_originals.jpg
```

The chosen photos have 256+ pixels on the short side. Some are event/celebrity images, some have different illumination and framing, and the classes have noticeably different appearance distributions; these are data quality risks to revisit after the generated-pair review.

## Controlled generation and review gate

[`data001_generate_kaggle.py`](../../notebooks/data001_generate_kaggle.py) uses pretrained `black-forest-labs/FLUX.2-klein-base-4B` with the already tested FP16 CPU-offloaded inference path on GPU 0, 512×512, 20 steps, guidance 4.0, and fixed seed 1977. It pins the source revision, verifies the declared card license and model revision, reuses `/tmp/hf-cache`, and writes output only under `/kaggle/working/data001`. Source photographs are EXIF-corrected, converted to RGB, and fitted to 512×512 without cropping. Its output metadata includes prompt, exact source/target classes, split, seed, attempt, runtime, and memory. It never marks an output accepted.

In a Kaggle GPU notebook with Internet enabled, obtain this repository source in `/kaggle/working/CometicsAI` (or upload the script **and** its selection JSON with the same relative layout). Use the notebook kernel's interpreter. In a fresh session, the existing EXP-001 `--phase prepare` performs dependency setup only; it does not rerun training or inference:

```python
import subprocess, sys
repo = "/kaggle/working/CometicsAI"
subprocess.run([sys.executable, f"{repo}/notebooks/exp001_flux2_klein_kaggle_smoke.py", "--phase", "prepare"], check=True)
subprocess.run([sys.executable, f"{repo}/notebooks/data001_generate_kaggle.py"], check=True)
```

The default run makes **three TRAIN pilot outputs, one per class**, writes `/kaggle/working/data001/pilot_plan.json`, and stops. The [committed pilot plan](DATA-001-pilot-plan.json) matches the code planner exactly: `CrewCut_1 → BobHair`, `BobHair_1 → LayeredHair`, and `LayeredHair_4 → CrewCut`. Each output has a JSON sidecar with model revision, source revision and hash, output hash, prompt, seed, attempt, timestamp, dimensions, runtime, and GPU memory. `/kaggle/working/data001/generation_review_sheet.jpg` shows originals beside generated counterparts. These images remain PENDING VISUAL QA.

The earlier strict pilot stop and pilot-approval requirement were superseded by the Supervisor's critical-path direction. The [V1 runner](../../notebooks/data001_generate_kaggle.py) now permits `--all` after verifying the existing three pilot images, metadata, and hashes, without a V2 run or approval file. It preserves the selected identities and frozen generation settings, and generates only the remaining 27. It does **not** accept any output. An explicit REGENERATE review is required for one seed-only retry, including a validation identity; no indefinite retry is permitted. The [current handoff](DATA-001-v1-bulk-handoff.md) contains executable Kaggle commands and the practical review standard.

After all outputs have been reviewed, save an explicit 30-key review map with values like `{"CrewCut_1": {"status": "ACCEPT", "attempt": 1, "notes": "Hairstyle, identity, and background checked"}}`; any missing, `REGENERATE`, or `REJECT` entry blocks [`data001_finalize.py`](../../scripts/data001_finalize.py). Then transfer the small `/kaggle/working/data001/original/` and `generated/` outputs and metadata to the local ignored `data/dataset_v1/kaggle/` folder and run:

```text
python scripts/data001_finalize.py --generation-dir data/dataset_v1/kaggle --reviews data/dataset_v1/reviews.json
```

The finalizer requires 30 explicit ACCEPT decisions with notes, matches original/generated metadata and hashes to the pinned selection, verifies image decoding and 512×512 RGB mode, groups reverse directions in the same split, rejects unexpected SHA256 duplicate identities, calculates the required per-style distribution before copying, writes 48 train + 12 validation direction pairs, and creates the manifest, QA report, and both mandatory contact sheets. It preserves generation metadata and reviews in the final manifests. Captions are in `target/<stem>.txt` and reference/target image filenames match the proven AI Toolkit `control_path` contract. It does not train a model.

Earlier local implementation checks on 2026-09-23: Python compilation passed; the committed pilot plan matched the code planner. A separate **synthetic file-contract fixture** exercised the finalizer with 30 distinct RGB originals/counterparts and yielded 24/6 identity groups, 48/12 directional pairs, and the expected 16/4 per-style target counts. Corrupting one generated SHA256 in that fixture made finalization stop before writing an output dataset. These fixture images were not FLUX outputs or human-approved training examples. The earlier pilot-approval block is no longer part of the current V1 `--all` path.

## Three-image TRAIN pilot execution

The Supervisor ran the committed default runner in Kaggle on 2026-09-23. The supplied [full console log](DATA-001-pilot-console.log) records a CUDA-enabled Tesla T4 session, PyTorch `2.10.0+cu128`, Diffusers installed through the pinned EXP-001 preparation, a fresh Base pipeline load with FP16 and CPU offload on GPU 0, and exactly three 20-step image edits. The process exited with code 0 and printed the following completed outputs:

| Sample ID | Requested style | Console runtime | Generated path |
| --- | --- | ---: | --- |
| `CrewCut_1` | `BobHair` | 62.1 s | `/kaggle/working/data001/generated/CrewCut_1.png` |
| `BobHair_1` | `LayeredHair` | 64.0 s | `/kaggle/working/data001/generated/BobHair_1.png` |
| `LayeredHair_4` | `CrewCut` | 63.3 s | `/kaggle/working/data001/generated/LayeredHair_4.png` |

The runner reported `/kaggle/working/data001/generation_review_sheet.jpg`. The log shows no generation exception; it includes non-fatal Flax deprecation, unauthenticated Hugging Face rate-limit, and dependency-resolution warnings during preparation. The console alone did not include generated pixels, sidecars, model revision, or image-specific GPU-memory measurements; these were checked after the Supervisor supplied the pilot ZIP. **No official ACCEPT/REGENERATE/REJECT review has been recorded.**

The Supervisor then supplied `data001_pilot.zip` with the three original/generated images, sidecars, review sheet, plan, and environment report. [Pilot visual review](DATA-001-pilot-review.md) verified hashes and provenance and found one candidate suitable, two unsuitable under the original strict threshold because of hair-color and identity/accessory/clothing drift. The Supervisor later superseded that stop rule for Dataset V1 with a practical threshold and authorized the remaining global-edit generations. No official review statuses or final pairs have followed yet.

The later [masked Pilot V2](DATA-001-pilot-v2.md) and its [masked bulk handoff](DATA-001-bulk-handoff.md) remain unexecuted optional fallback material. They do **not** gate the current V1/global method. The active path is the [V1 bulk handoff](DATA-001-v1-bulk-handoff.md): generate the remaining 27, review all 30 with the practical threshold, retry only clear failures once, and finalize only after 30 explicit ACCEPT decisions.

## Current counts and pending evidence

| Item | Measured now | Final target |
| --- | ---: | ---: |
| Original source candidates | 30/class | — |
| Provisionally selected originals | 10/class, 30 total | 30 accepted |
| Excluded original candidates | 20/class, 60 total | replacements if required |
| FLUX generated counterparts | 3 pilot outputs, unreviewed | 30 accepted |
| Regenerations | 0 | at most one per failed candidate |
| Explicit generated ACCEPT / REJECT | 0 / 0; Codex visual findings are recorded, official review pending | 30 / 0 |
| Directional training / validation pairs | 0 / 0 | 48 / 12 |
| Final identity-generation and directional contact sheets | none | both required |

**The source dataset contains source photographs and sketches, not paired hairstyle edits.** The intended training pairs will be project-created by editing the selected originals with pretrained FLUX.2 Klein Base, visually filtering outputs, and expanding accepted identity groups bidirectionally. The custom hairstyle LoRA has not been trained, and identity preservation has not yet been demonstrated for these photographs.

# DATA-001 — Real hairstyle paired dataset V1

**Status: IN PROGRESS. Source inspection and selection complete; FLUX counterpart generation and visual acceptance have not occurred. No real LoRA training has begun.**

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

The default run makes **three pilot outputs, one per class**. Inspect the original and generated images side by side for identity, face, expression, pose, clothing, background, hairstyle, and artifacts before `--all`. `--all` generates the remaining 27 without overwriting the pilot. If one output fails visual QA, `--retry CrewCut/1.jpg` (for example) makes exactly one second attempt. A second failure remains REJECT; select a replacement real candidate if feasible, or stop under the DATA-001 minimum-count gate. No automatic quality acceptance or indefinite retry is permitted.

After all outputs have been reviewed, save an explicit 30-key review map with values like `{"CrewCut_1": {"status": "ACCEPT", "attempt": 1}}`; any missing, `REGENERATE`, or `REJECT` entry blocks [`data001_finalize.py`](../../scripts/data001_finalize.py). Then transfer the small `/kaggle/working/data001/original/` and `generated/` outputs and metadata to the local ignored `data/dataset_v1/kaggle/` folder and run:

```text
python scripts/data001_finalize.py --generation-dir data/dataset_v1/kaggle --reviews data/dataset_v1/reviews.json
```

The finalizer requires 30 explicit ACCEPT decisions, matches original/generated metadata to the pinned selection, verifies image decoding and 512×512 RGB conversion, groups reverse directions in the same split, rejects unexpected SHA256 duplicate identities, writes 48 train + 12 validation direction pairs, and creates the manifest, QA report, and both mandatory contact sheets. Captions are in `target/<stem>.txt` and reference/target image filenames match the proven AI Toolkit `control_path` contract. It does not train a model.

## Current counts and pending evidence

| Item | Measured now | Final target |
| --- | ---: | ---: |
| Original source candidates | 30/class | — |
| Provisionally selected originals | 10/class, 30 total | 30 accepted |
| Excluded original candidates | 20/class, 60 total | replacements if required |
| FLUX generated counterparts | 0 | 30 accepted |
| Regenerations | 0 | at most one per failed candidate |
| Explicit generated ACCEPT / REJECT | 0 / 0 | 30 / 0 |
| Directional training / validation pairs | 0 / 0 | 48 / 12 |
| Final identity-generation and directional contact sheets | none | both required |

**The source dataset contains source photographs and sketches, not paired hairstyle edits.** The intended training pairs will be project-created by editing the selected originals with pretrained FLUX.2 Klein Base, visually filtering outputs, and expanding accepted identity groups bidirectionally. The custom hairstyle LoRA has not been trained, and identity preservation has not yet been demonstrated for these photographs.

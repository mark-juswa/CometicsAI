# DATA-002 frozen selection and GPU handoff

Status: **frozen for Project Lead review**. No FLUX counterpart, final edit pair, or TRAIN-002 checkpoint exists. The live registry continues to enable only TRAIN-001.

## Source and selection

The original photographic source is `yikaiwang/FaceSketches-HairStyle40`, revision `45de974926fe64551fc2d0b80973335e20ca10e2`. The dataset card declares Apache-2.0; rights in individual celebrity and stock portraits have not been separately verified. Use the `image/` photographs, never the sketches. The source ZIP SHA-256, each selected member path and raw-byte SHA-256, source dimensions, split, target class, and status are frozen in [DATA-002-manifest.json](DATA-002-manifest.json). Its SHA-256 is in [DATA-002-manifest.sha256](DATA-002-manifest.sha256).

All selected images were decoded locally and inspected in the [selection contact sheets](DATA-002-selection-sheets/). The [curation record](DATA-002-curation.json) names every selected train/validation and reserve file and summarizes rejection reasons. The [machine-readable selection report](DATA-002-selection-report.json) lists reserves, rejected files, counts, target balance, and image-hash checks. These sheets supplement exact hashes for identity review; neither hashes nor thumbnails can prove that celebrity identities are unique.

| Source class | Train identities | Validation identities | Reserves | Excluded from V2 selection |
| --- | ---: | ---: | ---: | ---: |
| Afro | 10 | 2 | 4 | 14 |
| BowlCut | 10 | 2 | 4 | 14 |
| Bun | 10 | 2 | 4 | 14 |
| CornRows | 10 | 2 | 4 | 14 |
| DreadLocks | 10 | 2 | 4 | 14 |
| HiTopFade | 10 | 2 | 4 | 14 |
| PixieCut | 10 | 2 | 4 | 14 |
| PonyTail | 10 | 2 | 4 | 14 |
| SpikyHair | 10 | 2 | 4 | 14 |
| WaistLenHair | 10 | 2 | 4 | 14 |

`CurtainedHair` and `HimeCut` were replaced after visual inspection: the former had repeated/soft examples and ambiguous center-part membership; the latter often showed only bangs rather than clear hime side locks. `SpikyHair` and `WaistLenHair` offered clearer usable candidates. The other audited alternatives are recorded in the curation file. `PixieCut/27.jpg` is byte-identical to `SpikyHair/15.jpg`, so only the latter was selected; we also avoided several apparent celebrity repeats across train/validation. All **120 chosen source files** have unique SHA-256 values. A simple image difference-hash check found no near duplicates within its narrow threshold; manual identity review remains the stronger evidence.

## Pairing and calculated budget

Every source style has **two** target neighbors. The graph is two edge-disjoint directed cycles, defined once in `scripts/data002_freeze_manifest.py` and materialized as an explicit `target_style` on each sample in the manifest. Generation and finalization consume the manifest; they do not recalculate the graph. The first cycle follows `BowlCut → PixieCut → Bun → PonyTail → WaistLenHair → DreadLocks → CornRows → Afro → HiTopFade → SpikyHair → BowlCut`. The second follows `BowlCut → Afro → CornRows → DreadLocks → WaistLenHair → PonyTail → Bun → PixieCut → SpikyHair → HiTopFade → BowlCut`. Selected examples alternate between the two edges, including one validation identity for each edge.

The manifest planner calculates **100 train + 20 validation identities**, **120 first-attempt generation jobs**, and, if every counterpart passes review, **200 train + 40 validation directional pairs**. Each target style receives **20 train + 4 validation pairs** from its own originals and incoming edits. Both directions of an identity remain in the same split. These are exact counts for the frozen manifest, conditional on all 120 outputs passing human review. If a rejected case has no acceptable bounded retry/reserve replacement, the finalizer refuses to silently drop it.

`DATA-002-manifest.json` is the source of truth for sample IDs, source paths/hashes, selected status, split, target, prompts via style definitions, generation policy, planning counts, and pair construction. Each `sample_id` also serves as its one-photo `identity_group_id`. The original ZIP and FLUX Base revision are pinned. TRAIN-001 registry and adapter remain untouched.

## Approval gate and fresh Kaggle setup

The generation runner requires the exact manifest hash as an explicit approval argument. **Do not run `--all` until the Project Lead approves the selected classes, source sheets, and pairing graph.** The code must first be available in the GitHub repository the notebook clones. In a fresh Kaggle notebook, select a T4 GPU and enable Internet, then run this setup cell:

```python
from pathlib import Path
import subprocess, sys

repo = Path("/kaggle/working/CometicsAI")
if repo.exists():
    subprocess.run(["git", "-C", str(repo), "pull", "--ff-only"], check=True)
else:
    subprocess.run(["git", "clone", "--depth", "1",
                    "https://github.com/mark-juswa/CometicsAI.git", str(repo)], check=True)

import torch
assert torch.cuda.is_available() and torch.version.cuda, "Select Kaggle GPU and restart the session"
print(sys.executable, torch.__version__, torch.version.cuda, torch.cuda.get_device_name(0))
sys.path.insert(0, str(repo))
from scripts.kaggle_inference_bootstrap import OUT, dependencies
OUT.mkdir(parents=True, exist_ok=True)
dependencies(torch.__version__, torch.version.cuda)
```

Confirm the plan without GPU generation:

```python
subprocess.run([sys.executable, str(repo / "notebooks/data002_generate_kaggle.py"), "--plan"], check=True)
```

**Only after the Project Lead approves this exact manifest**, launch the resumable Supervisor-run bulk job:

```python
subprocess.run([
    sys.executable, "-u", str(repo / "notebooks/data002_generate_kaggle.py"),
    "--all",
    "--approved-manifest-sha256", "901169bf4b8e0e6340708e487cd2a0d4177c5da43b98d6a8e965dc3c59d908d6",
], check=True)
```

The runner uses FLUX.2 Klein Base revision `a3b4f4849157f664bdbc776fd7453c2783562f4d`, FP16 inference, CPU offload on one GPU, 512×512, 20 steps, guidance 4.0, seed 1977. It downloads the pinned source ZIP and Base into `/tmp/data002-hf-cache`, verifies the source ZIP/member hashes, loads Base once, and writes `/kaggle/working/data002/generated/<sample_id>/original.png`, `generated.png`, and `generated.json`. It skips only completed results whose sidecar and hashes verify. Review sheets are written under `/kaggle/working/data002/review_sheets/`. Results remain **PENDING_VISUAL_REVIEW**, never accepted automatically. The manifest hash in `/kaggle/working/data002/manifest.sha256` prevents mixing runs. On a new Kaggle session, restore the entire `data002` output directory before rerunning `--all` to resume.

## Human review, bounded retry, and later finalization

After generation, initialize a review manifest (this writes **PENDING**, not ACCEPT):

```python
subprocess.run([sys.executable, str(repo / "scripts/data002_review.py"), "init",
                "--reviews", "/kaggle/working/data002/reviews.json"], check=True)
```

For each image, visually compare original/result in the review sheets and explicitly set `status` to `ACCEPT`, `REGENERATE`, or `REJECT`, with a review note and the accepted attempt number. Accept recognizable hairstyle/identity with no severe artifacts or major scene/pose replacement. Minor hair-color, light, clothing-detail, or accessory drift may pass. The summary command checks all decisions:

```python
subprocess.run([sys.executable, str(repo / "scripts/data002_review.py"), "summary",
                "--reviews", "/kaggle/working/data002/reviews.json"], check=True)
```

For one decision marked `REGENERATE` at attempt 1, run exactly one seed-only retry:

```python
sample_id = "<sample_id_from_review_summary>"
subprocess.run([
    sys.executable, "-u", str(repo / "notebooks/data002_generate_kaggle.py"),
    "--retry", sample_id,
    "--reviews", "/kaggle/working/data002/reviews.json",
    "--approved-manifest-sha256", "901169bf4b8e0e6340708e487cd2a0d4177c5da43b98d6a8e965dc3c59d908d6",
], check=True)
```

Review the new `generated_r2.png`, then set `ACCEPT` with `attempt: 2`, or `REJECT`. There is no third attempt. A reserve replacement requires an explicit documented manifest revision before generation and must not cross identity splits.

Only after **all 120 explicit ACCEPT decisions**, finalize with:

```python
subprocess.run([
    sys.executable, str(repo / "scripts/paired_dataset.py"), "finalize",
    "--manifest", str(repo / "docs/data/DATA-002-manifest.json"),
    "--generation-dir", "/kaggle/working/data002/generated",
    "--reviews", "/kaggle/working/data002/reviews.json",
    "--output", "/kaggle/working/data002/final",
], check=True)
```

The finalizer validates generation provenance, hashes, captions, image decoding/RGB/size, duplicate images, class balance, and train/validation grouping before writing `final/train|val/reference|target`, manifests, QA report, and both identity and directional contact sheets. Training is a later phase. Before ending a Kaggle session, preserve `/kaggle/working/data002` as a Kaggle output or archive; `/tmp` model caches are temporary and need not be saved.

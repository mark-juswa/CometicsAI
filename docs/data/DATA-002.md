# DATA-002 Philippine hairstyle reassessment and GPU handoff

Status: **revised selection frozen for Project Lead review**. No FLUX counterpart, final edit pair, or TRAIN-002 checkpoint exists. The live registry continues to enable only TRAIN-001. The previous technical shortlist and hash are preserved in [DATA-002-technical-shortlist](DATA-002-technical-shortlist/); its approval hash is superseded.

## Source and selection

The original photographic source is `yikaiwang/FaceSketches-HairStyle40`, revision `45de974926fe64551fc2d0b80973335e20ca10e2`. The dataset card declares Apache-2.0; rights in individual celebrity and stock portraits have not been separately verified. Use the `image/` photographs, never the sketches. The source ZIP SHA-256, each selected member path and raw-byte SHA-256, source dimensions, split, target class, and status are frozen in [DATA-002-manifest.json](DATA-002-manifest.json). Its SHA-256 is in [DATA-002-manifest.sha256](DATA-002-manifest.sha256).

All selected images were decoded locally and inspected in the [Philippine-priority selection contact sheets](DATA-002-ph-selection-sheets/). The [requested-class audit](DATA-002-ph-audit/), [replacement audit](DATA-002-ph-alternatives/), and [final class gate audit](DATA-002-final-gate-audit/) show the source photographs. The [curation record](DATA-002-curation.json) names every selected train/validation and reserve file and summarizes rejection reasons. The [machine-readable selection report](DATA-002-selection-report.json) lists reserves, rejected files, counts, target balance, and image-hash checks. These sheets supplement exact hashes for identity review; neither hashes nor thumbnails can prove that celebrity identities are unique. Hairstyle relevance to Philippine users is a product hypothesis; the source portraits are not a representative Filipino-identity sample.

| Source class and proposed display style | Train identities | Validation identities | Reserves | Screened usable | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `CurtainedHair` — Curtain Hair | 10 | 2 | 2 | 14 | 16 |
| `undercutSidepart` — Side-Part Undercut | 10 | 2 | 3 | 15 | 15 |
| `SpikyHair` — Spiky Hair | 10 | 2 | 4 | 16 | 14 |
| `UndercutPompadour` — Pompadour Undercut | 10 | 2 | 4 | 16 | 14 |
| `PonyTail` — Ponytail | 10 | 2 | 4 | 16 | 14 |
| `PixieCut` — Pixie Cut | 10 | 2 | 4 | 16 | 14 |
| `ShoulderLenHair` — Shoulder-Length Hair | 10 | 2 | 4 | 16 | 14 |
| `WaveHair` — Wavy Hair | 10 | 2 | 4 | 16 | 14 |
| `shag` — Shag Hair | 10 | 2 | 2 | 14 | 16 |
| `Bun` — Bun | 10 | 2 | 4 | 16 | 14 |

Each selected source folder contains 30 raw photographs. Screened usable means selected plus reserve, based on visible hairstyle, face visibility, image quality, and apparent identity separation. The final gate replaced `Fauxhawk` with `SpikyHair`: many Fauxhawk photos show generic spikes or quiffs rather than a clear central strip, while the selected SpikyHair photos visibly show upright spikes. The 12 selected SpikyHair portraits are male-leaning to reduce overlap with `PixieCut`; four reserves remain. `Perm` overlaps `WaveHair` and the chemical process is not visible in a photograph; `CombOver` mixes side parts with baldness-covering combovers, wigs, and parody; `UndercutCurly` often lacks visibly short sides; `UndercutLong` has clear examples but several hidden undercuts and profile views. `Crop` does not truthfully depict men's Textured Crop. `CurtainedHair` and `shag` have only two screened reserves and remain lower-confidence labels. All **120 chosen source files** have unique SHA-256 values. A simple difference-hash check found no near duplicates within its narrow threshold; manual identity review remains the stronger evidence.

Final gate comparison of the original-photo sheets (raw file counts are not usable-identity counts):

| Folder | Raw photos | Visual decision |
| --- | ---: | --- |
| `Fauxhawk` | 30 | Some clear central peaks, but many quiffs, ordinary spikes, children, and repeat celebrities weaken the truthful label. Prior screening had 12 selected and 3 reserves. |
| `SpikyHair` | 30 | Clearly upright spikes can support 10 train, 2 validation, and 4 reserves after excluding pixie-like cuts and apparent repeats; a truthful and familiar Spiky Hair label. Selected. |
| `Perm` | 31 | Many usable curly portraits, but a perm process is not visible, and a Curly Hair label would overlap `WaveHair`. |
| `UndercutLong` | 30 | Some clear long hair with shaved sides, but others hide the shaved side or show profile/rear views; a more niche catalog option. |
| `UndercutCurly` | 30 | Several curly cuts lack visibly short sides; a strict 12-identity undercut selection is uncertain. |
| `CombOver` | 29 | Mixes modern side parts, baldness-covering combovers, wigs, and parody, with apparent repeats; no consistent truthful label separate from `undercutSidepart`. |

## Pairing and calculated budget

Every source style has **two** target neighbors. The graph is two edge-disjoint directed cycles, defined once in `scripts/data002_freeze_manifest.py` and materialized as an explicit `target_style` on each sample in the manifest. Generation and finalization consume the manifest; they do not recalculate the graph. Cycle A is `CurtainedHair → undercutSidepart → UndercutPompadour → SpikyHair → PixieCut → ShoulderLenHair → WaveHair → shag → Bun → PonyTail → CurtainedHair`. Cycle B is `CurtainedHair → SpikyHair → undercutSidepart → PonyTail → Bun → ShoulderLenHair → shag → WaveHair → PixieCut → UndercutPompadour → CurtainedHair`. Selected examples alternate between the two edges, including one validation identity for each edge.

The manifest planner calculates **100 train + 20 validation identities**, **120 first-attempt generation jobs**, and, if every counterpart passes review, **200 train + 40 validation directional pairs**. Each target style receives **20 train + 4 validation pairs** from its own originals and incoming edits. Both directions of an identity remain in the same split. These are exact counts for the revised manifest, conditional on all 120 outputs passing human review. If a rejected case has no acceptable bounded retry/reserve replacement, the finalizer refuses to silently drop it.

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
    "--approved-manifest-sha256", "80772b55df3c48c0a195bf6b4cc5b83c02be36ff43d084e393d903eec4288718",
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
    "--approved-manifest-sha256", "80772b55df3c48c0a195bf6b4cc5b83c02be36ff43d084e393d903eec4288718",
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

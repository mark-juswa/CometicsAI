# DATA-002 — proposed second adapter group (review gate)

Status: **SUPERSEDED by [the frozen DATA-002 selection and handoff](DATA-002.md).** This page preserves the earlier proposal for comparison; its classes and graph are no longer the generation contract. No generation, training, or live enablement has occurred.

## Source inspection

Source: local `data/source/FaceSketches-HairStyle40.zip`, the same archive audited for DATA-001, from `yikaiwang/FaceSketches-HairStyle40` revision `45de974926fe64551fc2d0b80973335e20ca10e2`. The dataset card declares Apache-2.0; individual photograph rights remain unverified. `python scripts/data002_source_audit.py` decoded source photos directly from the archive and produced [inventory and contact sheets](DATA-002-audit/inventory.json) for 18 classes. The source ZIP contains 40 original-photo class folders and 1,199 photo entries after excluding macOS metadata. These are **raw candidates**, not approved identities. All ten proposed folders exist. One exact duplicate occurs within Afro (`5.jpg` / `21.jpg`). The inspected `shag/20.jpg` is truncated; `shag` is not proposed.

| Proposed source class | Raw photos | Decode and short side ≥256 px | Visual caveat |
| --- | ---: | ---: | --- |
| `Afro` | 30 | 30 | Several obscured faces or oversized hair framing; one exact duplicate. |
| `BowlCut` | 30 | 29 | Some photos resemble pixie cuts or have unusual cropping. |
| `Bun` | 30 | 29 | Several profile views or product/collage images. |
| `CornRows` | 30 | 29 | Braided variants and side views require selection review. |
| `CurtainedHair` | 30 | 26 | Several small/soft images and overlap with general medium hair. |
| `DreadLocks` | 30 | 29 | Some braids, occlusions, or non-frontal portraits. |
| `HiTopFade` | 30 | 29 | Several side/profile or low-face-area views. |
| `HimeCut` | 30 | 25 | Some low-resolution portraits; bangs alone are not sufficient. |
| `PixieCut` | 30 | 29 | Strong class overall, but overlaps short bowl cuts in a few images. |
| `PonyTail` | 30 | 30 | Many side views; ponytail must be visible. |

The technical counts only establish decodability and minimum dimensions. They do not establish **12 usable, distinct identities per class**. Contact sheets must be used to select and record source images and exclusions before any generation. None of these ten classes repeats the TRAIN-001 target classes `CrewCut`, `BobHair`, or `LayeredHair`.

## Proposed budget

Provisional target: **12 original identity groups per class**, split **10 train / 2 validation**. If all ten classes pass selection, this is 120 originals and at most 120 first-attempt Base edits. Explicit review and at most one bounded retry per failed image remain required. Bidirectional expansion would yield **200 train and 40 validation directional pairs**. Each target class would receive **20 train and 4 validation pairs**. These are calculations from a proposed budget, not selected or generated counts.

The DATA-001 V1 global generation settings (pinned FLUX.2 Klein Base, 512×512, 20 steps, guidance 4.0, seed 1977, FP16 plus CPU offload) are the starting method. At roughly one minute per generation observed in DATA-001, 120 first attempts suggest about two hours of image inference, excluding Base download/load, retries, review, and session interruptions. This is a projection, not a new measurement.

## Pairing plan

Do not generate all cross-class pairs. Give each selected train class **five** originals edited toward each of two designated neighboring styles; give each validation class **one** original to each neighbor. The neighbors form three small, visually related groups:

- `Afro ↔ CornRows ↔ DreadLocks ↔ HiTopFade ↔ Afro` (each class also targets the preceding neighbor);
- `BowlCut ↔ CurtainedHair ↔ PixieCut ↔ BowlCut` (each class targets both other members);
- `Bun ↔ HimeCut ↔ PonyTail ↔ Bun` (each class targets both other members).

Each class has equal incoming and outgoing generation jobs. Every accepted identity contributes one target in its original style and one in its generated alternate style; this yields balanced target counts without a ten-class all-pairs explosion. The exact per-identity target assignment is deferred until the selected images are approved, then frozen in the selection manifest. The grouping is a cost/coverage choice, not a claim that these transformations will preserve identity.

## Implemented foundation and next gate

`backend/app/style_registry.json` currently contains only the three active TRAIN-001 styles and its frozen checkpoint hash. TRAIN-002 is not listed or loaded. The registry contract supports style ID, display name, prompt, adapter ID, training label, and support status; individual styles may later be disabled without invalidating the adapter's trained-style metadata. Kaggle validates every enabled adapter's own hash and metadata before serving it, loads Base once, and switches one LoRA at a time under the existing request lock. [Diffusers 0.40.0 LoRA loading](https://github.com/huggingface/diffusers/blob/v0.40.0/src/diffusers/loaders/lora_pipeline.py) and [adapter unload/selection](https://github.com/huggingface/diffusers/blob/v0.40.0/src/diffusers/loaders/lora_base.py) provide the chosen API. The **actual T4 switch from TRAIN-001 to a future TRAIN-002 checkpoint remains unverified**. The existing TRAIN-001 loading call and adapter bytes are unchanged.

`scripts/paired_dataset.py` is the manifest-driven DATA-002+ planner/finalizer. The manifest explicitly lists each selected identity, source class/member, target class, and split. It calculates class counts, demands balanced target coverage, requires output metadata and explicit ACCEPT reviews, checks image hashes and duplicate identities, preserves reverse directions in one split, writes AI Toolkit-compatible `reference/` and `target/` pairs with captions, and makes paginated contact sheets. DATA-001 scripts and artifacts are unchanged. There is **no DATA-002 manifest or generation runner yet**, because the proposed class/identity selection requires Project Lead review first.

Next approval gate: review these ten classes and the 12-per-class budget, then select actual source identities from the contact sheets. Do not run generation or TRAIN-002 from this proposal.

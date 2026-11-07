# Corrective Makeup DATA admission and Kaggle training handoff

**DONE target admission, DATA finalization and local handoff verification. GPU training, new model evaluation and production integration NOT STARTED.**

The returned `D:/Downloads/makeup-target-quality-review.json` has SHA256 `7e4d0cf3b3941a4bb4121d330f7bebd31bb6bfc39c4dabed3ab22715507b4324`. It records six Natural Makeup acceptances and 72 pending entries. We imported and preserved those exact decisions, then asked whether the remaining entries were intentional. The Supervisor explicitly replied: **“I reviewed all 78 and accept them on all eight criteria.”**

That clarification is bound to the exact existing source, target and caption hashes in `artifacts/makeup-corrective-supervision-20261105/user-quality-review-02-chat.json`, SHA256 `e19b82660e281ecf4102b3857ac1f86ee40a64092e39afb34ae8332c9d803222`. The six existing acceptances remain intact; the other 72 are recorded as accepted by that explicit chat confirmation. Original returns and previous ledgers remain under `human-quality-returns/`. No approval was inferred from pending entries, and no production approval was recorded.

## Final DATA and package

The separate final copy is `.tmp/data_m001/corrective_selection/final_v1/`, schema `DATA-M001-corrective-final-v1`, status FINALIZED. It contains 52 training and 26 validation pairs, twelve training identities and the unchanged two development validation identities. All thirteen styles have four training and two validation identities. All 78 individual quality records pass the existing admission validator. Historical DATA, candidates and old adapter remain intact.

The package uses the existing `scripts/data_m001_package_training.py` and `notebooks/train_m001_kaggle.py`. Input ZIP: `artifacts/makeup001_corrective001_training_20261105.zip`, 198,859,794 bytes, 572 members, SHA256 `12ab2d039e5fd3d7f8f0bdcb891fa0efe1865e1ecd6407bff6b16f7b60ab6312`. It includes the exact frozen catalog, paired images/captions, review/provenance records and standalone validators/runner. No model weights or Hair adapter are included.

The existing recipe remains 250 steps, BF16 training, flowmatch, rank 16 LoRA and the pinned FLUX.2 Klein Base 4B revision `a3b4f4849157f664bdbc776fd7453c2783562f4d`. AI Toolkit stays at `a8dfcf7d7e2b38ccc7b2fb68ece9c6358e61e7a7`. The candidate job is `makeup001_corrective001_250step`. It starts from Base and preserves the old adapter. No architecture, training loss or hyperparameter sweep was introduced.

## Concrete notebook and local verification

The ready notebook is `artifacts/makeup-corrective-supervision-20261105/kaggle-training-handoff-20261106/ready/makeup_corrective001_train.ipynb`, SHA256 `60b7de18694f1b09b40f9b17348c86bd9e8f7c7604f829d046e15d122dcdb769`.

It embeds the frozen ZIP and member hashes, accepts Kaggle's ZIP or unpacked input representation, stages inputs to writable storage, prepares the existing runner, and checks for a T4 and the existing storage prerequisite. It reuses the pinned Toolkit installation with host Torch constraints. Training and evaluation run as separate existing runner phases, with exact final candidate checkpoint/hash selection. Result packaging occurs in a finally block, including partial evidence on failure. An optional recovery cell never repeats training.

The actual notebook helpers were executed locally against this real finalized input ZIP in `.tmp/makeup-corrective-training-preflight-20261106/`. Results:

- All four code cells compile.
- All 572 member hashes verify.
- ZIP staging, unpacked staging and repeated stage verification pass.
- Input tampering and escaped paths are refused.
- The standalone runner validates all 78 human review records and prepares the real 52/26 dataset successfully.
- The generated configuration uses a fresh Base candidate with no pretrained LoRA or resume setting.
- Evaluation resolves all thirteen matching style captions, two development validation people, and 52 Base/new adapter outputs.

These are local data/configuration checks, not GPU training evidence. Initial hardlink creation was denied by the local filesystem; the CPU fixture used an ordinary file copy instead. No data, model or GPU configuration was changed to make that check pass. The earlier unexecuted notebook draft remains preserved beside the ready version.

## Access, preservation and next action

The connected in-app browser shows Kaggle's Login link and no authenticated session. No Kaggle upload, dependency installation, GPU run, trained checkpoint or cloud deployment was performed by Codex. The user must start the supplied notebook in their signed-in Kaggle session, or provide that authenticated session for a later continuation. No additional target review is required for these unchanged 78 pairs.

Existing serving source/contract/release controls and Hair/Nails are unchanged. The new notebook runs separately from serving, and the old dataset, checkpoints, inference bundles, approved targets and failed evidence remain intact.

Next: execute the authorized bounded training job, return the result ZIP, verify actual finite training/checkpoint evidence and assess Base versus the new adapter. Model quality remains NEEDS VERIFICATION. Only a validated model proceeds to real application validation and the Project Lead's production review. The reused development validation identities do not constitute an untouched final test set.

[Run instructions](../guides/makeup-corrective001-training.md), [CPU verification receipt](../../artifacts/makeup-corrective-supervision-20261105/kaggle-training-handoff-20261106/ready/cpu-verification.json), [finalization receipt](../../artifacts/makeup-corrective-supervision-20261105/finalization-01.json).

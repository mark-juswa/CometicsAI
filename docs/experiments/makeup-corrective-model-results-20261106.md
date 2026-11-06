# Corrective MAKEUP model return and application candidate

Date: 6 November 2026. Model training DONE, returned evidence VERIFIED. Supervisor accepts all 26 corrective RAW results for application validation. Complete Makeup IN PROGRESS. Production integration NOT STARTED.

## Actual training and model review

Returned `D:/Downloads/makeup001_corrective001_results.zip` has 147,119,532 bytes, SHA256 `3c55f6b385b1530c9e2913cf0410c3324c35a9b37bf0b017e81ba3683230fefb`. All 70 unique safe members pass CRC. Original ZIP, logs, checkpoints and all evaluation outputs remain under `artifacts/makeup-corrective-supervision-20261105/gpu-return-01/`. Attached executable code and optimizer pickle were not executed.

The separate fresh Base training completed 250 steps and final save, exit zero, with no stop reason. There are 498 finite logged loss entries, including repeated progress entries. That does not mean 498 steps. Final loss is 0.1801. Elapsed time including model setup is 7,947.34 seconds, peak GPU memory 13,529 MiB. Neither loss nor successful saving establishes visual quality.

Final checkpoint: `raw/checkpoints/makeup001_corrective001_250step/makeup001_corrective001_250step.safetensors`, 46,223,632 bytes, SHA256 `991a1037cc892c1a62e1a731be577ed1aec2f331d9568b4586ff3829a4ee32c3`. Safe header and numeric inspection find 160 finite LoRA tensors. Step 125 and optimizer files remain intact. The old MAKEUP checkpoint is separate and unchanged.

Training used finalized DATA with 52 training pairs across 12 people and 26 validation pairs across two different people. Every one of the 13 catalog styles has four training people and both validation people. The paired targets are reviewed synthetic editor targets fitted to the sources, not outputs of this trained model.

Actual environment is Python 3.12.13, Torch 2.10.0+cu128, CUDA 12.8, Tesla T4, AI Toolkit `a8dfcf7d7e2b38ccc7b2fb68ece9c6358e61e7a7`. Base is `black-forest-labs/FLUX.2-klein-base-4B`, revision `a3b4f4849157f664bdbc776fd7453c2783562f4d`, transformer SHA256 `9c5fed22b76baea749d88fc2abe3ad53245e7b21a0d353a762665eea00043b92`. Installed Diffusers commit matches the existing shared serving foundation, `c943837899b16cbae2f619b8dd4f7bb6f07dd81a`. No Hair or historical Makeup adapter was used to initialize corrective training.

All 52 evaluation PNGs are real raw outputs, 26 Base and 26 corrective, with independently matched output and source hashes and 52 distinct output hashes. Each Base/corrective comparison uses the same original portrait, exact new style caption, seed 1977, 20 steps, guidance 4.0 and 512 square. Approved targets were not supplied to inference. No source fitting, skin matching or compositing was applied to the returned raw generations.

Engineering inspected all 26 native outputs, the complete catalog sheets and representative face/eye/mouth detail boards. The new adapter visibly reduces the pronounced Base whitening and plastic reconstruction while producing complete foundation, eye, cheek and lip looks. Strong eye and lip styles, warm gold/bronze and cool silver/blue remain visible. Original scene and recognizable identities are substantially better retained. This is a demonstrated model improvement on the reviewed subjects, not a guarantee of unchanged facial pixels or generalization.

The engineering inspection still notes close Natural/No Makeup looks on one person, darker/crisper berry lips than the muted guide, occasional spiky Manga clusters, some smoothing and imperfect matte/shine separation. These observations remain recorded even though the Supervisor accepts every reviewed result. They do not silently reverse that acceptance or trigger another speculative training sweep.

The source defined eroded forehead diagnostic, without alignment or grading thresholds, changes the median L difference across styles from +7.87 to +0.03 for 054109, and +5.77 to -1.10 for 056266. This supports reduced lightening in that sampled region. It does not prove matched undertone, texture, identity or realism. Full diagnostic values and limitations are in `gpu-return-01/complexion-diagnostics.json`.

Supervisor returns `D:/Downloads/makeup-corrective-model-review.json`, SHA256 `7db6666beb345275462d3358bac1e3db8f431f441caeb2db6f4235c0b573f3df`, reviewer label `Developer`, and says: “Here is the result. it looks great (Corrective adapter RAW, real generation)”. All 26 verdicts are `ACCEPT_FOR_APPLICATION_VALIDATION`. Every identity, style, caption, source, approved target, Base, corrective output and checkpoint binding matches the exported gallery. The original JSON and separate receipt are preserved in `gpu-return-01/human-model-review-01/`. Its `production_approved` field is false.

The complete reviewed catalog is Natural Makeup, No-Makeup Makeup, Soft Glam, Smoky Glam, Dewy Peach, Rosy Pink, Bronze / Golden Glam, Matte Nude, Classic Red Lip, Bold Evening Glam, Cloud-Skin Makeup with Blurred Berry Lips, Manga-Lash Makeup and Icy Silver Eye Makeup. No style was removed.

## Cause assessment and correction

Earlier evidence demonstrates defective pale/smoothed/reconstructed historical targets and one generic caption across all 60 historical pairs. The accepted corrective DATA and explicit 13 style component captions address those supervision defects. The new Base versus corrective comparison demonstrates that the trained adapter can materially improve these outputs under the same inference settings. This does not isolate the contribution of target preparation, caption changes and individual training examples. It does not prove that the old Kaggle runtime itself caused whitening. The current successful evaluation and existing serving runtime use the same pinned Base and Diffusers revision.

The correction belongs in reviewed training supervision and the trained adapter, with exact corresponding style captions at inference. The rejected inference compositors and lip only output are not promoted. The offline teacher fitter remains target preparation only.

## Bounded application implementation

`scripts/package_makeup_corrective_application.py` builds a new immutable candidate using the preserved complete Hair/Nails release. It validates the exact accepted review, frozen catalog and checkpoint before packaging. Both CPU response validation and GPU generation use one matching corrective contract, 13 exact captions and truthful new model metadata. The old 46,223,600 byte checkpoint cannot satisfy this new 46,223,632 byte contract.

The existing shared worker, Hair profile hook, Nails optimization, authenticated facade and generation/status/result contracts are reused. The existing original GPU archive passes its full historical manifest and artifact gates before a separate candidate overlay installs the new checkpoint at `gate1/adapters/makeup-corrective001`. It does not overwrite the old adapter. The original manifest stays unchanged and a new overlay inventory records the candidate changes truthfully. Existing active tensor equality checks remain, with an additional full ordinary PEFT scaling assertion for corrective Makeup. A candidate status field exposes active tensor verification for the probe.

Only generated candidate copies of `makeup_contract.py`, `makeup_styles.py`, `makeup_inference_server.py` and `unified_gate3_server.py` are changed. Their production repository counterparts remain exact. The three held Makeup additions are exposed in this isolated candidate API for testing; their production release remains held. Candidate catalog totals are 18 Hair, 13 Makeup and 8 Nails. The candidate's existing Hair/Nails release identifier is retained, while its separate Makeup candidate inventory is explicit. It is not registered as a new production release.

The new three cell notebook reuses pinned startup and dependency guards. After authenticated local application readiness, it returns before the public tunnel and website registration steps. It cannot take over the production website endpoint. No UI, database, secret, dependency or checkpoint family change is introduced.

`scripts/makeup_corrective_application_probe.py` submits 13 Makeup generations through the actual authenticated application facade and polls admitted jobs without replaying generation POSTs. It interleaves both expanded Hair adapter routes and one existing Nails GPU crop, checks worker tensor verification and foundation load count, validates the corrective model/captions/settings, preserves raw outputs and builds Original | Accepted model RAW | Application RAW comparisons. It records byte equality to accepted outputs without making equality a visual quality claim. The Nails crop checks ownership and restoration, not full hand fitting.

Package and handoff are in `artifacts/makeup-corrective-supervision-20261105/application-candidate-01/`:

| Artifact | Exact binding |
|---|---|
| New CPU candidate | `makeup_corrective001_application_candidate_20261106.bin`, 75,233,903 bytes |
| CPU SHA256 | `be312de50d6e8d44f304dc095134485232e54c57db3edcaa953cc66f3402214d` |
| Notebook | `makeup_corrective001_application.ipynb` |
| Notebook SHA256 | `a74640ad59ba0592e7a58c07b0c12774b7b7b7cfce7920d7b36cc1354804b3d0` |
| Existing GPU input | `capstone_train002_20260928_v1.bin`, unchanged |
| GPU SHA256 | `f0d1fed52e00b6c5a1da2cade3731237675cdebbfc0b2cde3b2dbda99a4019ac` |

## Local verification and preservation

62 focused tests pass: candidate admission, exact 13 captions, wrong review/output/settings refusal, historical Makeup runtime/package, expanded Hair and unified worker regressions. The exact pytest command and observed summary are retained in the candidate verification receipt.

Actual new CPU and original GPU archives pass the existing extraction/hash/CRC/inventory checks. The actual notebook preparation, original GPU historical gates, fresh overlay install and nested worker bootstrap compilation pass. A fresh staged process verifies the actual new checkpoint contract, all 13 Makeup API routes through simulated remote transport, 18 installed Hair and 8 Nails entries, unknown style refusal, and rejection of old checkpoint/wrong profile/inactive LoRA responses. This CPU transport fixture does not claim GPU output or visual quality.

Initial sandbox FastAPI checks stalled and were stopped. The successful checks ran with local test transport access outside the sandbox. An earlier preflight assertion compared escaped Windows code text; it was corrected to inspect the parsed path argument. Previous preflight workspaces remain; no application bug or model failure is inferred from that assertion. See `cpu-preflight.json` for the successful actual run.

All eight frozen serving/release controls, the original preferred lip helper and both original CPU/GPU release archive hashes are unchanged. Historical datasets, training results, checkpoints, failed experiments and approved targets remain intact. No new GPU generation/training, Git publication or cloud deployment occurred in preparing this application candidate.

## Remaining milestone

DATA finalization DONE. Corrective model training DONE. Base comparison and all 26 human model verdicts DONE. Local application candidate/preflight DONE. Real shared GPU application run NOT STARTED. Fresh uploaded portrait, live website/manual and consultation paths, save/book, mobile and production review remain NEEDS VERIFICATION. The two existing validation people were reused during development and are not an untouched final test set.

Next run the supplied application notebook on the existing compatible Kaggle foundation and return `makeup_corrective001_application_results.zip`. This is application validation, not another target audit or training run. After its actual evidence is checked, prepare the matching production model/catalog release and website rollout for project lead approval. Do not silently substitute the checkpoint into the old serving contract or claim deployment from the successful raw gallery alone.

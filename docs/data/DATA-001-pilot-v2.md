# DATA-001 Pilot V2: masked hairstyle editing

**Status: PREPARED, KAGGLE RUN PENDING.** The approved three-image pilot is `CrewCut_1 → BobHair`, `BobHair_1 → LayeredHair`, and `LayeredHair_4 → CrewCut`. Do not generate the other 27 or mark any result accepted before visual review.

## Pinned components and API

- Existing AI Toolkit requirements pin Diffusers to `c943837899b16cbae2f619b8dd4f7bb6f07dd81a`; that source exports `Flux2KleinInpaintPipeline`. Its call accepts `image`, `mask_image`, `strength`, `num_inference_steps`, `guidance_scale`, and `generator`. White mask pixels are repainted; black pixels are preserved. The installed Kaggle build is checked at runtime and the runner stops if the class or arguments are missing. The prior V1 used `Flux2KleinPipeline`; V2 uses the inpaint variant.
- FLUX model: `black-forest-labs/FLUX.2-klein-base-4B` at `a3b4f4849157f664bdbc776fd7453c2783562f4d`. FP16, CPU offload, GPU 0, 512×512, 20 steps, guidance 4.0, seed 1977. The inpaint pipeline uses `strength=0.8` (its documented default). This is the necessary V2-specific parameter; all other V1 inference settings stay fixed.
- Parser: `jonathandinu/face-parsing` at `758b82e15a0178c9db39c1ff666a8b56e3a550c8`. Its model card documents CelebAMask-HQ training and 19 labels, including hair (13), skin/face/facial features (1–12), earrings (15), necklace (16), neck (17), and clothing (18). The pinned model card does **not** declare a model license. The runner uses its 512×512 RGB image processor on CPU with `SegformerForSemanticSegmentation` and safetensors. This is offline DATA-001 preprocessing only.

## Mask construction

The runner upscales semantic logits to 512×512, takes label 13 as the raw hair mask, expands the hair region by 32 pixels, and subtracts a four-pixel expansion of protected face, feature, hat, jewelry, neck, and clothing labels. The full source hair extent is included so long hair can be removed. It stops if the hair detection is implausibly small or large, less than 80% of source hair remains editable, or more than 48% of the whole image is editable. These checks catch obvious segmentation failures; they do not certify a visually good mask. The pipeline blends outside the mask in latent space, so the runner copies original RGB pixels outside the final mask after decoding. White in `editable_mask.png` means editable.

Masks may still cover nearby background, and a parser can misclassify hair, clothing, or accessories. The 512×512 edge may be imperfect after pixel compositing. Visual review of the source, semantic map, raw hair mask, final mask, and result is mandatory.

## Run and review

Use the same CUDA-enabled Kaggle environment as V1, with the repository at `/kaggle/working/CometicsAI` and V1 artifacts at `/kaggle/working/data001`. Run:

```bash
cd /kaggle/working/CometicsAI
git pull --ff-only
mkdir -p /kaggle/working/data001/pilot_v2_masked
/usr/bin/python3 notebooks/data001_pilot_v2_masked_kaggle.py 2>&1 | tee /kaggle/working/data001/pilot_v2_masked/run.log
```

If the previous Kaggle working directory is unavailable, upload the Supervisor's V1 `data001_pilot.zip` to Kaggle and pass `--v1-zip /path/to/data001_pilot.zip`; the runner verifies V1 image hashes before use. Use the CUDA Python interpreter from EXP-001, not a CPU-only interpreter. The runner reuses `/tmp/hf-cache` and writes only review artifacts under `/kaggle/working/data001/pilot_v2_masked/`.

For each sample it writes `semantic_labels.png`, `raw_hair_mask.png`, `editable_mask.png`, `mask_metrics.json`, `result.png`, and `generation.json`. It also writes `environment.json` and `v1_v2_comparison.jpg`. Metadata records exact hashes, revisions, prompt, settings, runtime, and peak allocated GPU memory. The comparison is `V1 RESULT | SOURCE | MASK | V2 RESULT` for all three. Review decisions remain pending; no pair builder or training runs.

After the pilot stops, package its small review artifacts for the Project Lead:

```bash
python3 -c "import shutil; shutil.make_archive('/kaggle/working/data001_pilot_v2', 'zip', root_dir='/kaggle/working/data001', base_dir='pilot_v2_masked')"
```

**Runtime status:** Exact Kaggle inpaint compatibility, three outputs, per-image runtime, peak VRAM, and visual preservation remain **NEEDS VERIFICATION** until the Supervisor runs this script and returns its artifact archive/log. Any missing inpaint class or structural runtime failure is a stop condition, not a reason to substitute another pipeline.

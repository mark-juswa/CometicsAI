# AI-assisted source-based Makeup pilot — 26 October 2026

**Offline implementation/execution DONE; integrity checks VERIFIED; appearance EXPERIMENTAL and human approval PENDING. Not integrated or deployed.**

## What was built

[scripts/makeup_source_render.py](../../scripts/makeup_source_render.py) runs the cached SegFormer face parser on an original portrait, derives source-coordinate lip/eyelid/cheek fields, and renders cosmetic color while retaining the original image as its canvas. No full-face foundation layer, smoothing, warping or generated face is used.

This is an AI-assisted virtual try-on. The AI region parser is pretrained external technology; the region-placement, pigment, profile and validation logic is project code. It does not invoke the trained generative MAKEUP-001 adapter. Runtime/provenance flags explicitly say lora_active=false and project_trained_generator_used=false.

The Supervisor approved this method in principle and then authorized the three-style/four-person pilot. No production route, contract, model, app catalog or cloud configuration was changed.

## Frozen inputs and actual execution

Four original DATA-M001 source photos were reused: 054109, 056266, 006553 and 035149. All input hashes, original photo credits and licenses are retained in the plans and private source-credits.json. These are development images, including earlier training/validation subjects, not untouched final evaluation. Some sources already wear cosmetics; this experiment is not a bare-face ground-truth study.

Three profiles: Natural Makeup, Soft Glam and Classic Red Lip. **12 outputs** with no hand-painted per-photo regions or per-person profile changes.

- [Initial plan](../../data/makeup/MAKEUP-RENDER-001/plan.json).
- [Color-corrected plan](../../data/makeup/MAKEUP-RENDER-001/plan-gamut-v2.json).
- [Machine-readable verification and review](makeup-source-render-pilot-20261026.json).
- [Focused synthetic tests](../../backend/tests/test_makeup_source_render.py).
- Private results: artifacts/makeup-render-20261026/run-02.
- Review ZIP: artifacts/makeup-render-20261026/beautycore-source-makeup-pilot-review.zip.

Cached parser weights/configuration/preprocessor hashes were verified, including model.safetensors SHA256 c2bec795a8c243db71bd95be538fd62559003566466c71237e45c99b920f4b62. Loading uses local_files_only on CPU. Four automatic region overlays were inspected before cosmetic rendering.

## Rendering and one implementation correction

Lips use source lip labels, inner-mouth exclusion, inward feathering, pigment chroma and retained local luminance variations. Eyelid placement follows the source eye contour and brow gap; liner darkens a narrow strip of eyelid skin. Blush is a low-opacity spatial field below/outside each eye, clipped to source facial skin and away from protected features. No overall complexion matching or generated-minus-source transfer is performed.

run-01 revealed a specific defect: saturated red pigment at overly constrained lip lightness exceeded the output RGB range and clipped. Original outputs, plan and runner are preserved. run-02 keeps the same four sources, masks, pigment colors and opacities, increases only the allowable target shade lightness adjustment on lips for Red Lip, and maps out-of-gamut chroma into range while retaining hue direction and local lightness. This is not whole-face darkening or another global opacity sweep.

The implementation follows [OpenCV's documented Lab/D65 conversion](https://docs.opencv.org/4.13.0/de/d25/imgproc_color_conversions.html). Color-conversion and gamut safeguards are also checked on synthetic known inputs. Correct numeric colors do not prove realistic cosmetics.

A zero-opacity safeguard was added after execution; all12 saved results were independently reproduced pixel-for-pixel with the current runner. The executed runner snapshot/hash and current runner/hash remain separately recorded.

## Actual review

Codex inspected all four source/region overlays, both versions' comparison sheets, and native-resolution Soft054109 and Red056266 outputs after the color correction.

- The original face, complexion, texture, expression, hair, clothing and scene remain recognizable. There is no new whole-face foundation/retouching mask as in the rejected generated-face tone trial.
- Natural changes are subtle, mainly rose lip tint with modest eye/cheek effects.
- Soft Glam reads most clearly through its mauve lip. Eye/cheek changes are less dramatic than a full salon glam look; new lashes, foundation and full-face finishing are not provided.
- Red Lip is distinct and visible, but can still look strongly painted, and lip-boundary/intensity quality needs user/salon review, especially on open-mouth smiles.
- Original upper/lower lip contrast and highlights remain; this can make the added pigment look uneven in some examples.
- Existing cosmetics, flash highlights, blemishes and texture are not removed. These remain visible because preserving the source is deliberate.

Disposition: **SOURCE_PRESERVATION_PROMISING_COSMETIC_FIDELITY_PENDING**. No case has been marked human ACCEPT. This is not a claim that the requested natural appearance or all current10Makeup styles are solved.

## Technical validation

Command: python -m pytest backend/tests/test_makeup_source_render.py -q

**24 passed.** Tests cover source/protected-pixel preservation, reproducibility, zero-opacity no-op, distinct synthetic profile outputs, missing/ambiguous regions, invalid strengths, color inversion/gamut mapping, metadata truthfulness, source tampering/path escape and evidence overwrite refusal.

Independent checks on all12 saved PNGs confirm:
- Exact original pixels outside permitted cosmetic support.
- Exact original parser-protected eyes/brows, inner mouth/teeth, nose, neck and nonfacial regions.
- An inspected central forehead patch is unchanged.
- Saved output hashes and all source/parser-map hashes match records.
- Current code reproduces all12 results without another parser/model load.
- No diff in the six production Makeup API/style/contract/worker files checked.

These checks are against parser-proposed regions, not calibrated human boundary ground truth. They cannot establish reliable behavior on arbitrary faces or photographs.

Recorded render-only times were about0.20–0.35seconds per image on this CPU, excluding face parsing, image I/O, queueing and network. This is **not online latency or a full-system speed benchmark**. No generative GPU call or new training occurred.

## Next gate

The Supervisor/salon should review all four sheets, particularly lip edge blending and whether Natural/Soft changes are sufficiently visible and distinct. Do not automatically deploy or broaden profiles.

If the appearances are accepted, test automatic region handling on more suitable existing photos and real client inputs with permission, then implement a truthful versioned renderer contract, supported-style catalog, shared consultation/save/book integration and coordinated Kaggle/Render rehearsal. The [deployment recovery plan](makeup-deployment-recovery-plan-20261026.md) remains the integration outline. Old models, saved looks and rollback artifacts remain intact.

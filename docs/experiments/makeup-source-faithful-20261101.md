# Source-faithful subtle complexion refinement — 1 November 2026

**Offline implementation DONE; technical evidence VERIFIED; appearance HUMAN-REJECTED. No deployment.**

**Requirement correction:** The user explicitly rejected this output because it removed the desired makeup. The interpretation below is retained as historical experiment context, not the current requirement. Original-person fidelity and selected makeup preservation must both hold. See [follow-up](makeup-selected-cosmetics-20261101.md).

## Updated requirement

The Supervisor says the earlier complexion blend is better, but the face still looks regenerated and too different. Their explicit new priority is subtle, realistic complexion retouching with original facial features, expression, skin texture, imperfections, lighting, hairstyle and background preserved. This prioritizes source fidelity over the earlier request for stronger full-look cosmetics in this particular refinement. It is not blanket approval to remove or replace existing Makeup services.

Color correction on a regenerated face cannot recover the original facial structure or skin texture that the model changed. This prototype therefore uses the actual original photo as the output canvas. A previous corrected Natural Makeup output supplies only a low-frequency color reference; none of its regenerated face pixels, geometry, smoothing or enhancements becomes the output canvas.

## Implementation

- Hash-verified originals, prior corrected references and cached source/raw parser maps are reused.
- Only the primary face is editable. Comparable multiple-face regions are rejected; small background face regions remain original.
- Align the color reference into original coordinates. Never resize/warp the original canvas.
- Estimate smooth skin color differences only; remove the global reference cast so the person's overall undertone remains the baseline.
- Limit local chroma differences to two color-code units at20percent strength, with a smooth inward skin transition.
- Preserve original per-pixel luma; compute color-only RGB offsets and shrink only the proposed offset near gamut boundaries.
- Copy original RGB outside allowed primary facial skin exactly. Eye/lip/teeth/brow/nose/hair/clothing/background regions are not beautified.
- Do not blur the original photograph or synthesize texture, lashes, highlights or facial geometry. Blur is used only to estimate low-frequency color.

The operations follow [OpenCV's documented RGB/YCrCb coefficients](https://docs.opencv.org/4.13.0/de/d25/imgproc_color_conversions.html). This is a custom bounded post-processing prototype, not a raw output of a newly trained generative model.

## Observed results

Two existing512-square development photos were tested. Both new outputs remain very close to the original. Original freckles, facial detail, expressions, smiles/teeth, hair and scene remain visible. The change is intentionally a faint skin-color refinement, not a full cosmetic makeover.

Maximum RGB changes are4/255 and3/255. Maximum luma error is0.484/255 from final8bit rounding; the floating-point adjustment is orthogonal to original luma. All checked non-skin/protected source pixels and non-primary-face pixels remain exact. Skin pixels are not claimed RGB-identical.

Eighteen focused tests pass: input/evidence/strength guards, identical-reference no-op, rejection of global reference cast, known texture/feature preservation, near-gamut safety, background-region protection, ambiguous-face refusal and exact reproduction of both saved real outputs.

The gallery has six comparison images and two full-size original/retouch toggles. Edge enlargement, toggle behavior,390pxmobile layout and zero script errors pass. [Open the review](../../artifacts/makeup-faithful-20261101/review-v2/review-self-contained.html).

## Limits and next gate

Technical constraints do not establish universal naturalness, professional photographic quality or all-person identity accuracy. The face parser is not ground-truth annotation. The prototype currently handles only the two512-square development examples and one subtle complexion profile; native-resolution upload handling and the existing full Makeup catalog are not implemented by this pilot.

Review the original/new toggle first. If this level of fidelity is useful, validate additional permitted originals, native-resolution handling and uncertain face-region behavior, then separately specify a truthful versioned service path. Do not automatically increase cosmetic strength or claim strong Makeup style coverage: the latest brief explicitly asks for minimum changes.

No new photos, model inference, diffusion/GPU generation, training, downloads, packages, serving/UI changes, database writes, secrets, Git publication or cloud deployment occurred. Current Makeup service, Hair/Nail release63fc851 and its packaged artifacts remain unchanged. Earlier complexion and source-renderer evidence is preserved.

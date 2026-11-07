# Offline Makeup source layer workflow

4 November 2026. **Implementation VERIFIED locally; full look appearance NEEDS VERIFICATION.**

This prepares and reviews source fitted cosmetic targets. It does not replace the real MAKEUP model, automatically fit a new upload, or enable an application style. The Supervisor selected artist/salon authored layers. No approved full look layer pack exists in the repository yet.

## Asset contract

A pack contains a `makeup-source-layers-v1` JSON document and one coverage map per layer. The document names the existing `style_id`, source RGB pixel SHA256, parser label pixel SHA256, `scope` (`component` or `full_look`), `production_enabled: false` and individual `layers`.

Each layer names its unique `id`, `kind`, relative `alpha_path`, decoded float32 `alpha_sha256` and explicit `palette_lab` triplet. Supported pigment kinds are lip, eyeshadow, liner, blush, contour and highlight. Coverage is an original 512 by 512 float32 NPY in 0..1, or a grayscale PNG divided by 255. PNG quantization changes the mask and therefore its pixel hash. Paths must remain within the document directory.

The artist fits coverage to the actual source features and reviews soft transitions at native size. The renderer does not warp the source or infer a new mask from a generated face. Lip coverage must remain on source lip labels; other pigment must remain on primary face skin. Source eye interiors, brows, mouth interior, nose, hair, clothing and scene are protected. Parser support is a protection estimate, not anatomical ground truth. Out of region or overlapping masks are refused; the artist must resolve their coverage explicitly. At least 40 fully covered pixels anchor each material to the source. Very small or entirely translucent masks currently require a future reviewed anchor design.

`artist_review` contains a named `reviewer`, `role` (`artist` or `salon`), `decision: ACCEPT` and review `evidence`. These are attestations, not authenticated proof of who reviewed the asset. A reviewed component does not establish that a complete style is reproduced. Missing lashes, sparkle, gloss, matte/dewy finish or exact reference shade cannot be declared implemented by a pigment layer.

The original lightness variation is retained under a bounded constant material offset inside uniform coverage. Blush cannot change source lightness; an unsafe black/white source range is refused instead of lifted. Gamut compression may reduce color saturation. This is a bounded color operator, not a calibrated physical model of skin, undertone or cosmetics.

## Application and review

For a real reviewed asset pack:

```powershell
python scripts/makeup_source_layers.py --portrait source.png --labels labels.png --layers layers.json --output new-result.png
```

Only an explicit `--development-only` permits an unapproved component proof. It remains marked experimental and cannot authorize training or release. Existing output images or receipts are never replaced. The result receipt binds the document, mask files and output pixels.

The six source bound example documents in `artifacts/makeup-architecture-20261104/review-validated/` are regression fixtures. Their coverage comes from the retained parser/landmark estimate and their lip palette comes from old generated guides. They are explicitly **not artist/salon assets**, not new full looks, and not accepted training data. They reproduce the previously preferred lip pixels exactly. Source image, labels, credits and original checksums are recorded in the adjacent review JSON.

## Corrective data gate

`data_m001_paired.py prepare` now writes a pending `target_quality.json`. Historical `approve-all` does not fill or approve this document. Each included pair needs an individual decision bound to pair ID, identity, split, source/target hashes and caption. All eight criteria must explicitly pass with observations: identity/geometry, complexion/undertone, texture/shading, cosmetic placement/blending, visible style fidelity, protected content, provenance/rights and truthful annotations. Both source and target annotations describe eyes, lips, blush, complexion finish, brows and contour/highlight. An archive suffix is never a style label.

`finalize --quality-review PATH` validates that separate review before copying targets. The default path is the candidate's `target_quality.json`. The packager and standalone Kaggle runner revalidate the review and images before training preparation or GPU preflight. A pinned policy refuses all 60 unchanged rejected historical targets, including lossless reencoding of their decoded RGB. This is not a perceptual duplicate detector; modified near duplicates still need review. The original ledger, photos, old approvals, training archives and model are preserved.

The existing runner still uses its proven 50/10 paired layout, source archive pin and FLUX/LoRA foundation. New source collection or changed pair counts need a separate reviewed training configuration. An accepted artist render does not bypass this gate, change the caption automatically, establish dataset rights, or prove that a newly trained adapter will reproduce it.

Next: acquire and review complete source fitted looks across representative original complexions and catalog families. Then prepare truthful pairs and retain an independent final acceptance set. These reused development portraits cannot supply untouched final acceptance. Finalization, corrective training, Base comparison and production integration remain separate milestones.

# Seven remaining source-based Makeup styles — 26 October 2026

**Offline implementation/execution DONE; integrity VERIFIED; appearance and description fidelity EXPERIMENTAL. Not deployed.**

## Delivered scope

Supervisor authorizes proceeding after the seven remaining existing styles were identified. This run adds **28 previews: seven profiles on the same four original portraits**. The earlier12Natural/SoftGlam/RedLip previews remain unchanged and reproduce exactly. Together there are **40 offline examples for all10existing Makeup styles**.

This authorization is not recorded as human appearance ACCEPT for the earlier profiles, the new profiles, or production deployment. Cloud-Skin Berry, Icy Silver and Manga-Lash expansion candidates are outside this run.

- [Implementation](../../scripts/makeup_source_styles.py), using the unchanged [baseline renderer](../../scripts/makeup_source_render.py).
- [Frozen seven-style plan](../../data/makeup/MAKEUP-RENDER-002/plan.json).
- [Verification, case review and review-ZIP receipt](makeup-seven-styles-20261026.json).
- [Extension tests](../../backend/tests/test_makeup_source_styles.py).
- Private results: artifacts/makeup-render-20261026/remaining-seven-01.
- All-ten gallery: artifacts/makeup-render-20261026/all-ten-review/review.html.
- ZIP: artifacts/makeup-render-20261026/beautycore-all-makeup-review.zip.

Extract the full ZIP and open review.html. It provides original-plus-ten cards for each person, clickable native PNGs, all-style comparisons, eye/lip detail sheets and source credits. All97local HTML image/link references were checked; ZIP CRC passed. It is a review artifact, not a published website or server package.

## What the additional profiles actually provide

| Existing style | Implemented trial effect | Verified limit / appearance observation |
|---|---|---|
| No-Makeup Makeup | Very light lip/eye/blush addition. | Often close to original, as intended. Does not remove pre-existing cosmetics, conceal blemishes or even full-face tone. |
| Smoky Glam | Darker diffused upper-eye shade, a restrained lower-eye band, liner and nude lip. | Eye depth is restrained on some people; this has not established a dramatic blended salon smoky eye. No added lashes. |
| Dewy Peach | Peach lip/cheek pigment, small cheek highlights and enhancement of existing lip highlights. | Local dewy effect only; original forehead shine and underlying skin are retained. Highlight difference can be subtle. |
| Rosy Pink | Coordinated pink lip, eyelid and blush pigment. | More distinct lip color; source upper/lower lip contrast can look strong or painted and needs review. |
| Bronze / Golden Glam | Bronze/gold eyelid tint, localized sheen and warm nude lip. | No whole-face bronzing or physically simulated glitter/metal. Eye pigment can look yellow rather than metallic. |
| Matte Nude | Muted nude/neutral pigment and localized lip-highlight attenuation. | Lip-only matte finish. The original face can still look shiny; not full-face matte foundation. |
| Bold Evening Glam | Deeper plum upper/lower-eye treatment, stronger liner and berry lip. | Strong lip-edge/intensity review needed. Does not add false lashes, sculpt face geometry or replace foundation. |

These limits must be reflected in future product naming/descriptions or capability decisions. Do not advertise complete legacy prompt fidelity from successful execution.

## Source preservation and implementation

The original portrait remains the canvas. No replacement face, full-face whitening/smoothing or generated-minus-source correction is used. Four already cached, hash-verified source parser maps were reused; no new parser/model inference, dataset, training or GPU generation occurred in this extension.

The new module adds style-specific eye spread/lower-eye bands, localized cheek highlights, lip gloss/matte fields and golden eyelid pigment. All are restricted to source skin/lip cosmetic support; parser-protected eyes, brows, inner mouth/teeth, nose, neck and nonfacial areas remain untouched.

Dewy highlights are capped and local. Lip finish fields operate from source luminance/highlight variation; they do not blur or regenerate the face. Source texture/lighting, blemishes, existing makeup and flash remain. This is a limited2Dtry-on, not a claim of physical cosmetic simulation.

Profile colors, strengths, supported descriptions and missing features were frozen before outputs. The only preparation correction completed diagnostic overlays to show the additional active lower-eye/highlight fields; the initial base-fields-only overlays are retained. No new style/strength sweep was performed.

## Validation and actual review

Command:
python -m pytest backend/tests/test_makeup_source_styles.py backend/tests/test_makeup_source_render.py -q

**51 passed =27new extension tests +24baseline tests.** These cover all seven profiles, deterministic source protection, localized finish-only edits, zero-effect behavior, invalid strengths/regions, truthful non-LoRA flags, source/map/baseline tampering and evidence preservation.

All28saved PNGs were independently regenerated and matched exactly. Every original, cached label and output hash was checked. There were zero changed pixels outside allowed cosmetic support, zero changed protected pixels, and no changes to the diagnostic forehead patch. The12prior previews were re-rendered pixel-identically before and after the extension.

Codex visually inspected all four complete region sheets and all four original-plus-seven result sheets, plus native-size eye/lip detail sheets for054109and006553. Source preservation is promising. Visible style separation varies: No-Makeup is minimal; Smoky/Dewy/Matte can be subtle; Rosy/Evening are more obvious; gold reads as localized warm pigment rather than validated metallic makeup. Lip boundary/intensity realism remains a human review issue.

No quantitative skin-quality score, calibrated mask-ground-truth accuracy, all-face/lighting generalization or human ACCEPT is claimed. Four reused development portraits are not an untouched test population.

CPU render-only times were about0.22–0.35seconds, excluding parser/network/queue/file I/O. This does not establish online latency or deployed memory requirements.

## Deployment status and next step

No frontend, API, style catalog, live model, contract, Kaggle bundle or Render configuration changed. The current website continues its existing implementation. The review ZIP is not an upgrade package.

Review the actual looks and decide which profiles and descriptions are acceptable. Then validate automatic regions on more suitable original/client photos, version the accepted renderer/profile contract and truthful catalog, test standalone/consultation/guest/save/book/stylist flows, and package matching Kaggle/Render updates with rollback. Preserve old saved-image snapshots and the original trained-model evidence.

Unsupported full-face finish/lash claims must be resolved explicitly before release. Do not silently route remaining looks to the old whitening model or claim all10styles are deployment-ready.

# Makeup alignment gate and one Soft Glam revision — 30 October 2026

**Progress DONE; technical VERIFIED; appearance EXPERIMENTAL / Codex rejects release.** User approves the bounded alignment check and single-style revision, with method reassessment if still artificial. No all-style or cloud deployment performed.

## What ran

Downloaded Google's published 3,758,596-byte Face Landmarker task, pinned observed SHA256 64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff. Existing MediaPipe0.10.33 runs four source portraits locally on CPU; no new Python package install, training, image generator or photo upload. Each has one detected face and478normalized points. Observed detection calls9–31ms exclude Python startup/model load and are not end-to-end generation timings. Model download receipt is retained.

Source images/maps/previous outputs and helper code are hash pinned in MAKEUP-ALIGN-001. Native eye crops and full overlays compare parser upper curves with landmark eye outlines and include brow/lip points. Eight eye mean absolute disagreements span0.69–2.78px. This is disagreement, not error against manually labeled ground truth. Codex checks all4full overlays and2native crops; acceptable for this four-case experiment only. Semantic brow shape remains because landmark brow coordinates are not a verified hair boundary. Detection thresholds0.6 are initial uncalibrated settings.

## What changed in the isolated renderer

New scripts/makeup_alignment_pilot.py performs detection/geometry/provenance checks. scripts/makeup_aligned_soft_glam.py consumes reviewed cached points, uses landmark eye contours, finer nonuniform tapered lash clusters, lip-outline restriction and explicit eye-interior protection. Warm palette and pigment strengths are EXACT previous MAKEUP-COMPLETE-001 profile; no strength sweep. Frozen recipe precedes rendering.

Four full Soft Glam comparisons saved. Nose, mouth interior and nonface remain exact source. Brows/lips remain editable within source shape. Important protection difference: a narrow semantic eye rim outside BOTH landmark eye polygons and eroded semantic eye core may receive cosmetics. Changed semantic eye-rim pixels:43,28,0,71. Protected eye interiors/semantic cores remain exact. Do not claim that every prior label4/5 pixel is unchanged.

## Checks and appearance

20new tests +86existing rendering regression tests = **106pass**. One initial test failed only because its message regex expected 'differs' while the correct rejection said 'differ'; test corrected, no renderer change. All4saved PNGs independently reproduce, palettes match, source/model/maps/helper/previous/landmark/output hashes match. Zero outside-support, protected, or protected-eye-interior changes.

Codex inspects all4comparisons: roots align better and regular comb band is reduced, but procedural lash fibers still look drawn-on/spiky. Cheek/lid/skin material finish does not recreate the reference's complete look. **Not accepted for release; zero human appearance acceptances.** Safety and placement do not prove realistic makeup.

## Evidence and next decision

Private evidence under artifacts/makeup-render-20261030/alignment-01 and aligned-soft-glam-01. Review archive beautycore-makeup-alignment-review.zip:37members, CRC verified,6,264,489bytes; SHA256 6b148a4020448d743a732ac8735f4b81c048788371369901f747744f51c4d0fd. Originals/previous outputs/source credits included; reference/model weights excluded.

The agreed fallback is reached: stop opacity/lash-stroke sweeps and reassess the method. A read-only source audit of a dedicated reference-conditioned candidate is saved in [reassessment](../research/makeup-method-reassessment-20261030.md). No replacement model has been adopted or shown to solve skin tone. No training/GPU generation, service/API/model contract/catalog/dependency changes, Render/Kaggle action, or automatic fallback to previously rejected generation.

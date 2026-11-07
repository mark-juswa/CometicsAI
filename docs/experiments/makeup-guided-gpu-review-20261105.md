# MAKEUP-GUIDED-001 returned GPU review

5 November 2026. **Technical execution VERIFIED. Both visual cases REJECTED by engineering. Production integration NOT STARTED.**

## Conclusion

Separate original and cosmetic guide conditioning did not correct Makeup realism. Both actual MAKEUP-001 outputs contain visible full makeup but replace natural skin with a stylized smooth surface and substantially alter facial features. The deeper complexion is severely lightened. The fair portrait also loses texture and has reconstructed brows, eye makeup/eye appearance, nose shading and teeth. Neither resembles the approved photographic complete look closely enough for promotion.

Stop this approach at its bounded gate. Do not spend a further all13style GPU run, recolor these faces globally, composite the earlier rejected material pipeline over them, admit these outputs as targets, or integrate this path into serving. This is an appearance failure with a successful runtime, not a failed model download, missing adapter or swapped guide.

## Independently checked evidence

Received `D:/Downloads/beautycore-makeup-reference-results.zip`,3,974,056bytes, SHA256 `2677b2539d938a713221a0ab0555a078da6dbad2326494c9c61aff81c0f4d112`. Preserved unchanged with extracted data at `artifacts/makeup-complexion-release-20261105/gpu-return-01/`. No attached code was executed.

All23members have unique safe paths; ZIP CRC passed. Returned plan bytes and six source file inventory hashes match the prepared notebook. Six fixture hashes match, including original portraits and different training identity guides. Environment matches the original exact reviewed host/packages/Diffusers commit. Base revision/index and adapter identity match. Returned assertions report200matchingadaptertensors/100activelayers at full1.0influence; this corroborates the trusted harness, not independent live access to its GPU. Raw PNG and decoded RGB hashes match. Every saved comparison panel reproduces its corresponding actual fixture/output exactly. Effective prompts, image order,20steps,guidance4 and seed1977 match. One foundation load, two model generations, no postprocessing, no training or deployment.

| Case | Actual model time | Peak allocated GPU memory | Visual verdict |
|---|---|---|---|
|054109, Soft Glam,006553guide |85.894seconds |8303.43MiB | REJECTED: major whitening, plastic texture, reshaped/darkened brows, reconstructed eye/nose/mouth detail, replaced brighter teeth, excessive red eye/cheek makeup versus soft neutral guide |
|056266, Bold Evening,035149guide |84.586seconds |8304.56MiB | REJECTED: plastic foundation/skin, exaggerated hard contour/highlight and cheek patches, reconstructed brows/eyes/teeth; visible bold lips and eye makeup do not compensate for loss of photographic realism |

The times are two observations, not a benchmark. Startup including model/adapter load59.389seconds, separate from setup/download.

## Visual comparisons

Each saved board is `Original | Different-person cosmetic guide | Previously rejected CPU result | Actual MAKEUP-001 raw`.

- [Soft Glam comparison](../../artifacts/makeup-complexion-release-20261105/gpu-return-01/results/054109-soft_glam-comparison.png)
- [Bold Evening comparison](../../artifacts/makeup-complexion-release-20261105/gpu-return-01/results/056266-bold_evening_glam-comparison.png)

Both boards and both native512rawoutputs were inspected. These are clear failures against the required complexion, texture, identity and natural blending criteria. Engineering rejection does not claim an additional Supervisor review. The third panel is explicitly a CPU compositor, not a matched old model baseline. No causal Base versus adapter conclusion can be drawn from that panel.

## Root cause update and next boundary

The full output reconstruction behavior persists despite an improved cosmetic guide and explicit source identity/complexion instructions. Missing cosmetic image conditioning is therefore insufficient as an explanation or correction under this fixed configuration. This test cannot isolate the historical adapter's contribution from Base behavior, prompt interactions or conditioning behavior; earlier Base failures also remain relevant. It does not establish that every possible setting or future adapter must fail.

The evidence supports returning to reviewed complete photographic target preparation and a separately trained/evaluated corrective adapter on the existing FLUX/LoRA foundation. Training must use admitted targets with truthful synthetic provenance and identity separated splits. The approved external teacher direction is useful for that target standard but is not proof that the current model learned it, and training on the rejected historical pairs would not be a correction. Any new target set still needs full catalog/style and complexion review before finalization. No new training is authorized by silently reusing old FINALIZED labels.

Zero new accepted training pairs; DATA corrective finalization remains BLOCKED by target admission. Corrective training, its Base comparison and actual application validation are NOT STARTED. A reliable complete Makeup deployment today is not established by the available evidence. The existing18Hair/8Nails prepared release remains intact with its separate matching deployment and rehearsal requirements. Do not silently substitute a third party live editor, remove Makeup styles or call the external teacher our MAKEUP-001.

## Preservation

Only returned evidence inspection and project records changed. No new model invocation, GPU rerun, dependency/model download, training, serving/UI/API/adapter change, Git publication or cloud deployment. The approved teacher proof, prior failures, source datasets and all existing checkpoints remain intact. Source and technical review receipts are under `gpu-return-01/independent-review.json` and `gpu-return-01/visual-review.json`.

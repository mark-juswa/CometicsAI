# DATA-001 three-image pilot review

**Status: PILOT STOP.** Codex inspected the Supervisor-supplied pilot ZIP on 2026-09-23. These are visual findings for the Project Lead/Supervisor; they are not an official ACCEPT review manifest or authorization for full generation. The accepted-counterpart count remains zero.

## Artifact integrity and provenance

- Supplied archive: `D:/Downloads/data001_pilot.zip`; SHA256 `ef71eb19b52c2d0cf1ad21c8d5f30a36a118bf9319192dc78485e1ccc04d4485`.
- Local extracted copy (ignored by Git): `data/dataset_v1/pilot_review/`; review sheet: `data/dataset_v1/pilot_review/generation_review_sheet.jpg`.
- The ZIP contains all three planned original PNGs, generated PNGs, JSON sidecars, the pilot plan, and environment report. All three original and generated files decode as RGB 512×512. Source and generated SHA256 hashes match each sidecar. Sidecar sample IDs, classes, split, prompts, and seeds match the [committed pilot plan](DATA-001-pilot-plan.json).
- Dataset: `yikaiwang/FaceSketches-HairStyle40` at `45de974926fe64551fc2d0b80973335e20ca10e2`. Model: `black-forest-labs/FLUX.2-klein-base-4B` at `a3b4f4849157f664bdbc776fd7453c2783562f4d`.
- All three jobs used GPU 0 (Tesla T4), FP16 with CPU offload, 512×512, 20 steps, guidance 4.0, seed 1977, attempt 1. Exact sidecars are preserved in [`pilot/`](pilot/); generated pixels remain outside Git.

| Sample ID | Requested style | Runtime | Peak allocated GPU memory | Codex visual assessment |
| --- | --- | ---: | ---: | --- |
| `CrewCut_1` | `BobHair` | 62.074 s | 8,705,465,856 bytes | Candidate suitable for acceptance: chin/neck-length bob is visible; face, smile, pose, clothing, and background remain recognizable and largely stable. Minor facial retouching warrants Supervisor review. |
| `BobHair_1` | `LayeredHair` | 63.915 s | 8,707,695,104 bytes | Not suitable as a hairstyle-only pair: the blonde hair becomes dark brown. Face, pose, outfit, and background remain broadly stable, and the new layered shape is visible, but hair color becomes a confounded training change. |
| `LayeredHair_4` | `CrewCut` | 63.205 s | 8,707,695,104 bytes | Not suitable as an identity-preserving pair: the crew cut is present, but facial details change visibly; the result also adds a necklace and alters the clothing/neckline. The face is more stylized than the original. |

## Pilot gate result

Codex's provisional assessment is **one candidate suitable, two unsuitable**. Under the approved pilot rule, **0–1 of 3 acceptable outputs means stop and reconsider the generation methodology**. A one-seed retry is reserved for a 2-of-3 result; this evidence does not justify launching retries or the remaining 27. No official `ACCEPT`, `REGENERATE`, or `REJECT` review manifest has been written; the Supervisor/Project Lead retains that decision.

The observed errors are specific: hair color drift in `BobHair_1`, and identity/accessory/clothing drift in `LayeredHair_4`. A method review should determine how to constrain these changes before any more generation. This record does not change the source selection, split, transformation cycle, model, or training architecture.

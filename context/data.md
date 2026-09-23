# Data

Source: Supervisor's CODEX HANDOFF 001 and approved DATA-001. Dataset V1 strategy: CONFIRMED; source inspection and selection: VERIFIED; three-image pilot generation: VERIFIED EXECUTION; pilot method: STOPPED after visual review.

Intended paired-edit example: a source portrait of one person with an original or synthetic alternate hairstyle, a target portrait of that same person with the desired style, and an editing instruction that asks for the target hairstyle while preserving identity, pose, clothing, background, and lighting.

The earlier six-category, 72-pair preliminary plan is superseded for V1 by the Supervisor's three exact classes: `CrewCut`, `BobHair`, `LayeredHair`. The [DATA-001 record](../docs/data/DATA-001.md) pins `yikaiwang/FaceSketches-HairStyle40` at `45de974926fe64551fc2d0b80973335e20ca10e2`: its card declares Apache-2.0, its original photo folders each contain 30 decodable images, and a hand-reviewed provisional selection has ten per class (eight train and two validation identity groups). The source card names Hairstyle30k as upstream; it does not document individual photograph rights. The three TRAIN pilot generations completed in Kaggle; the [pilot visual review](../docs/data/DATA-001-pilot-review.md) found one potentially suitable output and two with material drift. Official review decisions remain with the Supervisor/Project Lead. No generated counterpart has been accepted, so 48 train + 12 validation directional pairs remain a target, not an existing dataset.

CONFIRMED V1 construction: `CrewCut → BobHair → LayeredHair → CrewCut`; one pretrained Base alternate per selected original, at most one regeneration per failed output, explicit visual acceptance, then both edit directions kept within the original identity group's split. Identity and non-hair preservation, generated quality, and any training benefit remain NEEDS VERIFICATION. No directional pairs are claimed to exist.

When data work is authorized, record source URLs, license evidence, transformations, pairing provenance, exclusions, class mapping, and exact split manifest. Keep detailed dataset evidence outside this summary.

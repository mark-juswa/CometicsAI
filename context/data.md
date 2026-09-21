# Data

Source: Supervisor's CODEX HANDOFF 001. Dataset strategy decision: PROPOSED; actual dataset evidence: UNKNOWN.

Intended paired-edit example: a source portrait of one person with an original or synthetic alternate hairstyle, a target portrait of that same person with the desired style, and an editing instruction that asks for the target hairstyle while preserving identity, pose, clothing, background, and lighting.

Preliminary planning numbers are approximately six hairstyle categories, 60 training pairs, and 12 held-out validation pairs, 72 total. These are PROPOSED targets, not inspected counts or a created split. Candidate FaceSketches-HairStyle40 or Hairstyle30k-derived sources are unselected. Source, licensing, allowed uses, class names, usable images, quality, provenance, consent/privacy implications, and split leakage are NEEDS VERIFICATION before preparation.

PROPOSED synthetic-pair method: start from a real target-style photograph, use a pretrained editor to make a different/neutral hairstyle source, then pair that synthetic source with the original target. Whether identity and non-hair regions remain suitable, whether generation is feasible at $0, and whether the training signal helps are NEEDS VERIFICATION. No pairs are claimed to exist.

When data work is authorized, record source URLs, license evidence, transformations, pairing provenance, exclusions, class mapping, and exact split manifest. Keep detailed dataset evidence outside this summary.

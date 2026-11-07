# Expanded styles: first implementation milestone

Date: 30 October 2026  
Status: **DONE locally; overall release IN PROGRESS**  
Deployment: **NOT STARTED**  
Appearance approval: **PENDING**

## Implemented

- Strict, versioned manifest for all 13 target candidates. All are disabled.
- Explicit installed-profile and canonical renderer-source checks. Unsupported Hair/Makeup profiles cannot be enabled by changing a flag.
- Three source-preserving Nails algorithms integrated into the existing renderer/refinement/compositor path: Raspberry Jelly, Pink Aura Ombré, Negative-Space Micro-Dots.
- Active discovery and direct generation use the same approval gate. Consultation reads the active feature catalog; tags exist for pending Nails but do not enable them.
- New renderer results identify their renderer profile/release and do not claim a trained adapter.
- Protected facade readiness includes bounded style capabilities. Render validates the known release/digest, original three-style or expanded thirteen-style Hair baseline, model catalogs and renderer IDs.
- True legacy readiness remains compatible. Malformed, inconsistent or wrong optional worker capability reports fail closed. Signed registration fields, heartbeat and lease behavior are unchanged.
- Deterministic generator/checker for matching Render evidence and business additions. Accepted metadata remains after generation is disabled so saved looks/bookings can still resolve it.
- Local original-size gallery of the existing four-hand/three-design results. No new image generation was needed.

## Validation

| Check | Result |
|---|---|
| Initial focused backend | 79 passed |
| Full backend suite | 773 passed |
| Final readiness/release edge-case follow-up | 64 passed |
| Render compatibility and registration | 32 passed |
| Business workflows, pricing, save/book, completion | 47 passed |
| Guest trial | 29 passed |
| TypeScript | Passed |
| Production Next.js build | Passed |
| Catalog and generated-release checks | Passed |
| Original four hands, three styles each | All 12 decoded RGB outputs reproduced exactly |

The final focused follow-up checks malformed/inconsistent optional worker evidence added after the full-suite run. No existing runtime feature was weakened to make tests pass. The existing python-multipart deprecation and Node module-mocking warnings remain.

SHA256 comparisons confirm the Makeup contract, both Hair registries, GPU worker source, optimization source, original client/optimized notebooks and current business style metadata are unchanged.

## Limits and next steps

This is installed code behind an approval gate, not a deployed expansion. The production-visible catalogs remain unchanged. Supervisor says they need to review the images first; this is not acceptance.

1. Review the three designs. Record per-style acceptance; keep rejected/pending entries disabled.
2. For accepted designs, update the manifest deliberately, regenerate matching Render metadata, rerun relevant checks and preserve the release record.
3. Prepare the matching Kaggle release artifacts/notebook. Current private archives do not acquire these local source changes automatically.
4. Rehearse direct generation, consultation, saving, booking, original model paths and rollback before switching the live runtime.
5. Continue other Nails finishes and Hair validation as separate gated work. Original Makeup white-cast correction remains unresolved; no replacement model was adopted.

No Render deploy, push, database migration, Kaggle start, new GPU run or speed benchmark was performed.

Sources: [plan](../specs/0015-expanded-styles-release.md), [machine receipt](expanded-style-milestone1-20261030.json). Local review gallery: artifacts/expanded-nails-release-review-20261030/index.html.

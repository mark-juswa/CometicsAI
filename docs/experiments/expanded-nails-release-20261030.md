# Approved Nails release preparation

Date: 30 October 2026  
Status: **DONE locally; release IN PROGRESS; not deployed**

The Supervisor approves the repaired gallery. Raspberry Jelly, Pink Aura Ombré and Negative-Space Micro-Dots are the only three enabled additions. Current local metadata has 13 Hair, 10 Makeup and 8 Nails. Other expansion candidates remain held/untested, and the original Makeup white-cast issue is unresolved.

The generated Render release and accepted business catalog match the versioned backend manifest. New looks use the existing descriptions, salon service prices and persistent save/book/image authorization. No database migration or architecture replacement is needed.

A separate immutable CPU package, render_kaggle_cpu_styles_20261030_01.bin, and render_kaggle_expanded_nails_demo.ipynb are built. They retain the original GPU archive, Nails-only optimization, automatic registration and fallback notebooks. Exact artifact/source hashes are recorded in the package inventory.

## Verified

- Full backend: **777 passed, 0 failed, 0 skipped**.
- Render registration/release: **32 passed**.
- Business workflows: **50 passed**, including each new design's saved snapshot, catalog-priced booking and shared client/assigned-stylist private image.
- Guest trial: **29 passed**.
- TypeScript, production Next.js build, generated-release/catalog checks and scoped whitespace check passed.
- All twelve historical automatic-mask Nail results reproduce exactly.
- Real CPU extraction, CRC/member/source hashes, tamper rejection, notebook/GPU pairing, immutable rebuild and fallback preservation passed.

The initial pair test exposed implicit Windows text decoding; the new notebook now reads UTF-8 explicitly. The failed pre-publication notebook/receipt remain preserved. Older catalog assertions were updated to expect the approved eight styles. Final complete checks passed.

These are local tests, including supplied geometry/mask fixtures and a disposable database. No new GPU inference, live browser generation, Render deployment, source push or production database write ran. The new notebook must still be rehearsed with matching Render code.

## Next

Follow [the release guide](../guides/expanded-nails-release-20261030.md): publish/deploy matching Render source, switch Kaggle during a planned gap, rehearse all features plus consultation/save/book and retain the old optimized starter for rollback. Connected status alone is not acceptance.

[Approval](expanded-nails-approval-20261030.json), [package inventory](expanded-nails-package-20261030.json), [validation receipt](expanded-nails-release-20261030.json).

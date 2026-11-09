# Camera visibility diagnosis — 10 November 2026

Evidence status: VERIFIED for source/deployment mismatch; no release action performed.

The user reports the Hair Studio upload area has no camera choice. Repository inspection finds CameraCapture in the Hair page on commit 78fac069484e879d1345e23db2461f2eb3c5d056, pushed to codex/ai-methodology-camera. Fetched origin/main is ba077964e87b7f6b5b481ecc55d4dc6f7083a408 and does not include that feature.

The signed-in Render dashboard deployment detail for service srv-db4ftmbbc2fs73blpkr0, deployment dep-dboummu1egvs7384lrl0, visibly reports Deploy succeeded / Live and source ba07796. This establishes a release mismatch, not a camera permission failure. The implementation supplies a separate Use camera button; it does not add an entry to the desktop operating system's file chooser.

Next release step is merging the tested camera/methodology branch into main and manually deploying that source on Render (Auto Deploy is off). No merge, cloud configuration change, GPU request or deployment was performed in this diagnosis. Real camera permission and device acceptance remain unverified as recorded in the implementation evidence.

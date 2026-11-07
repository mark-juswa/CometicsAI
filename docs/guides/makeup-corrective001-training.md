# Run the approved corrective Makeup training

6 November 2026. DATA is finalized and all 78 pairs are accepted. Target review is complete. The next step is real corrective adapter training and evaluation.

Use these two files:

1. [Training input ZIP](../../artifacts/makeup001_corrective001_training_20261105.zip), 198,859,794 bytes. SHA256: `12ab2d039e5fd3d7f8f0bdcb891fa0efe1865e1ecd6407bff6b16f7b60ab6312`.
2. [Importable Kaggle notebook](../../artifacts/makeup-corrective-supervision-20261105/kaggle-training-handoff-20261106/ready/makeup_corrective001_train.ipynb).

In your signed-in Kaggle session:

1. Upload the training ZIP as a **private Kaggle Dataset**.
2. Import the notebook into a separate training notebook/session and attach that Dataset. Keep the current serving notebook and existing release files intact.
3. Select **Tesla T4**, turn **Internet on**, and run the notebook cells in order, or use Run All. If your existing model access uses a Kaggle secret named HF_TOKEN, the setup cell can read it without printing it.
4. Download **makeup001_corrective001_results.zip** from Kaggle Output and return it here.

The first cell verifies the frozen input and copies it to writable storage. This avoids the historical read-only training-cache failure. The second installs the same pinned AI Toolkit requirements while preserving host Torch. The third trains a fresh, separately named 250 step adapter from the existing pinned Base and generates 26 Base plus 26 new adapter outputs across all 13 styles. It does not continue the rejected adapter, start a service, change Hair/Nails, or deploy a model.

The old successful 250 step training run took 8,623 seconds including model load. That is historical timing, not a promise for this run. The 52 real evaluation calls take additional time.

The result ZIP contains training and environment logs, final and intermediate checkpoints, optimizer state, and completed evaluation images and comparison sheets. A failure preserves and packages partial evidence. If you manually interrupt execution before packaging finishes, the final recovery cell packages existing files without repeating training or generation.

We will review the real new model outputs for complexion, identity, texture, complete makeup and style fidelity. If they pass, the next milestone is the compatible runtime model package and real application validation, followed by production review. Target acceptance and successful training do not by themselves establish deployment readiness.

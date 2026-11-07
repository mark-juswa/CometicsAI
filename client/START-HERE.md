# BeautyCore client serving package, 6 November 2026

Repository handoff update, 7 November: [source access, local development, push permissions and Render deployment](../docs/guides/client-repository-handoff.md). In a Git clone the two `.bin` files listed below are absent by design; obtain them privately from the project owner. The retained local serving ZIP includes both. Importing this notebook does not pin Kaggle's Docker image. The reviewed environment is Python 3.12.13, Torch 2.10.0+cu128, CUDA 12.8 and Tesla T4. Current startup is not yet verified after the reported host and input discovery errors.

This package supports 18 Hair, 13 Makeup and 8 Nails styles (39 total).

Contents:
1. render_kaggle_makeup_corrective_demo.ipynb, final serving notebook.
2. beautycore_makeup_release_20261106.bin, matching application/worker release, corrected Makeup adapter, exact13stylecaptions and CPU Nails assets.
3. capstone_train002_20260928_v1.bin, original shared GPU foundation runtime and original Hair TRAIN-001/TRAIN-002, Nails adapter and preserved older Makeup adapter. The final notebook deliberately selects the new corrective Makeup from input2.
4. manifest.json, exact file sizes and hashes.

Use both .bin files as Kaggle inputs, keeping their filenames unchanged. Do not upload this whole handoff ZIP as an input and assume the notebook can find its enclosed files. Extract it first, then attach datasets containing each .bin. Keep the CPU/model inputs private.

Use a separate private copy of the project's tested pinned Kaggle notebook, then import the final serving .ipynb. The known source notebook is https://www.kaggle.com/code/cosmetics100/render-kaggle-demo-pinned . Preserve originals. Do not create a fresh latest-image notebook and bypass the environment guards. The notebook checks Python/Torch/CUDA/GPU before starting models.

Enable T4 and Internet. Configure the existing three Kaggle Secrets: AI_BACKEND_API_KEY, AI_REMOTE_API_KEY, GEMINI_API_KEY. AI_BACKEND_API_KEY must match the existing Render deployment. Arrange access securely with the project owner. No secret values are included in this package or should be pasted into notebook cells. Keep the serving notebook private.

Run the three code cells in order once. The startup installs its reviewed dependencies and downloads the shared pinned FLUX Base model. The full Base weights are not inside this ZIP, so this is not an offline installer. All project-trained feature adapters and required bundled CPU assets are included. No raw training dataset or retraining is needed.

Wait for CONNECTED TO WEBSITE and the matching styles-20261106-01 release, then leave the Kaggle session running. If an older serving session owns the website lease, stop that old session only when ready to switch and allow normal lease expiry, up to180seconds. Do not force database/endpoint edits or repeat uncertain generation requests.

Render web deployment578330d is already Live. All13Makeup outputs passed real application validation and exactly match the reviewed real model PNGs. Both Hair adapters and one Nails crop also passed. The final production-serving connection has not yet been observed, because the user chose to run it manually. Before handing over as fully ready, verify CONNECTED TO WEBSITE and test Hair, Makeup on a fresh portrait, and Nails on a clear full hand photo through the actual site. Consultation/save/book and mobile acceptance stay explicit.

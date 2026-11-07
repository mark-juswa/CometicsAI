# Serving runtime mismatch, 6 November 2026

Status: IN PROGRESS. Diagnosis VERIFIED. Kaggle recovery NEEDS VERIFICATION.

The Supervisor supplied a screenshot from BeautyCore V2 and a pasted traceback. The serving notebook stops in `prepare` at `check_host`, before model loading, service startup or registration. The reviewed archive requires Python 3.12.13, Torch 2.10.0+cu128, CUDA 12.8 and Tesla T4. The reported host is Python 3.13.16, Torch 2.11.0+cu130, CUDA 13.0 and Tesla T4. The GPU name matches. This error does not establish a model, checkpoint, target quality or dataset failure.

Local reproduction executed the actual final serving notebook's host check against the reviewed environment read from the unchanged GPU archive. Matching values pass. The reported values produce the exact supplied error. [Machine receipt](makeup-serving-runtime-mismatch-20261106.json).

The final serving notebook metadata contains only `kernelspec`, with no Kaggle Docker image pin. The complete client ZIP therefore carries code and model inputs, but does not establish a reproducible Kaggle host. DOCUMENTATION DRIFT: copying or importing the supplied notebook must not be described as proof that the reviewed host is retained. The bootstrap also checks the host later; bypassing the first guard would not establish compatibility.

The bounded recovery is to return to the original successful application notebook at https://www.kaggle.com/code/cosmetics100/render-kaggle-demo-pinned and inspect its environment setting. If the original environment remains selectable, retain that environment when importing the final serving code, keep the two verified inputs and existing secrets, then start a fresh T4 session. Confirm actual versions at Cell 1 before continuing. Preserve the original code and outputs first. Selecting original on a newly created notebook may retain that new notebook's incompatible environment. Copy inheritance and current availability of the old image have not been verified. If the original notebook no longer offers the reviewed image, capture the environment options before choosing an alternative runtime.

No notebook browser operation, cloud change, package downgrade, guard removal, GPU generation, retraining, model alteration or dataset change was performed during this diagnosis. The Supervisor retains manual browser control. Previous accepted model and application results remain valid. The current serving connection remains unverified.

## Subsequent input discovery error

The next supplied traceback stops earlier, at the exact count check for `capstone_train002_20260928_v1.bin`. This establishes zero or multiple filename matches, not which count. The screenshot lists both BeautyCore GPU Models 20261106 and capstone_train002_20260928_v1, plus seven other input attachments. Duplicate matching files are plausible but unproven until filenames are expanded or enumerated. The final serving notebook's actual BUNDLES assignment still requires exactly one original GPU file and one `beautycore_makeup_release_20261106.bin` file, with the preserved hashes. Recommend retaining only the two new serving input attachments on this notebook and checking their exact contained filenames. Detach obsolete inputs from this notebook only, without deleting datasets. This earlier failure provides no new evidence that the host version mismatch has been resolved.

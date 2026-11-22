# Kaggle validation failure, 22 November 2026

Progress: DONE local diagnosis and correction, live Kaggle revalidation NEEDS VERIFICATION. VERIFIED asynchronous gateway protocol defect reproduces the reported failure. The stopped session's original HTTP response is not retained.

Supervisor reports that Kaggle completed startup through GPU/bootstrap/readiness, advertised18Hair/13Makeup/8Nails and printed `KAGGLE_BACKUP_READY_FOR_VALIDATION`, explicitly without website connection. The third cell then raised `Local subject rejection failed for hairstyle; no retry was made` from `backup_validate`.

VERIFIED source: `scripts/kaggle_backup_controls.py` and the public notebook's third code cell submit a512pixel blank PNG to each feature and require HTTP422 with that feature's exact public subject error. The generic exception is raised for either another status or another detail. It does not establish whether the observed response was authentication failure, detector unavailability, unrelated validation, or another condition. The website registration function is separate and requires successful negative checks,16real application cases and explicit visual acceptance. The printed tunnel URL alone is not registration evidence.

The provided input screenshot shows the two expected archive filenames, but does not establish their hashes or the validation response. No archive, model or Render URL change is justified by this traceback alone.

Initial access reached public Version3 while signed out. After the Supervisor completed authentication, the editor confirmed cosmetics100 is signed in, retained the matching startup/error output, and displayed `Draft Session off (run a cell to start)`. Supervisor confirms the session is off. The output browser has no accessible runtime files. No notebook restart, cloud cell execution, GPU request, key disclosure or server registration was performed.

## Reproduction and correction

Ranked checks were an asynchronous202 admission mistaken for the final rejection, an authorization rejection, and a photo detector503. The first is a concrete source mismatch: `app.demo_gateway.create_gateway` always returns202 with a job ID for an admitted manual generation request, even when the inner photo guard immediately returns422. The original `backup_validate` checks this admission body as though it were the final image validation result.

VERIFIED `test_subject_validation_resolves_the_actual_hosted_gateway_ticket` uses the real gateway with an inner fixture that correctly rejects all three subjects. Before the fix it raises the exact `Local subject rejection failed for hairstyle; no retry was made`. After the fix it reaches `SUBJECT_REJECTION_PASS`, with exactly three POSTs and three final result GETs. There are no model/remote calls in this test. [Before](../../artifacts/kaggle-validation-20261122/reproduction-before-fix.log), [after](../../artifacts/kaggle-validation-20261122/reproduction-after-fix.log).

The correction submits once, validates the returned UUID, then polls only GET status/result for that same owner-bound job, bounded to60seconds after admission. The final status must still be422 with the exact feature message. Detector503, invalid ticket, pending timeout and unrelated errors remain failures, without another submission or registration. Mismatches now include the HTTP status while omitting arbitrary response detail.

VERIFIED32 focused tests pass. Three unchanged gateway handler tests that expect blank pictures to produce successful previews fail on the newly inherited photo guards/native asset dependencies; these are recorded in `final-tests.log`, not silently claimed green. The focused run excludes only those three. Main, gateway, detector and those old tests match origin/main byte for byte. Windows sandbox blocks asyncio's internal socket pair; local gateway checks were run outside the sandbox, with no cloud traffic. [Focused log](../../artifacts/kaggle-validation-20261122/focused-tests.log).

## Delivered files and bounds

- Corrected companion notebook: `client/beautycore_kaggle_backup_20261122.ipynb`.
- Replacement third cell: `artifacts/kaggle-validation-20261122/Cell-3-validation-fixed.py`.
- Original13November notebook preserved byte for byte, SHA256 `03134219d9de447f95b5c501459fe2890751d6398c04a9bd546abaaa4206413b`. Only the third code cell differs in the companion notebook; all other cells, guards and final false visual-acceptance flag match. Tests compile every code cell and compare the controls to the maintained source. [Hashes](../../artifacts/kaggle-validation-20261122/notebook-verification.json).

This fixes a reproducible validator bug. It does not prove the stopped Kaggle detector's actual response or a working fresh session. After restarting the retained reviewed environment, the corrected subject check and existing real-output/visual gates must pass before explicitly connecting to Render. No need to replace either model archive or change Render's URL to address this protocol bug.

Separately, the earlier approved Render UI deployment remains pending. Feature implementation commit7396ca3 exists locally. Integration of origin/main1d9d562 had only documentation conflicts; both dated additions are retained. No push or manual deploy is established by that pending integration.

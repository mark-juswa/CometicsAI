# Local photo check release preparation

This candidate changes the CPU API and the website error relay. It requires both releases. The current public Runpod image and Kaggle backup are unchanged. Keep the old deployment and private archives available for rollback.

From the repository root, prepare the pinned public face asset and a fresh package:

```powershell
python scripts/prepare_photo_detector.py
python scripts/package_runpod.py --profile a40 --inputs I:/HAIR/client --output artifacts/photo-check-release
docker build -t beautycore-runpod:photo-check-release artifacts/photo-check-release/build-context
```

Use the actual private input directory on the operator machine. Choose a new output directory if that path already exists. The packager verifies both original private archive hashes and inventories the CPU updates and detector asset. Do not upload private inputs or model files to the public source/image repository. Building the image does not load a GPU or change the live service.

The already built and locally checked candidate for 13 November is `beautycore-runpod:photo-guard-a40-20261113-03`. It has not been published. After authorized image publication, record its immutable digest and configure exactly the reviewed A40 profile, retaining existing secrets, disks and notebook startup. No credentials should be included in logs or screenshots.

Before website cutover, stage/start the new serving image with BEAUTYCORE_PUBLIC_URL unset. Test one usable portrait for Makeup and Hair, one usable full hand for Nails, and wrong subject images through the actual API. Verify a missing detector gives a service unavailable message rather than a wrong photo accusation. Verify office/natural preferences, strong Makeup preferences, exclusions and fewer than three compatible styles. Make one real accepted generation per affected path when GPU budget is authorized. Do not claim previous image outputs establish these new checks.

Release the matching website error relay, then restart the runtime with the existing Render URL and verify CONNECTED_TO_WEBSITE plus a fresh ordinary client workflow. The current command remains `python /opt/server/runtime.py start`. Avoid starting a second owner of the same workspace. Keep the original model release/catalog, and do not rerun training for this change.

Kaggle remains an older backup. Its notebook/archive packaging does not automatically pick up these Runpod CPU updates. Report that difference until a separately validated backup update exists.

See [implementation and evidence](../experiments/consultation-photo-guards-20261113.md) and [design](../specs/0022-consultation-relevance-photo-suitability.md).

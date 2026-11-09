# BeautyCore source and deployment handoff

Date: 7 November 2026. Deployment guidance updated 9 November 2026 from the actual Render dashboard.

Runpod update, 8 November: the [Runpod server guide](runpod-serving.md) now provides a built and publicly published image with verified anonymous pull access, Linux staging, CPU model loads and notebook authentication. You can skip Docker build steps. Private inputs and secrets are supplied separately. Kaggle remains backup. Actual Runpod GPU validation and provider cutover remain open. [Build receipt](../experiments/runpod-docker-build-20261108.md).

## Get the complete source

Repository: https://github.com/mark-juswa/CometicsAI

Use `main` for the complete source handoff and the current Render deployment. `codex/render-kaggle-demo` is the historical serving branch. The publication receipts record exact published commits. Older experiment results are preserved as evidence, including failed approaches. Their presence does not select them for production.

```powershell
git clone https://github.com/mark-juswa/CometicsAI.git
cd CometicsAI
git switch main
```

| Folder | Responsibility |
| --- | --- |
| `beautycore/` | Current Next.js Client, Stylist and Admin website, authenticated AI bridge, database schema and migrations |
| `backend/` | FastAPI, Consultation, Hair, Makeup, Nails and automated tests |
| `mobile/` | Expo mobile client and its separate setup guide |
| `scripts/` | Training, packaging, inference, validation and preserved research tools |
| `notebooks/` | Serving and training notebooks |
| `client/` | Final serving notebook, required package hashes and startup guide |
| `data/` | Versioned catalogs, policies, plans and nonimage annotations |
| `docs/`, `context/` | Architecture, decisions, reports, runbooks, scope and evidence limits |
| `frontend/` | Earlier standalone AI frontend retained for rollback |

The active release is `styles-20261106-01`: 18 Hair, 13 Makeup and 8 Nails styles, including the approved expanded catalog. Makeup uses `MAKEUP-001-CORRECTIVE-001`, not the rejected early targets or experimental compositors. See [application evidence](../experiments/makeup-corrective-application-results-20261106.md).

## Edit and push

The repository is public. Anyone can view, clone and fork it. Public visibility does not grant direct write access. To push directly to this repository, the owner invites the client's GitHub account under repository Settings, Collaborators, and the client accepts. Each person authenticates with their own GitHub credentials. See [GitHub collaborator permissions](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/permission-levels-for-a-personal-account-repository).

A collaborator can create a branch and open a pull request:

```powershell
git switch main
git pull --ff-only origin main
git switch -c client/my-change
# Edit and run the relevant checks.
git add path/to/changed-file
git commit -m "Describe the change"
git push -u origin client/my-change
```

Anyone without collaborator access can use GitHub's Fork button, clone their own fork, push there and open a pull request to this repository. A fork does not inherit the owner's running Render service, database, private datasets or credentials. Account ownership transfer is separate from sharing source.

## Run the website locally

Use Node 24.7.0 as configured in `render.yaml`. From `beautycore/`:

```powershell
npm ci
Copy-Item .env.local.example .env.local
# Enter your own development configuration in .env.local.
npm run dev
```

Use a separate development database for schema changes and demo seeding. `npm run db:seed` clears and reloads demo rows. A source handoff does not authorize reseeding the existing deployed database. The example environment is a template with historical provider options; the current scheduled deployment values are in `render.yaml` and [the Render runbook](render-kaggle-demo.md). Read [the unified local guide](unified-beautycore.md) for the existing Windows launchers and backend setup. Read [mobile/README.md](../../mobile/README.md) for the separate Expo app.

Useful website checks from `beautycore/` are `npm run typecheck`, `npm run test:style-release`, `npm run test:business` and `npm run build`. Backend checks run from the repository root with `python -m pytest -o "pythonpath=backend scripts" backend/tests`; their Python environment and synthetic fixtures are separate from the pinned Kaggle inference environment. Reports distinguish a local test from real GPU generation.

The 7 November handoff run passed the website checks and 1,016 backend tests, with 18 backend failures in historical catalog, packaging, experiment and worker checks. The full backend suite is not green. Some retained packaging/reproduction tests also require private assets that are intentionally absent from a public clone. See [the exact validation record](../experiments/client-source-publication-20261107.md) before rerunning older experiments. Do not assume every historical packager can rebuild the current release.

After correcting Git line ending conversion, a clean public source export passed 47 critical Makeup API, runtime, serving notebook startup and corrective training admission tests. This verifies the source handoff independently of the private working folder. It is not a fresh GPU or live website generation result.

## Existing deployment and future releases

Website: https://beautycore-demo.onrender.com

The latest directly observed Live Render web release is commit `4689b4c5b4ba6e0312d9333f0f7411cd9aee5770` on 9 November 2026, including the client enhancements and generation recovery fix. The dashboard confirms branch `main` and `beautycore` root. Build is `npm ci --include=dev && npm run build`; start is `npm run start -- --hostname 0.0.0.0 --port $PORT`; health is `/api/health`. Auto Deploy is Off in both the dashboard and versioned Blueprint. [Release receipt](../experiments/generation-recovery-deployment-20261109.md).

After reviewing a website change, merge and push it to `main` through the repository's normal workflow. The current service does not require updating the historical serving branch. Preserve that branch and earlier releases for reference.

An authorized Render operator can then use Manual Deploy, Deploy latest commit. Confirm the linked branch, dashboard setting and exact deployed commit first. Pushing source alone is not proof of a live deployment. If the client uses their own fork, create or reconnect a Render service to that fork with its own database and secrets. [Render deployment documentation](https://render.com/docs/deploys) explains manual and automatic deployment.

Repository access does not grant Render workspace or Neon database access. Arrange the appropriate account invitations or a deliberate separate deployment. Existing secrets remain in the relevant provider settings, never in Git. Keep the backend key consistent between Render and Kaggle, and keep existing signing secrets stable if retaining existing sessions and signed data.

## Private model packages are supplied separately

Git contains source, not model binaries, portrait images, environment files, installed dependencies, caches or generated galleries. The existing `.gitignore` preserves that boundary. Keep all retained originals locally. The complete local serving handoff is `artifacts/beautycore-client-all-features-20261106.zip`. The two required model inputs also exist in the local `client/` folder but are intentionally ignored by Git.

The public copies of `notebooks/hair_expansion_validation.ipynb` and `notebooks/makeup_expansion_completion.ipynb` replace embedded private fixtures with external file lookup under `/kaggle/input`. Their filenames and original SHA256 checks remain. The original notebooks retain their embedded fixtures locally. The final production serving notebook is unchanged.

Keep the `.gitattributes` rules for the reviewed Makeup JSON files and final serving notebooks. Those files have byte hash contracts. Changing line endings alone can prevent import or fail the handoff manifest, even when the visible JSON or code looks identical.

| Required filename | Bytes | SHA256 |
| --- | ---: | --- |
| `capstone_train002_20260928_v1.bin` | 171360891 | `f0d1fed52e00b6c5a1da2cade3731237675cdebbfc0b2cde3b2dbda99a4019ac` |
| `beautycore_makeup_release_20261106.bin` | 75246586 | `0c657ae4d2b62e11bd8c5728321330d5416fbfd1d36354d8482ac548f1449357` |

Provide these packages to the intended client through private file or Kaggle dataset access. The client needs exactly one attached copy of each filename, with no duplicate legacy input. These packages include all custom feature adapters and required CPU assets. Full FLUX Base weights download at startup from the pinned revision. No raw training dataset or retraining is required for serving. Reproducing training additionally requires the private approved paired data and its review/provenance artifacts.

## Current Kaggle startup limitation

The supplied notebook does not pin Kaggle's Docker image in its metadata. The reviewed host is Python 3.12.13, Torch 2.10.0+cu128, CUDA 12.8 and Tesla T4. A fresh notebook reported Python 3.13.16, Torch 2.11.0+cu130 and CUDA 13.0 and was correctly refused before model loading. The following attempt stopped earlier at zero or multiple GPU filename matches. Neither attempt establishes a working new production connection.

Retain the original successful notebook environment if Kaggle still offers it. Selecting original in a newly created notebook may retain the wrong new image. Keep the version and package guards. Correct the attachments first, then verify the actual runtime at Cell 1. See [the exact diagnosis](../experiments/makeup-serving-runtime-mismatch-20261106.md) and [client startup instructions](../../client/START-HERE.md).

The existing three Kaggle Secrets are `AI_BACKEND_API_KEY`, `AI_REMOTE_API_KEY` and `GEMINI_API_KEY`. Configure them privately. Kaggle runs the GPU worker and CPU facade, then registers its changing tunnel with Render. Keep the serving session running and wait for `CONNECTED TO WEBSITE`. This is scheduled compute, not an always available GPU service.

The accepted 13 Makeup application outputs and Hair/Nails crop checks remain valid. The new live serving connection, fresh portrait generation on the website, full hand Nails, Consultation/save/booking walkthrough and separate mobile acceptance remain unverified. Publishing this handoff does not close those gates.

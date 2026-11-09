# Generation recovery web deployment

Date: 9 November 2026. Progress DONE. Evidence VERIFIED for Git publication, Render release and public web checks. Authenticated GPU acceptance remains NEEDS VERIFICATION.

Supervisor explicitly requests merging the verified client based fix and deploying it on Render, then says continue after opening the dashboard. The earlier Windows browser attempt stopped before any merge or deployment because its current URL could not be determined safely. Work resumed through the user opened in app Render dashboard.

## Exact publication

`main` was fast forwarded from `c82e0366e43c003a23fba52b7d6dc0da5e23aa57` to `4689b4c5b4ba6e0312d9333f0f7411cd9aee5770`. Normal push and subsequent remote head inspection verify the result. The fix includes the latest client branch at `efd63d763ce5b194e2df9eb1b742593d87c81060`, including inventory and consultation history filters. The original client branch remains unchanged. No force push or conflict resolution was needed.

The client's inventory change already has its expected tables, functions and consumption policy column in the project's configured database. The preflight used SELECT metadata queries only and printed booleans, never credentials or customer data. No migration, seeding or database mutation was performed. A separate existing inventory suite passes 29 tests, in addition to the 153 focused recovery/application tests and full production build preserved in the implementation report.

## Render release

The signed in dashboard confirms service `beautycore-demo`, ID `srv-db4ftmbbc2fs73blpkr0`, currently deploys `main`, root `beautycore`. Build is `npm ci --include=dev && npm run build`; start is `npm run start -- --hostname 0.0.0.0 --port $PORT`. Auto Deploy is Off. This corrects DOCUMENTATION DRIFT in the older handoff guide, which still named the historical serving branch.

One Manual Deploy, Deploy latest commit was submitted. Render deployment `dep-dborks1srm7s73ct9al0` identifies exact source `4689b4c` and reports **Deploy succeeded | Live**, duration **2m 1s**. Dashboard start is 9 November 2026, 8:20 PM GMT+8. No service settings, secrets, plan or provider resources changed.

Website: https://beautycore-demo.onrender.com

Release: https://dashboard.render.com/web/srv-db4ftmbbc2fs73blpkr0/deploys/dep-dborks1srm7s73ct9al0

## Public verification

Independent read only HTTP checks at `2026-11-09T12:23:45.367Z` verify:

| Route or evidence | Result |
| :--- | :--- |
| `/api/health` | HTTP 200 |
| `/api/auth/session`, without cookies | HTTP 200 |
| `/api/ai/features`, without cookies | HTTP 401 |
| `/client/hair-studio` | HTTP 200 |
| Thirteen served JavaScript assets | Contain the recovery journal namespace, Continue browsing and Check existing preview controls |

The live release therefore serves the corrected web code and retains the anonymous AI authorization boundary. No generation request was sent. Runpod, Kaggle backup, weights, datasets, catalog and model settings are unchanged. Current GPU availability and a real authenticated navigation/generation run on this release are not established by these checks.

Local receipts are retained at `artifacts/generation-recovery-deployment-20261109/`: Render screenshots, `public-smoke.json`, inventory test output and deployment metadata. Deployment notes published afterward change documentation/context only and do not require a second web build.

Client next step: refresh the website to load the release, then test a new generation while moving between studios. Existing jobs lost before this fix were not retroactively journaled. A stopped worker or expired gateway job remains a separate availability boundary.

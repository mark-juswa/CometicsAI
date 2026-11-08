# BeautyCore sign-in HTML response recovery — 9 November 2026

Status: VERIFIED for local API recovery and affected automated tests.

The supplied screenshot displayed a JSON parsing exception beginning with an HTML DOCTYPE. A direct local probe reproduced the underlying condition: the BeautyCore Next.js development server on port 3000 returned HTTP 404 with `text/html` for `/api/auth/login` and `/api/auth/session`, while `/login` and `/api/health` were reachable. Process inspection confirmed the expected BeautyCore project. Required database/session environment settings were present; their values were not printed.

The verified project-specific development server was stopped. Its `.next/dev` compiled cache was moved to a uniquely named sibling backup within the project's ignored `.next` directory, with resolved paths and non-link directories checked before the move. The cache was preserved rather than deleted. The development server was restarted from the same BeautyCore folder on port 3000. This restored the missing routes; no application data or protected AI resources were moved.

`lib/auth-response.ts` now validates JSON responses and account payloads. `context/AuthContext.tsx` uses it for sign-in, registration and session restoration. HTML/framework error pages and malformed payloads produce a readable account-service error. Existing credential errors remain unchanged, and invalid payloads cannot establish a local authenticated user. The helper contains no authentication bypass or account reset.

Verification:

- `GET /api/auth/session` without a cookie: HTTP 200 JSON.
- `POST /api/auth/login` with empty credentials: HTTP 400 JSON.
- Existing client sign-in: HTTP 200 JSON, correct client role, session cookie issued.
- Following session read using that cookie: HTTP 200 JSON, correct client role. Credentials and tokens were not output.
- Auth-response and business UI suites: 18 tests passed, including the screenshot's HTML-404 regression and existing booking, image, availability and payment UI workflows.
- TypeScript check passed after the development cache was rebuilt. The first check overlapped the cache recovery and encountered invalid old generated route declarations; the repeat passed against the stable cache.
- Protected manifest comparison: 265 source files checked, zero changed hashes.

No database migration, seed, account edit, image update, AI request, model/dataset modification, or cloud deployment was performed during this recovery. The local development server remains running at `http://localhost:3000`; reload the login page to pick up the refreshed client bundle.

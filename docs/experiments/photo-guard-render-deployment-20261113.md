# Photo check website release, 13 November 2026

Supervisor explicitly requests publishing the changes to Render. This authorizes the website release, not a paid GPU allocation or a Runpod image cutover.

Source `de883e8cecb2393999569d90a9d831f327e94285` is published on GitHub main and codex/consultation-photo-guards. It retains the client's price updates through a005550. Private model archives, photos, detector binaries, local images and credentials are excluded from Git. The local checks recorded in the implementation report remain 113 backend, 57 website, 33 client price tests, native detector checks, staged API verification, TypeScript and production build.

The actual Render dashboard confirms beautycore-demo, service srv-db4ftmbbc2fs73blpkr0, source main. Previous Live release was a005550, deployment dep-dbpa0l8n74is73dbc8e0. Manual Deploy latest commit created dep-dbr7578ae00c73eq4ku0 for exact source de883e8. VERIFIED final status Deploy succeeded | Live at 10:17:22 AM Asia/Manila, duration 2m28s. Cloud compilation, TypeScript and startup health checks passed. [Deployment](https://dashboard.render.com/web/srv-db4ftmbbc2fs73blpkr0/deploys/dep-dbr7578ae00c73eq4ku0).

VERIFIED public checks after Live: /api/health 200 with status ok, /how-ai-works 200 with training text, /try-consultation 200, anonymous /api/ai/features 401, /api/auth/session 200. Receipt: artifacts/photo-suitability-20261113/render-live-smoke.json. No authenticated generation or new server photo rejection is inferred from website liveness.

The Render root remains beautycore. Only the website message relay runs here. Backend photo suitability, Gemini prompts and recommendation ranking run on the separate Runpod CPU API. Those remain locally packaged, not live: the candidate image beautycore-runpod:photo-guard-a40-20261113-03 is not published or installed on a Pod. No model retraining, secret change, database migration, GPU generation or Runpod operation was performed for this website release. Kaggle backup is unchanged.

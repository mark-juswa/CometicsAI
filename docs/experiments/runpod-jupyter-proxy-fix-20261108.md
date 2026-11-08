# Runpod Jupyter proxy login correction

DONE source correction, Linux regression checks and public image publication. VERIFIED local reproduction and corrected image behavior. NEEDS VERIFICATION live Pod update and browser login. No paid resource or cloud setting changed by Codex.

## Root cause

User logs show Jupyter rejecting the public HTTPS Origin because Runpod forwards an internal Host header. Password POST then returns 404. The earlier password length failure was separately corrected; this is a subsequent proxy integration defect. Original direct localhost authentication tests did not reproduce the proxy headers and were insufficient to establish live Runpod login.

The exact installed Jupyter implementation compares Origin against Host, then its configured allow_origin. A real local test using the observed internal Host pattern reproduced HTTP404. CLI configuration of an exact allowed origin changed login to302 and authenticated contents/JupyterLab to200. Requests without an XSRF token remained403 and an unrelated origin remained404. [Jupyter configuration reference](https://jupyter-server.readthedocs.io/en/stable/other/full-config.html).

## Correction

`runtime.notebook_proxy_config` derives one HTTPS origin from the provider supplied RUNPOD_POD_ID and fixed HTTP8888 proxy hostname. It validates the Pod ID, configures that exact origin and trusts forwarded scheme/address headers for SSL termination. No wildcard origins, password bypass, unauthenticated contents API or disabled XSRF check. Local use without a Pod ID retains the original configuration. No model generation, dependency, profile, catalog, facade, registrar or website behavior changed.

Corrected A6000 image:

```
markuos/beautycore-runpod@sha256:614bddb4352ef3127251583f062240ef1fb749e08a7cb137027f3c1cbf090ffa
```

Public anonymous manifest GET200 and digest equality verified. Original images remain intact. The new context differs from the preceding A6000 context only in runtime.py and its manifest. Same four environments, original archives, model hashes and all39 styles.

## Verification

31 focused tests pass. The built image's default startup, with a synthetic provider Pod ID and proxy Host/Origin headers, independently reproduces the fix: baseline login404, fixed login302, authenticated contents200, authenticated lab200, missing XSRF403 and unrelated origin404. Both CPU vision models, all four pip checks, exact source/GPU package checks and actual archive/preflight/overlay checks pass again. No GPU inference occurred. Only owned temporary local containers were removed; original branch/index, research, inputs and artifacts remain intact.

Sanitized synthetic logs and structured receipts are retained under `docs/experiments/runpod-docker-20261108/proxyfix/`. No user credentials or supplied credential screenshots are published. Structured receipt: [JSON](runpod-jupyter-proxy-fix-20261108.json).

## Apply to the existing Pod

Edit the existing Pod image to the corrected digest, preserving its volume, 20+ character notebook password, other secrets, HTTP8888 and empty start command. Apply the change and allow container startup. Do not delete the Pod or create a duplicate. Use its HTTPS8888 URL with /lab and no token query, then log in with the existing notebook password. Runpod's token based unauthenticated API status probe may still receive403 with this password protected setup; successful browser login is a separate check. Actual hardware, private input staging, Base startup and real output validation still follow. Render is not connected by this image change.

Live recovery follow up: user supplied browser screenshot now shows the authenticated JupyterLab Launcher after the corrected image instructions. Live browser login/GUI recovery is visually established. Actual terminal operation, GPU/RAM/disk checks, Base load and AI/website acceptance remain unverified.

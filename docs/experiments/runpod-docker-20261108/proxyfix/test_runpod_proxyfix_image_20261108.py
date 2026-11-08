"""Reproduce the observed internal-Host/public-Origin failure with real Jupyter."""
from pathlib import Path
import json, os, secrets, subprocess, time
from uuid import uuid4
import httpx

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/runpod-proxy-fix-20261108"
OUT = OUT / "image-proxy-proof"
OUT.mkdir(exist_ok=False)
IMAGE = "beautycore-runpod:styles-20261106-01-a6000-build-20261108"
ORIGIN = "https://fixturepodabc-8888.proxy.runpod.net"
REPORT = {"real_gpu_generation": False, "cases": {}}

def docker(args):
    return subprocess.check_output(["docker", *args], stderr=subprocess.STDOUT).decode("utf-8", errors="replace").strip()

for fixed in (False, True):
    label = "fixed" if fixed else "baseline"
    name = "beautycore-proxy-proof-" + uuid4().hex[:10]
    password = secrets.token_urlsafe(24)
    env = dict(os.environ, JUPYTER_PASSWORD=password)
    args = ["docker", "run", "-d", "--name", name, "-p", "127.0.0.1::8888", "-e", "JUPYTER_PASSWORD"]
    if fixed:
        args += ["-e", "RUNPOD_POD_ID=fixturepodabc", "beautycore-runpod:styles-20261106-01-a6000-proxyfix-20261108"]
    else:
        args += [IMAGE]
    created = False
    try:
        subprocess.run(args, env=env, capture_output=True, check=True)
        created = True
        address = docker(["port", name, "8888/tcp"]).splitlines()[0]
        with httpx.Client(base_url="http://" + address, timeout=10, follow_redirects=False,
                          headers={"Host": "100.65.37.38:60292", "X-Forwarded-Proto": "https"}) as client:
            deadline = time.monotonic() + 75
            while True:
                try:
                    if client.get("/login").status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                if time.monotonic() > deadline:
                    raise RuntimeError(label + " notebook not ready")
                time.sleep(1)
            xsrf = client.cookies.get("_xsrf")
            cookie = {"Cookie": "_xsrf=" + xsrf}
            if fixed:
                missing = client.post("/login", headers={**cookie, "Origin": ORIGIN}, data={"password": password})
                assert missing.status_code == 403
                wrong = client.post("/login", headers={**cookie, "Origin": "https://unrelated.example"},
                                    data={"password": password, "_xsrf": xsrf})
                assert wrong.status_code in (403, 404)
                REPORT["cases"]["missing_xsrf"] = missing.status_code
                REPORT["cases"]["unrelated_origin"] = wrong.status_code
            result = client.post("/login?next=%2Flab", headers={**cookie, "Origin": ORIGIN, "Referer": ORIGIN + "/login"},
                                 data={"password": password, "_xsrf": xsrf})
            REPORT["cases"][label + "_login"] = result.status_code
            if fixed:
                assert result.status_code in (302, 303)
                browser_cookie = "; ".join(k + "=" + v for k, v in client.cookies.items())
                auth = {"Cookie": browser_cookie, "Origin": ORIGIN}
                contents = client.get("/api/contents", headers=auth)
                lab = client.get("/lab", headers=auth)
                assert contents.status_code == lab.status_code == 200
                REPORT["cases"].update(authenticated_contents=contents.status_code, authenticated_lab=lab.status_code)
            else:
                assert result.status_code in (403, 404)
    finally:
        if created:
            logs = docker(["logs", name])
            assert password not in logs
            (OUT / (label + "-jupyter.log")).write_text(logs, encoding="utf-8")
            docker(["rm", "-f", name])
        (OUT / "proxy-login-proof.json").write_text(json.dumps(REPORT, indent=2) + "\n")
REPORT["status"] = "PASS"
(OUT / "proxy-login-proof.json").write_text(json.dumps(REPORT, indent=2) + "\n")
print(json.dumps(REPORT, indent=2))

"""Bounded real application validation, no model training or generation retries."""
import base64
from hashlib import sha256
from html import escape
from io import BytesIO
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen
from uuid import uuid4
from zipfile import ZipFile, ZIP_DEFLATED


def request(url, headers, data=None):
    # A response loss is ambiguous. Never automatically resend a generation POST.
    with urlopen(Request(url, headers=headers, data=data), timeout=180) as response:
        return response.status, json.load(response)


def multipart(image, style, **fields):
    boundary = "makeup-validation-" + uuid4().hex
    raw = bytearray()
    for key, value in {"style_id": style, **fields}.items():
        raw.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    raw.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="source.png"\r\nContent-Type: image/png\r\n\r\n'.encode())
    raw.extend(image)
    raw.extend(f'\r\n--{boundary}--\r\n'.encode())
    return bytes(raw), "multipart/form-data; boundary=" + boundary


def validate_makeup(payload, style, candidate, prompt):
    m = payload["metadata"]
    required = {"feature": "makeup", "style_id": style, "adapter_id": candidate["adapter_id"],
                "adapter_sha256": candidate["checkpoint_sha256"], "lora_active": True,
                "base_model_id": candidate["base_model_id"], "base_model_revision": candidate["base_model_revision"],
                "prompt_presets_sha256": candidate["prompt_presets_sha256"], "prompt": prompt,
                "steps": 20, "seed": 1977, "guidance": 4.0}
    if (payload.get("status") != "completed" or payload.get("generator") != "flux2_klein_base_makeup001_corrective001"
            or any(m.get(k) != v for k, v in required.items())):
        raise ValueError("Application output is not the accepted corrective model/prompt/settings")
    return decode_image(payload)


def decode_image(payload):
    from PIL import Image
    item = payload["image"]
    if (item.get("content_type") != "image/png" or item.get("width") != 512 or item.get("height") != 512
            or not item["data_url"].startswith("data:image/png;base64,")):
        raise ValueError("Application PNG metadata differs")
    raw = base64.b64decode(item["data_url"].split(",", 1)[1], validate=True)
    with Image.open(BytesIO(raw)) as image:
        if image.format != "PNG" or image.size != (512, 512):
            raise ValueError("Application output is not a 512 PNG")
        image.verify()
    return raw


def run(work):
    from kaggle_secrets import UserSecretsClient
    work = Path(work)
    cpu, gpu = work / "cpu-src", work / "gpu-src"
    output = work / "application-results"
    output.mkdir(exist_ok=False)
    report = {"schema": "makeup-corrective-application-results-v1", "status": "IN_PROGRESS",
              "production_registered": False, "automatic_generation_retries": 0, "cases": []}
    secret = UserSecretsClient()
    api_headers = {"X-AI-Backend-Key": secret.get_secret("AI_BACKEND_API_KEY"),
                   "X-AI-User-Id": "corrective-application-validation"}
    gpu_headers = {"X-API-Key": secret.get_secret("AI_REMOTE_API_KEY")}
    facade, worker = "http://127.0.0.1:8800", "http://127.0.0.1:8765"
    candidate = json.loads((cpu / "demo_bundle.json").read_text())["makeup_candidate"]
    prompts = json.loads((cpu / "data/makeup/DATA-M001-corrective/inference_presets.json").read_text())["styles"]
    panels = []
    try:
        for feature, count in (("hairstyle", 18), ("makeup", 13), ("nails", 8)):
            _, catalog = request(f"{facade}/features/{feature}/styles", api_headers)
            if len(catalog) != count or len({s['id'] for s in catalog}) != count:
                raise ValueError("Application catalog scope differs: " + feature)
            report[feature + "_catalog"] = catalog
        if {s["id"] for s in report["makeup_catalog"]} != {s["id"] for s in prompts}:
            raise ValueError("Application Makeup catalog and accepted captions differ")
        _, readiness = request(facade + "/deployment/readiness", api_headers)
        if readiness.get("ready") is not True:
            raise RuntimeError("Application readiness failed")
        report["readiness_before"] = readiness
        source = cpu / "candidate/fixtures/054109.png"
        jobs = [("hairstyle", "exp_french_bob_wispy", source, None)]
        for i, style in enumerate(prompts):
            identity = ("054109", "056266")[i % 2]
            jobs.append(("makeup", style["id"], cpu / f"candidate/fixtures/{identity}.png", style["caption"]))
            if i == 3:
                jobs.append(("nails", "classic_red", gpu / "gate1/inputs/nails.png", None))
            if i == 8:
                jobs.append(("hairstyle", "exp_wolf_cut", source, None))
        for feature, style, source, prompt in jobs:
            print("APPLICATION CASE", feature, style, flush=True)
            raw_source = source.read_bytes()
            data, content_type = multipart(raw_source, style, **({"inference_steps": "8"} if feature == "nails" else {}))
            started = time.monotonic()
            if feature == "nails":
                # Existing prepared crop tests GPU ownership only, not full hand fitting.
                _, payload = request(worker + "/nails/generate", {**gpu_headers, "Content-Type": content_type}, data)
            else:
                status, job = request(facade + f"/features/{feature}/generate",
                                      {**api_headers, "Content-Type": content_type}, data)
                if status != 202 or not job.get("job_id"):
                    raise RuntimeError("Application did not admit the generation")
                report["admitted_job_id"] = job["job_id"]
                deadline = time.monotonic() + 240
                while True:
                    _, state = request(facade + f"/jobs/{job['job_id']}", api_headers)
                    if state.get("result_available"):
                        break
                    if time.monotonic() > deadline:
                        raise TimeoutError("Admitted generation has uncertain completion. Do not replay.")
                    time.sleep(2)
                _, payload = request(facade + f"/jobs/{job['job_id']}/result", api_headers)
            raw = validate_makeup(payload, style, candidate, prompt) if feature == "makeup" else decode_image(payload)
            _, state = request(worker + "/status", gpu_headers)
            verification = state.get("active_adapter_verification") or {}
            if (state.get("foundation_load_count") != 1 or state.get("gpu_runtime_ready") is not True
                    or verification.get("tensor_equality_verified") is not True):
                raise ValueError("Shared worker foundation/active tensor verification failed")
            m = payload["metadata"]
            if not state.get("requests") or state["requests"][-1].get("adapter_sha256") != m.get("adapter_sha256"):
                raise ValueError("Application and shared worker adapter provenance disagree")
            name = f"{feature}-{style}"
            (output / (name + ".png")).write_bytes(raw)
            (output / (name + ".json")).write_text(json.dumps({k:v for k,v in payload.items() if k != 'image'}, indent=2))
            row = {"feature": feature, "style_id": style, "source_sha256": sha256(raw_source).hexdigest(),
                   "output_sha256": sha256(raw).hexdigest(), "metadata": m,
                   "seconds": round(time.monotonic() - started, 3), "active_verification": verification}
            report["cases"].append(row)
            if feature == "makeup":
                identity = source.stem
                accepted = (cpu / f"candidate/accepted/{identity}-{style}.png").read_bytes()
                row["accepted_raw_sha256"] = sha256(accepted).hexdigest()
                row["byte_equal_to_accepted_raw"] = raw == accepted
                def img(data):
                    return '<img src="data:image/png;base64,' + base64.b64encode(data).decode() + '">'
                panels.append('<h2>' + escape(identity + " " + style) + '</h2><div>'
                              + img(raw_source) + img(accepted) + img(raw) + '</div>')
            (output / "results.json").write_text(json.dumps(report, indent=2))
        _, report["worker_status_after"] = request(worker + "/status", gpu_headers)
        report["status"] = "TECHNICAL_PASS_VISUAL_REVIEW_PENDING"
        report["limits"] = ["Reused development subjects, fresh user upload unverified.",
            "Nails prepared crop tests adapter switching, full hand application unchanged and not retested.",
            "No live website, save/book or mobile acceptance in this local Kaggle API test."]
    except Exception as error:
        # Preserve outputs and exact exception category, not secret-bearing URLs/headers.
        report["status"], report["error_type"] = "FAILED_OR_UNCERTAIN_NO_REPLAY", type(error).__name__
        print("STOP:", type(error).__name__, "Results preserved. Do not resend an admitted generation.", flush=True)
    finally:
        (output / "results.json").write_text(json.dumps(report, indent=2))
        (output / "review.html").write_text('<!doctype html><meta charset="utf-8"><title>Application validation</title>'
            '<style>body{font:16px sans-serif;background:#eee}div{display:flex;flex-wrap:wrap}img{width:32%;min-width:260px}</style>'
            '<h1>Original | Accepted model RAW | Application RAW</h1><p>Production remains on hold. Technical status: '
            + escape(report["status"]) + '</p>' + ''.join(panels), encoding="utf-8")
        archive = Path("/kaggle/working/makeup_corrective001_application_results.zip")
        if archive.exists():
            archive = archive.with_name("makeup_corrective001_application_results_" + uuid4().hex[:8] + ".zip")
        with ZipFile(archive, "x", ZIP_DEFLATED) as bundle:
            for path in output.iterdir():
                bundle.write(path, path.name)
        print("RESULT:", archive, report["status"], "cases", len(report["cases"]), flush=True)
        from IPython.display import display, FileLink
        display(FileLink(str(archive)))
    return report

"""Provider adaptation only; no GPU or generation requests in these tests."""
import json
from pathlib import Path
import pytest
from scripts import makeup_corrective_application_probe as probe


def ready(tmp_path, monkeypatch):
    work = tmp_path / "runs" / "fixture"
    work.mkdir(parents=True)
    (tmp_path / "latest-run.txt").write_text(str(work))
    (work / "session.json").write_text(json.dumps({"status": "READY_FOR_RUNPOD_VALIDATION",
                                                  "release_id": "styles-20261106-01"}))
    monkeypatch.setenv("AI_BACKEND_API_KEY", "fixture-backend" * 4)
    monkeypatch.setenv("AI_REMOTE_API_KEY", "fixture-remote" * 4)
    monkeypatch.delenv("BEAUTYCORE_PUBLIC_URL", raising=False)
    return work


def test_runpod_uses_existing_probe_env_and_persistent_archive_without_kaggle(tmp_path, monkeypatch):
    work = ready(tmp_path, monkeypatch)
    calls = []
    def run(observed, **options):
        calls.append((observed, options))
        assert options["secret_client"].get_secret("AI_BACKEND_API_KEY") == "fixture-backend" * 4
        return {"status": "TECHNICAL_PASS_VISUAL_REVIEW_PENDING"}
    monkeypatch.setattr(probe, "run", run)
    assert probe.runpod_main(["runpod", "--workspace", str(tmp_path)]) == 0
    assert len(calls) == 1 and calls[0][0] == work
    assert calls[0][1]["archive_directory"] == tmp_path / "validation"
    assert calls[0][1]["display_result"] is False
    assert calls[0][1]["execution_provider"] == "runpod"


@pytest.mark.parametrize("invalid", ["registered", "wrong_release", "website", "outside", "secret"])
def test_refuses_unsafe_probe_before_any_generation(tmp_path, monkeypatch, invalid):
    work = ready(tmp_path, monkeypatch)
    if invalid in ("registered", "wrong_release"):
        session = json.loads((work / "session.json").read_text())
        session["status" if invalid == "registered" else "release_id"] = "different"
        (work / "session.json").write_text(json.dumps(session))
    elif invalid == "website":
        monkeypatch.setenv("BEAUTYCORE_PUBLIC_URL", "https://fixture.example")
    elif invalid == "outside":
        (tmp_path / "latest-run.txt").write_text(str(tmp_path / "outside"))
    else:
        monkeypatch.setenv("AI_BACKEND_API_KEY", "short")
    monkeypatch.setattr(probe, "run", lambda *a, **k: pytest.fail("Generation must not be called"))
    with pytest.raises(ValueError):
        probe.runpod_main(["runpod", "--workspace", str(tmp_path)])


def test_uncertain_result_has_nonzero_exit_and_no_replay(tmp_path, monkeypatch):
    ready(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(probe, "run", lambda *a, **k: calls.append(1) or {"status": "FAILED_OR_UNCERTAIN_NO_REPLAY"})
    assert probe.runpod_main(["runpod", "--workspace", str(tmp_path)]) == 2
    assert calls == [1]


@pytest.mark.parametrize("uncertain", [False, True])
def test_existing_full_probe_archives_results_without_kaggle_and_never_replays(tmp_path, monkeypatch, uncertain):
    import base64
    import re
    from io import BytesIO
    from zipfile import ZipFile
    from PIL import Image
    work = tmp_path / "work"
    cpu, gpu = work / "cpu-src", work / "gpu-src"
    styles = json.loads((Path(__file__).resolve().parents[2] /
        "data/makeup/DATA-M001-corrective/inference_presets.json").read_text())["styles"]
    candidate = {"adapter_id": "fixture", "checkpoint_sha256": "fixture-hash", "base_model_id": "fixture-base",
                 "base_model_revision": "fixture-revision", "prompt_presets_sha256": "fixture-presets"}
    image = BytesIO()
    Image.new("RGB", (512, 512), "gray").save(image, format="PNG")
    raw = image.getvalue()
    for identity in ("054109", "056266"):
        path = cpu / f"candidate/fixtures/{identity}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        for style in styles:
            path = cpu / f"candidate/accepted/{identity}-{style['id']}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    path = gpu / "gate1/inputs/nails.png"
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    path = cpu / "data/makeup/DATA-M001-corrective/inference_presets.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"styles": styles}))
    (cpu / "demo_bundle.json").write_text(json.dumps({"makeup_candidate": candidate}))
    posts, payloads = [], []
    catalogs = {"hairstyle": ["hair" + str(i) for i in range(18)],
                "makeup": [s["id"] for s in styles], "nails": ["nail" + str(i) for i in range(8)]}
    def request(url, headers, data=None):
        if url.endswith("/styles"):
            return 200, [{"id": x} for x in catalogs[url.split("/")[-2]]]
        if url.endswith("/deployment/readiness"):
            return 200, {"ready": True}
        if data is not None:
            posts.append(url)
            feature = "nails" if url.endswith("/nails/generate") else url.split("/")[-2]
            style_id = re.search(rb'name="style_id"\r\n\r\n([^\r]+)', data)[1].decode()
            metadata = {"feature": feature, "style_id": style_id, "adapter_id": candidate["adapter_id"],
                "adapter_sha256": candidate["checkpoint_sha256"], "base_model_id": candidate["base_model_id"],
                "base_model_revision": candidate["base_model_revision"], "prompt_presets_sha256": candidate["prompt_presets_sha256"],
                "lora_active": True, "steps": 20, "seed": 1977, "guidance": 4.0,
                "prompt": next((s["caption"] for s in styles if s["id"] == style_id), "fixture hair/nail")}
            payload = {"status": "completed", "generator": "flux2_klein_base_makeup001_corrective001", "metadata": metadata,
                "image": {"content_type": "image/png", "width": 512, "height": 512,
                          "data_url": "data:image/png;base64," + base64.b64encode(raw).decode()}}
            payloads.append(payload)
            return (200, payload) if feature == "nails" else (202, {"job_id": "fixture-job"})
        if "/jobs/" in url:
            if uncertain:
                raise TimeoutError("synthetic uncertain job; do not repeat POST")
            return (200, payloads[-1]) if url.endswith("/result") else (200, {"result_available": True})
        assert url.endswith("/status")
        return 200, {"foundation_load_count": 1, "gpu_runtime_ready": True,
                     "active_adapter_verification": {"tensor_equality_verified": True},
                     "requests": [{"adapter_sha256": candidate["checkpoint_sha256"]}]}
    monkeypatch.setattr(probe, "request", request)
    archive = tmp_path / "archive"
    archive.mkdir()
    class Secrets:
        def get_secret(self, name):
            return "synthetic-secret-not-printed"
    report = probe.run(work, secret_client=Secrets(), archive_directory=archive,
                       display_result=False, execution_provider="runpod")
    assert len(posts) == (1 if uncertain else 16)
    assert report["automatic_generation_retries"] == 0
    assert report["execution_provider"] == "runpod"
    assert report["status"] == ("FAILED_OR_UNCERTAIN_NO_REPLAY" if uncertain else "TECHNICAL_PASS_VISUAL_REVIEW_PENDING")
    assert len(report["cases"]) == (0 if uncertain else 16)
    with ZipFile(next(archive.glob("*.zip"))) as bundle:
        saved = json.loads(bundle.read("results.json"))
        assert saved["status"] == report["status"]
        assert "review.html" in bundle.namelist()
        if uncertain:
            assert saved["admitted_job_id"] == "fixture-job"

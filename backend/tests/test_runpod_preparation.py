"""Offline Runpod preparation checks. No GPU, provider account or generation."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from fnmatch import fnmatchcase
from pathlib import Path
from types import SimpleNamespace
from contextlib import nullcontext

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


runtime = module("runpod_runtime_test", ROOT / "deploy/runpod/runtime.py")
package = module("runpod_package_test", ROOT / "scripts/package_runpod.py")


def test_verified_notebook_exports_definitions_without_starting_kaggle(tmp_path):
    notebook = ROOT / "notebooks/render_kaggle_makeup_corrective_demo.ipynb"
    original = notebook.read_bytes()
    namespace = {}
    exec(package.helpers(notebook), namespace)
    assert "CLIENT_WORK" not in namespace
    assert namespace["BUNDLES"][0][1] == package.DIGESTS[0]
    assert namespace["BUNDLES"][1][1] == package.DIGESTS[1]
    namespace["validated"](namespace["OPTIMIZED_SOURCES"])
    assert notebook.read_bytes() == original
    changed = tmp_path / "changed.ipynb"
    changed.write_bytes(original + b" ")
    with pytest.raises(ValueError, match="notebook changed"):
        package.helpers(changed)


def test_missing_private_archives_fail_before_output_creation(tmp_path):
    with pytest.raises(ValueError, match="Private serving input"):
        package.build(tmp_path / "output", tmp_path)
    assert not (tmp_path / "output").exists()


def test_container_context_allows_runtime_inventory_and_excludes_private_material():
    rules = (ROOT / "deploy/runpod/.dockerignore").read_text().splitlines()
    def allowed(name):
        result = True
        for rule in rules:
            if fnmatchcase(name, rule.removeprefix("!")):
                result = rule.startswith("!")
        return result
    for name in ("Dockerfile", ".dockerignore", "runtime.py", "registration.py", "release_setup.py",
                 "profile.json", "build-manifest.json", "requirements/gpu.txt"):
        assert allowed(name), name
    for name in (".env", "kaggle.json", "adapter.safetensors", "portrait.png", "inputs/model.bin"):
        assert not allowed(name), name


def test_distribution_tampering_and_traversal_are_refused(tmp_path):
    path = tmp_path / "runtime.py"
    path.write_bytes(b"reviewed")
    manifest = {"schema": "beautycore-runpod-build-v1", "files": {"runtime.py": sha256(b"reviewed").hexdigest()}}
    manifest_path = tmp_path / "build-manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    assert runtime.verify_distribution(tmp_path) == manifest
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="distribution changed"):
        runtime.verify_distribution(tmp_path)
    manifest["files"] = {"../outside": "0" * 64}
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="distribution changed"):
        runtime.verify_distribution(tmp_path)


def profile_case():
    profile = json.loads((ROOT / "deploy/runpod/profile.json").read_text())
    reviewed = json.loads((ROOT / "docs/experiments/unified-kaggle-gate2-review.json").read_text())["environment"]
    actual = deepcopy(reviewed)
    actual.update(gpu=profile["gpu"], gpu_total_bytes=24 * 1024**3, compute_capability=[8, 6])
    return actual, reviewed, profile


def test_candidate_profile_preserves_original_review_and_all_dependency_checks():
    actual, reviewed, profile = profile_case()
    original = deepcopy(reviewed)
    runtime.check_profile(actual, reviewed, profile, 32 * 1024**3)
    assert reviewed == original and reviewed["gpu"] == "Tesla T4"


def test_a6000_candidate_accepts_only_its_hardware_with_reviewed_dependencies():
    actual, reviewed, default = profile_case()
    candidate = json.loads((ROOT / "deploy/runpod/profiles/rtx-a6000.json").read_text())
    actual.update(gpu=candidate["gpu"], gpu_total_bytes=48 * 1024**3)
    runtime.check_profile(actual, reviewed, candidate, 32 * 1024**3)
    # Neither image silently accepts the other's GPU, or a smaller virtual allocation.
    with pytest.raises(ValueError, match="gpu"):
        runtime.check_profile(actual, reviewed, default, 32 * 1024**3)
    for field, bad in (("gpu", default["gpu"]), ("gpu_total_bytes", 24 * 1024**3),
                       ("cuda", "13.0"), ("packages", {}), ("diffusers_commit", "changed")):
        with pytest.raises(ValueError):
            runtime.check_profile(dict(actual, **{field: bad}), reviewed, candidate, 32 * 1024**3)
    with pytest.raises(ValueError):
        runtime.check_profile(actual, reviewed, candidate, 25 * 1024**3)
    assert default["gpu"] == "NVIDIA GeForce RTX 3090"


def test_unknown_profile_fails_without_creating_output(tmp_path):
    with pytest.raises(ValueError, match="Unknown Runpod GPU profile"):
        package.build(tmp_path / "output", tmp_path, profile="anything")
    assert not (tmp_path / "output").exists()


def test_notebook_proxy_trust_is_bound_to_this_pod_without_disabling_xsrf():
    assert runtime.notebook_proxy_config("") == ""
    source = runtime.notebook_proxy_config("fixturepodabc")
    settings = SimpleNamespace(ServerApp=SimpleNamespace())
    exec(source, {"c": settings})
    assert settings.ServerApp.allow_origin == "https://fixturepodabc-8888.proxy.runpod.net"
    assert settings.ServerApp.trust_xheaders is True
    assert not hasattr(settings.ServerApp, "disable_check_xsrf")
    assert "*" not in source
    for invalid in ("../other", "https://example.com", "pod\nprint('bad')", "pod;bad"):
        with pytest.raises(ValueError, match="RUNPOD_POD_ID"):
            runtime.notebook_proxy_config(invalid)


@pytest.mark.parametrize("field", ["python", "torch", "cuda", "gpu", "packages", "diffusers_commit",
                                    "gpu_total_bytes", "compute_capability", "cuda_available", "ram"])
def test_candidate_profile_rejects_wrong_or_insufficient_runtime(field):
    actual, reviewed, profile = profile_case()
    memory = 32 * 1024**3
    if field == "ram":
        memory = 25 * 1024**3
    elif field == "gpu_total_bytes":
        actual[field] = 16 * 1024**3
    elif field == "compute_capability":
        actual[field] = [7, 5]
    elif field == "cuda_available":
        actual[field] = False
    else:
        actual[field] = "different"
    with pytest.raises(ValueError):
        runtime.check_profile(actual, reviewed, profile, memory)


def test_container_limit_wins_over_larger_host_ram(tmp_path):
    proc = tmp_path / "meminfo"
    proc.write_text("MemTotal: 67108864 kB\n")
    cgroup = tmp_path / "cgroup"
    cgroup.mkdir()
    (cgroup / "memory.max").write_text(str(25 * 1024**3))
    assert runtime.usable_memory(proc, cgroup) == 25 * 1024**3
    (cgroup / "memory.max").write_text("max")
    assert runtime.usable_memory(proc, cgroup) == 64 * 1024**3


def readiness_case():
    source = json.loads((ROOT / "beautycore/lib/ai/style-release.json").read_text())
    models = next(row for row in source["baseline_model_catalogs"] if len(row["hairstyle"]) == 18)
    catalog = {"model_styles": models, "renderer_styles": source["renderer_styles"]}
    cap = {"release_id": source["release_id"], "manifest_sha256": source["manifest_sha256"], **deepcopy(catalog)}
    expected = {key: source[key] for key in ("release_id", "manifest_sha256")}
    expected["enabled_style_ids"] = sorted(s for values in models.values() for s in values if s.startswith("exp_"))
    expected["enabled_style_ids"] += [s for s in source["renderer_styles"] if s.startswith("exp_")]
    return {"ready": True, "foundation_load_count": 1, "style_capabilities": cap}, expected, catalog


def test_exact_current_catalog_is_required_and_unknown_ids_cannot_replace_baseline():
    response, expected, catalog = readiness_case()
    runtime.check_readiness(response, expected, catalog)
    response["style_capabilities"]["model_styles"]["makeup"][0] = "unsupported_fixture_id"
    with pytest.raises(ValueError):
        runtime.check_readiness(response, expected, catalog)


@pytest.mark.parametrize("feature", ["hairstyle", "makeup", "nails", "renderer", "digest", "base"])
def test_missing_feature_or_wrong_identity_refuses_readiness(feature):
    response, expected, catalog = readiness_case()
    if feature == "renderer":
        response["style_capabilities"]["renderer_styles"].pop()
    elif feature == "digest":
        response["style_capabilities"]["manifest_sha256"] = "0" * 64
    elif feature == "base":
        response["foundation_load_count"] = 2
    else:
        response["style_capabilities"]["model_styles"][feature].pop()
    with pytest.raises(ValueError):
        runtime.check_readiness(response, expected, catalog)


def test_missing_secrets_are_named_without_exposing_values():
    values = {"AI_BACKEND_API_KEY": "fixture-backend-" * 4, "AI_REMOTE_API_KEY": "fixture-gpu-" * 4,
              "GEMINI_API_KEY": "fixture-only"}
    runtime.secret_environment(values)
    values["AI_REMOTE_API_KEY"] = "short"
    with pytest.raises(ValueError) as error:
        runtime.secret_environment(values)
    assert "AI_REMOTE_API_KEY" in str(error.value) and "short" not in str(error.value)


def test_service_death_is_not_retried_as_generation_or_hidden_by_readiness():
    calls = []
    with pytest.raises(RuntimeError, match="Owned service exited"):
        runtime.wait_for("http://fixture/health", [SimpleNamespace(poll=lambda: 1)],
                         read=lambda *_: calls.append("read"))
    assert calls == []


def test_runtime_supervisor_stops_only_its_owned_process_group(monkeypatch):
    calls = []
    process = SimpleNamespace(pid=12345, poll=lambda: None, wait=lambda timeout: calls.append(("wait", timeout)))
    monkeypatch.setattr(runtime.os, "killpg", lambda pid, sig: calls.append((pid, sig)), raising=False)
    runtime.stop_process(process)
    assert calls == [(12345, runtime.signal.SIGTERM), ("wait", 15)]


@pytest.mark.parametrize("website", ["", "https://fixture.example"])
def test_foreground_startup_does_not_replace_lease_or_leave_owned_services(tmp_path, monkeypatch, website):
    response, expected, catalog = readiness_case()
    (tmp_path / "profile.json").write_text((ROOT / "deploy/runpod/profile.json").read_text())
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "cloudflared").write_bytes(b"synthetic executable, never run")
    processes, commands, killed, registrations = [], [], [], []
    monkeypatch.setattr(runtime, "HERE", tmp_path)
    monkeypatch.setattr(runtime, "verify_distribution", lambda: {"catalog": catalog})
    monkeypatch.setattr(runtime.sys, "platform", "linux")
    monkeypatch.setattr(runtime.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(runtime, "usable_memory", lambda: 32 * 1024**3)
    monkeypatch.setattr(runtime, "exclusive_lock", lambda _: nullcontext())
    monkeypatch.setattr(runtime.socket.socket, "connect_ex", lambda *_: 1)
    for key, value in {"AI_BACKEND_API_KEY": "fixture-backend-" * 4,
                       "AI_REMOTE_API_KEY": "fixture-gpu-" * 4, "GEMINI_API_KEY": "fixture",
                       "BEAUTYCORE_PUBLIC_URL": website}.items():
        monkeypatch.setenv(key, value)

    def assemble(_inputs, work):
        for directory in ("gpu-src", "cpu-src"):
            (work / directory).mkdir(parents=True)
        return SimpleNamespace(STYLE_RELEASE_EXPECTED=expected)

    def popen(args, **kwargs):
        commands.append(args)
        if args[0] == str(workspace / "cloudflared"):
            kwargs["stdout"].write("https://fixture.trycloudflare.com\n")
            kwargs["stdout"].flush()
        child = SimpleNamespace(pid=12300 + len(processes), poll=lambda: None, wait=lambda timeout: 0)
        processes.append(child)
        return child

    def register(*args):
        registrations.append(args[0])
        raise RuntimeError("Synthetic existing lease conflict")

    def end_wait(_):
        raise KeyboardInterrupt()

    monkeypatch.setattr(runtime, "assemble", assemble)
    monkeypatch.setattr(runtime.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0))
    monkeypatch.setattr(runtime.subprocess, "Popen", popen)
    monkeypatch.setattr(runtime, "wait_for", lambda *args, **kwargs: response)
    monkeypatch.setattr(runtime, "load_module", lambda *_: SimpleNamespace(website_root=lambda x: x, register=register))
    monkeypatch.setattr(runtime, "stop_process", lambda child: killed.append(child.pid))
    monkeypatch.setattr(runtime.time, "sleep", end_wait)
    with pytest.raises((KeyboardInterrupt, RuntimeError)):
        runtime.serve(workspace, tmp_path / "inputs")
    assert len(processes) == 3 and killed == [child.pid for child in reversed(processes)]
    assert registrations == ([website] if website else [])
    assert not any("generate" in str(command) for command in commands)
    work = Path((workspace / "latest-run.txt").read_text())
    record = json.loads((work / "session.json").read_text())
    assert record["status"] == "STOPPED_OR_FAILED" and record["full_generation_verified"] is False

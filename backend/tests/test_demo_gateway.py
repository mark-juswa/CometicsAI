"""Hosted-demo auth, ownership, long-running admission, and private result boundaries."""
import asyncio
from datetime import datetime, timedelta, timezone
from io import BytesIO
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx
from PIL import Image
import pytest

from app.demo_gateway import create_gateway, MAX_UPLOAD
from app.generation.remote_destination import valid_gpu_url

KEY = "test-backend-key-at-least-thirty-two-characters"
HEADERS = {"x-ai-backend-key": KEY, "x-ai-user-id": "client-one"}


def execute(test):
    return asyncio.run(test())


def fixture():
    inner = FastAPI()
    gate = asyncio.Event()
    started = asyncio.Event()
    calls = []
    identity = str(uuid4())
    @inner.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH"])
    async def route(path: str, request: Request):
        calls.append((request.method, path))
        if path == "consultations":
            return JSONResponse({"id": identity, "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()}, status_code=201)
        if path.endswith("/generate") or path.endswith("/generation") and request.method == "POST":
            started.set()
            await gate.wait()
            if b"fail" in await request.body():
                return JSONResponse({"detail": "controlled failure"}, status_code=422)
            return {"image": {"data_url": "data:image/png;base64,AA=="}, "status": "completed"}
        return {"ok": True}
    return inner, gate, started, calls, identity


def test_key_required_all_private_routes_and_no_arbitrary_proxy():
    async def scenario():
        inner, _, _, calls, _ = fixture()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_gateway(inner, KEY)), base_url="http://test") as client:
            assert (await client.get("/health")).status_code == 200
            for headers in ({}, {"x-ai-backend-key": "wrong"}, {"x-ai-backend-key": KEY}):
                assert (await client.get("/features", headers=headers)).status_code in {401, 403}
            for path in ("/status", "/hairstyle/generate", "/features?host=other", "/deployment/diagnostics"):
                assert (await client.get(path, headers=HEADERS)).status_code == 404
            response = await client.get("/features", headers=HEADERS)
            assert response.status_code == 200 and KEY not in response.text
            assert calls == [("GET", "features")]
    execute(scenario)


@pytest.mark.parametrize("feature", ["hairstyle", "makeup", "nails"])
def test_admission_returns_before_inference_serializes_and_binds_result(feature):
    async def scenario():
        inner, gate, started, calls, _ = fixture()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_gateway(inner, KEY)), base_url="http://test") as client:
            accepted = await client.post(f"/features/{feature}/generate", headers=HEADERS, content=b"photo")
            assert accepted.status_code == 202
            job = accepted.json()["job_id"]
            await started.wait()
            assert (await client.get("/jobs/" + job, headers=HEADERS)).json()["status"] == "generating"
            assert (await client.get("/jobs/" + job + "/result", headers=HEADERS)).status_code == 409
            assert (await client.get("/jobs/" + job, headers={**HEADERS, "x-ai-user-id": "other"})).status_code == 404
            assert (await client.post("/features/makeup/generate", headers=HEADERS)).status_code == 429
            gate.set()
            for _ in range(20):
                await asyncio.sleep(0)
                if (await client.get("/jobs/" + job, headers=HEADERS)).json()["status"] == "completed":
                    break
            result = await client.get("/jobs/" + job + "/result", headers=HEADERS)
            assert result.status_code == 200 and result.json()["status"] == "completed"
            assert result.headers["cache-control"] == "private, no-store"
            assert calls == [("POST", f"features/{feature}/generate")]
    execute(scenario)


def test_consultation_owner_and_background_generation():
    async def scenario():
        inner, gate, started, _, identity = fixture()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_gateway(inner, KEY)), base_url="http://test") as client:
            assert (await client.post("/consultations", headers=HEADERS, json={})).status_code == 201
            assert (await client.get("/consultations/" + identity, headers={**HEADERS, "x-ai-user-id": "other"})).status_code == 404
            accepted = await client.post(f"/consultations/{identity}/recommendations/look-1/generation", headers=HEADERS)
            assert accepted.status_code == 202
            await started.wait()
            gate.set()
            await asyncio.sleep(.01)
            assert (await client.get("/jobs/" + accepted.json()["job_id"] + "/result", headers=HEADERS)).status_code == 200
    execute(scenario)


def test_failed_jobs_record_original_status_without_retry():
    async def scenario():
        inner, gate, _, calls, _ = fixture()
        gate.set()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_gateway(inner, KEY)), base_url="http://test") as client:
            accepted = await client.post("/features/nails/generate", headers=HEADERS, content=b"fail")
            await asyncio.sleep(.01)
            path = "/jobs/" + accepted.json()["job_id"]
            assert (await client.get(path, headers=HEADERS)).json()["status"] == "failed"
            assert (await client.get(path + "/result", headers=HEADERS)).status_code == 422
            assert len(calls) == 1
    execute(scenario)


def test_bounded_result_retention_and_expiry():
    async def scenario():
        inner, gate, _, _, _ = fixture()
        gate.set()
        now = [0]
        app = create_gateway(inner, KEY, max_jobs=1, clock=lambda: now[0])
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            first = (await client.post("/features/nails/generate", headers=HEADERS)).json()["job_id"]
            await asyncio.sleep(.01)
            now[0] += 1
            second = (await client.post("/features/makeup/generate", headers=HEADERS)).json()["job_id"]
            assert (await client.get("/jobs/" + first, headers=HEADERS)).status_code == 404
            await asyncio.sleep(.01)
            now[0] += 1801
            assert (await client.get("/jobs/" + second, headers=HEADERS)).status_code == 404
    execute(scenario)


def test_upload_bound_checked_before_dispatch():
    async def scenario():
        inner, _, _, calls, _ = fixture()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_gateway(inner, KEY)), base_url="http://test") as client:
            response = await client.post("/features/hairstyle/generate", headers=HEADERS, content=b"x" * (MAX_UPLOAD + 1))
            assert response.status_code == 413 and not calls
    execute(scenario)


def test_gateway_requires_strong_secret():
    with pytest.raises(ValueError):
        create_gateway(FastAPI(), "short")


def test_gpu_loopback_is_explicit_and_restricted(monkeypatch):
    monkeypatch.delenv("AI_GPU_LOOPBACK", raising=False)
    assert not valid_gpu_url("http://127.0.0.1:8765/hairstyle")
    monkeypatch.setenv("AI_GPU_LOOPBACK", "1")
    assert valid_gpu_url("http://127.0.0.1:8765/hairstyle")
    assert valid_gpu_url("https://worker.example/hairstyle")
    for value in ("http://remote.example:8765/hairstyle", "http://127.0.0.1:9999/nails", "http://127.0.0.1:8765/other", "http://u:p@127.0.0.1:8765/nails"):
        assert not valid_gpu_url(value)


@pytest.mark.parametrize("feature,style", [("hairstyle", "crew-cut"), ("makeup", "natural_makeup"), ("nails", "nude_pink")])
def test_actual_existing_handlers_keep_their_contract(feature, style):
    async def scenario():
        from app.main import app
        buffer = BytesIO()
        Image.new("RGB", (64, 64), "white").save(buffer, format="PNG")
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_gateway(app, KEY)), base_url="http://test") as client:
            accepted = await client.post(f"/features/{feature}/generate", headers=HEADERS,
                                         files={"image": ("photo.png", buffer.getvalue(), "image/png")}, data={"style_id": style})
            assert accepted.status_code == 202
            path = "/jobs/" + accepted.json()["job_id"]
            for _ in range(20):
                await asyncio.sleep(.01)
                if (await client.get(path, headers=HEADERS)).json()["status"] != "generating":
                    break
            response = await client.get(path + "/result", headers=HEADERS)
            assert response.status_code == 200, response.text
            assert response.json()["style"]["id"] == style
            assert response.json()["image"]["data_url"].startswith(("data:image/png;base64,", "data:image/jpeg;base64,"))
    execute(scenario)

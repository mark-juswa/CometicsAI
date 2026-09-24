"""Exercise the local app and Kaggle API contract without loading a GPU model."""

import base64
from io import BytesIO
import sys
from pathlib import Path

from fastapi.testclient import TestClient
import httpx
from PIL import Image

from app import main
from app.generation.remote_flux import RemoteFluxEngine


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts import kaggle_inference_server as gpu_server  # noqa: E402


def png() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (128, 128), "#8aafbb").save(buffer, format="PNG")
    return buffer.getvalue()


def test_real_style_catalog_and_local_to_gpu_contract(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/generate"
        assert request.headers["X-API-Key"] == "secret-value-for-test-only"
        assert b'crew_cut' in request.content
        return httpx.Response(200, json={"image": {"data_url": "data:image/png;base64," + base64.b64encode(png()).decode(),
                                                   "content_type": "image/png", "width": 128, "height": 128},
                                         "metadata": {"adapter_steps": 250}})

    client_class = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: client_class(transport=httpx.MockTransport(handler), **kwargs))
    monkeypatch.setattr(main, "engine", RemoteFluxEngine("https://example.trycloudflare.com", "secret-value-for-test-only"))
    client = TestClient(main.app)
    styles = client.get("/styles").json()
    assert [style["id"] for style in styles] == ["crew_cut", "bob_hair", "layered_hair"]
    assert client.post("/generate", data={"style_id": "pixie"}, files={"image": ("x.png", png(), "image/png")}).status_code == 400
    response = client.post("/generate", data={"style_id": "crew_cut"}, files={"image": ("x.png", png(), "image/png")})
    assert response.status_code == 200
    assert response.json()["generator"] == "remote_flux"
    assert response.json()["metadata"]["adapter_steps"] == 250


def test_gpu_endpoint_auth_validation_and_recoverable_request(monkeypatch):
    monkeypatch.setenv("HAIRCAPSTONE_API_KEY", "secret-value-for-test-only")
    monkeypatch.setattr(gpu_server.runtime, "ready", True)
    monkeypatch.setattr(gpu_server.runtime, "generate", lambda image, style: {
        "status": "completed", "generator": "flux2_klein_base_train001", "image": {
            "data_url": "data:image/png;base64," + base64.b64encode(png()).decode(),
            "content_type": "image/png", "width": 128, "height": 128},
        "metadata": {"adapter_steps": 250}})
    client = TestClient(gpu_server.app)
    files = {"image": ("portrait.png", png(), "image/png")}
    assert client.post("/generate", data={"style_id": "crew_cut"}, files=files).status_code == 401
    assert client.post("/generate", data={"style_id": "unknown"}, files=files,
                       headers={"X-API-Key": "secret-value-for-test-only"}).status_code == 400
    assert client.post("/generate", data={"style_id": "crew_cut"}, files={"image": ("x.txt", b"no", "text/plain")},
                       headers={"X-API-Key": "secret-value-for-test-only"}).status_code == 415
    response = client.post("/generate", data={"style_id": "crew_cut"}, files=files,
                           headers={"X-API-Key": "secret-value-for-test-only"})
    assert response.status_code == 200
    assert response.json()["metadata"]["adapter_steps"] == 250

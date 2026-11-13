"""Keep backend tests independent of the developer's local .env."""

import os
from pathlib import Path
import pytest


@pytest.fixture
def synthetic_photo_subject(monkeypatch):
    """Contract tests use drawn rectangles; detector evidence is tested separately."""
    monkeypatch.setattr('app.photo_suitability.check_subject', lambda *_: True)


def pytest_configure() -> None:
    os.environ["GENERATION_ENGINE"] = "mock"
    os.environ["MAKEUP_GENERATION_ENGINE"] = "mock"
    os.environ["NAILS_PREVIEW_MODE"] = "mock"
    os.environ["CONSULTATION_PROVIDER"] = "deterministic"
    os.environ["HAIRCAPSTONE_STYLE_REGISTRY_PATH"] = str(
        Path(__file__).resolve().parents[1] / "app" / "style_registry.json")

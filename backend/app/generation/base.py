"""Stable generation boundary for the mock and a future real engine."""

from dataclasses import dataclass, field
from typing import Protocol

from PIL import Image

from app.styles import Style


@dataclass(frozen=True)
class GeneratedImage:
    content: bytes
    content_type: str
    width: int
    height: int
    metadata: dict = field(default_factory=dict)


class GenerationEngine(Protocol):
    name: str

    async def generate(self, image: Image.Image, style: Style) -> GeneratedImage:
        """Return image bytes and dimensions for a validated portrait and style."""

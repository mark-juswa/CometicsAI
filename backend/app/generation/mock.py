"""Local development engine. It makes no hairstyle changes."""

from io import BytesIO

from PIL import Image

from app.generation.base import GeneratedImage
from app.styles import Style


class MockEngine:
    name = "mock"

    async def generate(self, image: Image.Image, style: Style) -> GeneratedImage:
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=92, optimize=True)
        return GeneratedImage(
            content=buffer.getvalue(),
            content_type="image/jpeg",
            width=image.width,
            height=image.height,
        )

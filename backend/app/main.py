"""Small local API for the System MVP."""

import base64
import os
import warnings
from io import BytesIO
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel

from app.generation.base import GenerationEngine
from app.generation.mock import MockEngine
from app.styles import STYLE_BY_ID, STYLES, Style


MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_777_216
MIN_DIMENSION = 64
MAX_DIMENSION = 4096
ALLOWED_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png"}
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


def configured_engine() -> GenerationEngine:
    mode = os.getenv("GENERATOR_MODE", "mock").strip().lower()
    if mode == "mock":
        return MockEngine()
    raise RuntimeError(f"Unsupported GENERATOR_MODE: {mode}. This MVP supports mock only.")


engine = configured_engine()
app = FastAPI(title="HAIR CAPSTONE API", version="0.1.0", openapi_url=None, docs_url=None, redoc_url=None)
origins = [origin.strip() for origin in os.getenv(
    "FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class StyleResponse(BaseModel):
    id: str
    name: str
    description: str
    status: str


class ImageResponse(BaseModel):
    data_url: str
    content_type: str
    width: int
    height: int


class GenerateResponse(BaseModel):
    status: str
    generator: str
    style: StyleResponse
    image: ImageResponse


def style_response(style: Style) -> StyleResponse:
    return StyleResponse(**vars(style))


async def validated_image(upload: UploadFile) -> Image.Image:
    if upload.content_type not in ALLOWED_FORMATS.values():
        raise HTTPException(status_code=415, detail="Please upload a JPG or PNG image.")

    content = await upload.read(MAX_FILE_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail="The image file is empty.")
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 8 MB or smaller.")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as source:
                if source.format not in ALLOWED_FORMATS:
                    raise HTTPException(status_code=415, detail="Please upload a JPG or PNG image.")
                if ALLOWED_FORMATS[source.format] != upload.content_type:
                    raise HTTPException(status_code=415, detail="The image type does not match the file.")
                width, height = source.size
                if not (MIN_DIMENSION <= width <= MAX_DIMENSION and MIN_DIMENSION <= height <= MAX_DIMENSION):
                    raise HTTPException(
                        status_code=422,
                        detail="Image width and height must each be between 64 and 4096 pixels.",
                    )
                if width * height > MAX_IMAGE_PIXELS:
                    raise HTTPException(status_code=422, detail="Image dimensions are too large.")
                source.load()
                return ImageOps.exif_transpose(source).convert("RGB")
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombWarning, Image.DecompressionBombError):
        raise HTTPException(status_code=400, detail="The uploaded file is not a readable image.") from None


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "generator": engine.name}


@app.get("/styles", response_model=list[StyleResponse])
async def styles() -> list[StyleResponse]:
    return [style_response(style) for style in STYLES]


@app.post("/generate", response_model=GenerateResponse)
async def generate(
    image: Annotated[UploadFile, File()],
    style_id: Annotated[str, Form()],
) -> GenerateResponse:
    style = STYLE_BY_ID.get(style_id)
    if style is None:
        raise HTTPException(status_code=400, detail="Please choose a valid hairstyle.")

    portrait = await validated_image(image)
    try:
        generated = await engine.generate(portrait, style)
    except Exception:
        raise HTTPException(status_code=500, detail="Generation failed. Please try again.") from None
    encoded = base64.b64encode(generated.content).decode("ascii")
    return GenerateResponse(
        status="completed",
        generator=engine.name,
        style=style_response(style),
        image=ImageResponse(
            data_url=f"data:{generated.content_type};base64,{encoded}",
            content_type=generated.content_type,
            width=generated.width,
            height=generated.height,
        ),
    )

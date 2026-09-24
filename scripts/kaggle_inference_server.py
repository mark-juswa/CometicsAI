"""Single GPU FLUX.2 Klein Base plus TRAIN-001 LoRA inference service."""

import asyncio
import base64
from contextlib import asynccontextmanager
from io import BytesIO
import json
import logging
import os
from pathlib import Path
import sys
import time
from typing import Annotated
import warnings

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.styles import REAL_STYLE_PROMPTS  # noqa: E402


LOGGER = logging.getLogger("haircapstone.inference")
TRAIN001_SHA256 = "7e3991f8a4e502573d3e82e9ac34c89fdf3f0b66fb337abb026a5b4c9ad080ff"
MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_777_216
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


def read_adapter_metadata(directory: Path) -> dict:
    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    import hashlib
    import struct
    if (metadata.get("schema_version") != 1
            or metadata.get("artifact_type") != "project_trained_lora"
            or metadata.get("experiment") != "TRAIN-001"
            or metadata.get("training_steps") != 250
            or metadata.get("checkpoint_sha256") != TRAIN001_SHA256
            or set(metadata.get("supported_style_ids", [])) != set(REAL_STYLE_PROMPTS)
            or metadata.get("checkpoint_file") != "adapter.safetensors"):
        raise RuntimeError("Adapter metadata does not identify the approved TRAIN-001 250-step LoRA")
    checkpoint = directory / "adapter.safetensors"
    if (not checkpoint.is_file() or checkpoint.stat().st_size != metadata.get("checkpoint_bytes")
            or hashlib.sha256(checkpoint.read_bytes()).hexdigest() != metadata.get("checkpoint_sha256")):
        raise RuntimeError("Adapter checkpoint is missing or failed SHA-256 verification")
    with checkpoint.open("rb") as file:
        header_length = struct.unpack("<Q", file.read(8))[0]
        if not 0 < header_length < 8 * 1024 * 1024:
            raise RuntimeError("Adapter is not a readable safetensors file")
        header = json.loads(file.read(header_length))
    if not isinstance(header, dict) or not any("lora" in name.lower() for name in header):
        raise RuntimeError("Adapter file contains no LoRA tensors")
    return metadata


class FluxRuntime:
    def __init__(self):
        self.ready = False
        self.pipe = None
        self.torch = None
        self.metadata = {}
        self.lock = asyncio.Lock()

    def load(self) -> None:
        import torch
        from diffusers import Flux2KleinPipeline
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is unavailable; select a Kaggle GPU accelerator")
        model_dir = Path(os.environ["HAIRCAPSTONE_MODEL_DIR"])
        adapter_dir = Path(os.environ["HAIRCAPSTONE_ADAPTER_DIR"])
        metadata = read_adapter_metadata(adapter_dir)
        if metadata["base_model_id"] != "black-forest-labs/FLUX.2-klein-base-4B":
            raise RuntimeError("Adapter does not target FLUX.2 Klein Base 4B")
        if model_dir.name != metadata["base_model_revision"]:
            raise RuntimeError("Local Base snapshot revision does not match adapter metadata")
        started = time.monotonic()
        pipe = Flux2KleinPipeline.from_pretrained(str(model_dir), torch_dtype=torch.float16, local_files_only=True)
        pipe.enable_model_cpu_offload(gpu_id=0)
        pipe.load_lora_weights(str(adapter_dir), weight_name="adapter.safetensors")
        self.pipe = pipe
        self.torch = torch
        self.metadata = metadata
        self.load_seconds = round(time.monotonic() - started, 2)
        self.ready = True
        LOGGER.info("Base plus verified TRAIN-001 adapter loaded in %.1f s", self.load_seconds)

    def generate(self, image: Image.Image, style_id: str) -> dict:
        torch = self.torch
        source = ImageOps.pad(image, (512, 512), method=Image.Resampling.LANCZOS,
                              color=(245, 245, 245), centering=(0.5, 0.5))
        torch.cuda.reset_peak_memory_stats(0)
        started = time.monotonic()
        output = self.pipe(
            prompt=REAL_STYLE_PROMPTS[style_id], image=source,
            width=512, height=512, num_inference_steps=20, guidance_scale=4.0,
            generator=torch.Generator(device="cuda").manual_seed(1977),
        ).images[0]
        buffer = BytesIO()
        output.convert("RGB").save(buffer, format="PNG")
        return {
            "status": "completed", "generator": "flux2_klein_base_train001",
            "image": {"data_url": "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii"),
                      "content_type": "image/png", "width": output.width, "height": output.height},
            "metadata": {"style_id": style_id, "base_model_id": self.metadata["base_model_id"],
                         "base_model_revision": self.metadata["base_model_revision"],
                         "adapter_experiment": "TRAIN-001", "adapter_steps": 250,
                         "adapter_sha256": self.metadata["checkpoint_sha256"],
                         "seed": 1977, "steps": 20, "guidance": 4.0,
                         "runtime_seconds": round(time.monotonic() - started, 2),
                         "peak_gpu_mib": round(torch.cuda.max_memory_allocated(0) / 1024**2, 1)},
        }


runtime = FluxRuntime()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    runtime.load()
    yield
    runtime.ready = False


app = FastAPI(title="HAIR CAPSTONE GPU inference", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    torch = runtime.torch
    return {"status": "ready" if runtime.ready else "starting", "gpu_ready": bool(torch and torch.cuda.is_available()),
            "gpu": torch.cuda.get_device_name(0) if runtime.ready else None,
            "base_model_loaded": runtime.ready, "lora_loaded": runtime.ready,
            "base_model_id": runtime.metadata.get("base_model_id"),
            "adapter_experiment": runtime.metadata.get("experiment"),
            "adapter_steps": runtime.metadata.get("training_steps"),
            "adapter_sha256": runtime.metadata.get("checkpoint_sha256"),
            "supported_styles": list(REAL_STYLE_PROMPTS)}


async def validated_image(upload: UploadFile) -> Image.Image:
    if upload.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(status_code=415, detail="Upload a JPG or PNG portrait.")
    data = await upload.read(MAX_UPLOAD_BYTES + 1)
    if not data:
        raise HTTPException(status_code=400, detail="Image is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 8 MB or smaller.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as source:
                expected = {"JPEG": "image/jpeg", "PNG": "image/png"}
                if expected.get(source.format) != upload.content_type:
                    raise HTTPException(status_code=415, detail="Image type does not match its content.")
                width, height = source.size
                if not (64 <= width <= 4096 and 64 <= height <= 4096 and width * height <= MAX_IMAGE_PIXELS):
                    raise HTTPException(status_code=422, detail="Image dimensions must be 64 to 4096 pixels and at most 16 MP.")
                source.load()
                return ImageOps.exif_transpose(source).convert("RGB")
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombWarning, Image.DecompressionBombError):
        raise HTTPException(status_code=400, detail="The uploaded image cannot be read.") from None


@app.post("/generate")
async def generate(image: Annotated[UploadFile, File()], style_id: Annotated[str, Form()],
                   x_api_key: Annotated[str | None, Header()] = None) -> dict:
    import secrets
    key = os.environ.get("HAIRCAPSTONE_API_KEY", "")
    if not key or not x_api_key or not secrets.compare_digest(x_api_key, key):
        raise HTTPException(status_code=401, detail="Invalid API key.")
    if style_id not in REAL_STYLE_PROMPTS:
        raise HTTPException(status_code=400, detail="Unsupported hairstyle ID.")
    if not runtime.ready:
        raise HTTPException(status_code=503, detail="GPU model is not ready.")
    portrait = await validated_image(image)
    if runtime.lock.locked():
        raise HTTPException(status_code=429, detail="GPU is busy. Try again after the current image finishes.")
    async with runtime.lock:
        try:
            return await asyncio.to_thread(runtime.generate, portrait, style_id)
        except Exception:
            LOGGER.exception("Inference request failed")
            raise HTTPException(status_code=500, detail="GPU inference failed. Check the Kaggle server log.") from None

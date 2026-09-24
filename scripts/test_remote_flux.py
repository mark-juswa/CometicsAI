"""Send one portrait through the active Kaggle endpoint and save its PNG."""

import argparse
import base64
from io import BytesIO
import json
import os
from pathlib import Path
import time
from urllib.parse import urlparse

import httpx
from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Cloudflare Quick Tunnel URL")
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--style", choices=("crew_cut", "bob_hair", "layered_hair"), required=True)
    parser.add_argument("--output", type=Path, default=Path("remote_flux_result.png"))
    parser.add_argument("--api-key", default=os.environ.get("FLUX_REMOTE_API_KEY"))
    args = parser.parse_args()
    parsed = urlparse(args.url)
    if not ((parsed.scheme == "https" and parsed.hostname)
            or (parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"})):
        parser.error("Use an HTTPS endpoint, or HTTP localhost inside Kaggle")
    if not args.api_key:
        parser.error("Set FLUX_REMOTE_API_KEY or --api-key")
    with httpx.Client(timeout=180, follow_redirects=False) as client:
        health = client.get(args.url.rstrip("/") + "/health")
        health.raise_for_status()
        report = health.json()
        if not (report.get("status") == "ready" and report.get("lora_loaded")):
            raise RuntimeError(f"GPU server is not ready: {report}")
        with args.image.open("rb") as image:
            started = time.monotonic()
            response = client.post(args.url.rstrip("/") + "/generate",
                                   data={"style_id": args.style},
                                   files={"image": (args.image.name, image, "image/png" if args.image.suffix.lower() == ".png" else "image/jpeg")},
                                   headers={"X-API-Key": args.api_key})
        response.raise_for_status()
    payload = response.json()
    data_url = payload["image"]["data_url"]
    if not data_url.startswith("data:image/png;base64,"):
        raise RuntimeError("GPU endpoint did not return a PNG data URL")
    content = base64.b64decode(data_url.split(",", 1)[1], validate=True)
    with Image.open(BytesIO(content)) as result:
        result.verify()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(content)
    print(json.dumps({"output": str(args.output.resolve()), "request_seconds": round(time.monotonic() - started, 2),
                      "generation": payload.get("metadata"), "health": report}, indent=2))


if __name__ == "__main__":
    main()

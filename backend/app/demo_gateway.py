"""Authenticated, bounded demo facade; existing AI handlers stay private and unchanged."""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import hmac
import json
import re
import time
from uuid import uuid4

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

MAX_UPLOAD = 8 * 1024 * 1024 + 64 * 1024
MAX_RESULT = 96 * 1024 * 1024
LIFETIME = 30 * 60
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
SAFE_ID = r"[A-Za-z0-9_-]{1,80}"
PRIVATE = {"Cache-Control": "private, no-store"}


@dataclass
class Job:
    owner: str
    created: float
    status: str = "generating"
    response: httpx.Response | None = None
    task: asyncio.Task | None = None


def create_gateway(inner, secret: str, *, max_jobs=3, clock=time.monotonic):
    if len(secret) < 32:
        raise ValueError("AI_BACKEND_API_KEY must have at least 32 characters")
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    jobs: dict[str, Job] = {}
    owners: dict[str, tuple[str, float]] = {}
    busy = False

    def error(status, message):
        return JSONResponse({"detail": message}, status_code=status, headers=PRIVATE)

    def wire(response):
        return Response(response.content, status_code=response.status_code,
                        media_type="application/json", headers=PRIVATE)

    async def invoke(method, path, body, content_type):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=inner, raise_app_exceptions=False),
                                    base_url="http://private-ai", timeout=None) as client:
            return await client.request(method, path, content=body,
                                        headers={"Content-Type": content_type})

    async def run(job, method, path, body, content_type):
        nonlocal busy
        try:
            response = await invoke(method, path, body, content_type)
            if len(response.content) > MAX_RESULT:
                response = httpx.Response(503, json={"detail": "Result exceeds demo storage capacity."})
            job.response = response
            job.status = "completed" if response.is_success else "failed"
        except Exception:
            job.response = httpx.Response(502, json={"detail": "Generation failed. Check status before retrying."})
            job.status = "failed"
        finally:
            busy = False

    @app.get("/health")
    async def health():
        # Liveness only; protected /deployment/readiness checks actual AI readiness.
        return JSONResponse({"status": "ok", "service": "render-kaggle-demo-v1"}, headers=PRIVATE)

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH"])
    async def route(path: str, request: Request):
        nonlocal busy
        if not hmac.compare_digest(request.headers.get("x-ai-backend-key", "").encode(), secret.encode()):
            return error(401, "Backend access denied.")
        owner = request.headers.get("x-ai-user-id", "")
        if not re.fullmatch(SAFE_ID, owner):
            return error(403, "Client identity required.")
        if request.url.query:
            return error(404, "Operation not found.")
        now = clock()
        for identity in list(jobs):
            if jobs[identity].status != "generating" and now - jobs[identity].created > LIFETIME:
                del jobs[identity]
        for identity in list(owners):
            if owners[identity][1] <= now:
                del owners[identity]
        job_path = re.fullmatch(rf"jobs/({UUID})(/result)?", path)
        if job_path:
            if request.method != "GET":
                return error(405, "Method not allowed.")
            identity, result = job_path.groups()
            job = jobs.get(identity)
            if job is None or job.owner != owner:
                return error(404, "Generation not found or expired.")
            if result:
                if job.response is None:
                    return error(409, "Generation is still running.")
                return wire(job.response)
            return JSONResponse({"job_id": identity, "status": job.status,
                                 "result_available": job.response is not None}, headers=PRIVATE)

        method = request.method
        allowed = (method == "GET" and path in {"features", "consultations/mode", "consultations/catalog", "deployment/readiness"}
                   or method == "GET" and re.fullmatch(r"features/(hairstyle|makeup|nails)/styles", path)
                   or method == "POST" and path == "consultations")
        manual = method == "POST" and re.fullmatch(r"features/(hairstyle|makeup|nails)/generate", path)
        consultation = re.fullmatch(rf"consultations/({UUID})(.*)", path)
        generate = bool(manual)
        if consultation:
            identity, tail = consultation.groups()
            if identity not in owners or owners[identity][0] != owner:
                return error(404, "Consultation not found or expired.")
            allowed = (tail == "" and method in {"GET", "PATCH"}
                       or tail == "/photo" and method == "PUT"
                       or tail in {"/turn", "/recommendations"} and method == "POST"
                       or re.fullmatch(rf"/recommendations/{SAFE_ID}/generation", tail) and method in {"GET", "POST"}
                       or re.fullmatch(rf"/recommendations/{SAFE_ID}/select", tail) and method == "POST")
            generate = method == "POST" and tail.endswith("/generation") and bool(allowed)
            owners[identity] = (owner, now + 3600)
        if not allowed and not manual:
            return error(404, "Operation not found.")
        if generate and busy:
            return error(429, "The demo is busy or result capacity is full. No new generation was started.")
        limit = MAX_UPLOAD if manual or path.endswith("/photo") else 32 * 1024
        content = bytearray()
        async for chunk in request.stream():
            content.extend(chunk)
            if len(content) > limit:
                return error(413, "Request is too large.")
        body = bytes(content)
        content_type = request.headers.get("content-type", "application/json")
        if generate:
            # Recheck after upload: another request may have acquired the slot.
            if busy:
                return error(429, "The demo is busy. No new generation was started.")
            while len(jobs) >= max_jobs:
                oldest = min(jobs, key=lambda key: jobs[key].created)
                del jobs[oldest]
            busy = True
            identity = str(uuid4())
            job = jobs[identity] = Job(owner, now)
            job.task = asyncio.create_task(run(job, method, "/" + path, body, content_type))
            return JSONResponse({"job_id": identity, "status": job.status, "result_available": False},
                                status_code=202, headers=PRIVATE)
        response = await invoke(method, "/" + path, body, content_type)
        if method == "POST" and path == "consultations" and response.is_success:
            data = response.json()
            expires = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
            owners[data["id"]] = (owner, now + max(0, (expires - datetime.now(timezone.utc)).total_seconds()))
        return wire(response)

    return app

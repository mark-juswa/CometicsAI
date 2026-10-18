"""Test-only loopback worker control. Never package this in the demo service."""
import hmac
import os
from fastapi import Header, HTTPException
from pydantic import BaseModel, ConfigDict
from scripts.inference_performance import InferencePerformance


class Mode(BaseModel):
    model_config = ConfigDict(extra='forbid')
    mode: str


def set_mode(owner, mode):
    if mode not in ('baseline', 'candidate'):
        raise ValueError('Unsupported comparison mode')
    if owner.owner.locked():
        raise RuntimeError('Wait for the admitted request to finish')
    owner.performance = InferencePerformance(owner.synchronize, cache_enabled=mode=='candidate', phase_timing=False)
    owner.audit.clear()
    return {'mode': mode, 'cache_cleared': True}


def create_app(server):
    app = server.app
    @app.post('/rehearsal/mode')
    async def mode(body: Mode, x_api_key: str | None = Header(default=None)):
        key = os.environ.get('AI_REMOTE_API_KEY', '')
        if len(key)<24 or not x_api_key or not hmac.compare_digest(key, x_api_key):
            raise HTTPException(401, 'Invalid API key')
        if not server.runtime.ready or not server.runtime.owner:
            raise HTTPException(503, 'Worker not ready')
        try:
            return set_mode(server.runtime.owner, body.mode)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from None
        except RuntimeError as exc:
            raise HTTPException(409, str(exc)) from None
    return app


def factory():
    # Imported only by the owned uvicorn process.
    from scripts import unified_gate3_server as server
    return create_app(server)

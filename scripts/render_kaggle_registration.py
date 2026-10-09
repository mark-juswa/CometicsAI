"""HMAC metadata registration/heartbeat. No credentials or generation requests in logs."""
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import socket
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

SCHEMA = "beautycore-runtime-v1"
HEARTBEAT_SECONDS = 60

class RegistrationError(RuntimeError):
    def __init__(self, status=None):
        self.status = status
        super().__init__("Website connection not acknowledged" + (f" (HTTP {status})" if status else ""))

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def canonical(message):
    return json.dumps(message, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()

def sign(message, key):
    derived = hmac.new(key.encode(), b"beautycore-runtime-key-v1", sha256).digest()
    return hmac.new(derived, canonical(message), sha256).hexdigest()

def website_root(website):
    p = urlsplit(website)
    if (p.scheme != "https" or not p.hostname or p.username or p.password or p.port
            or p.query or p.fragment or p.path.rstrip("/")):
        raise RegistrationError()
    return website.rstrip("/")

def send(website, record, key, operation, *, opener=None, now=time.time):
    if len(key) < 32:
        raise RegistrationError()
    message = {"schema": SCHEMA, "operation": operation, "session_id": record["session_id"],
               "endpoint": record["url"], "started_at": record["started_at"], "issued_at": int(now())}
    request = Request(website_root(website) + "/api/internal/ai-runtime/register", data=canonical(message),
                      headers={"Content-Type": "application/json", "x-ai-runtime-signature": sign(message, key)})
    try:
        with (opener or build_opener(NoRedirect())).open(request, timeout=75) as response:
            if response.status != 200:
                raise RegistrationError(response.status)
            raw = response.read(8193)
            if len(raw) > 8192:
                raise RegistrationError()
            ack = json.loads(raw)
            if (ack.get("connected") is not True or ack.get("session_id") != record["session_id"]
                    or not isinstance(ack.get("expires_at"), (int, float)) or ack["expires_at"] <= now() * 1000):
                raise RegistrationError()
            return ack
    except HTTPError as error:
        raise RegistrationError(error.code) from None
    except (URLError, OSError, TimeoutError, ValueError, TypeError, AttributeError):
        raise RegistrationError() from None

def register(website, record, key, *, send_fn=send, sleep=time.sleep, attempts=4):
    # Metadata only. The GPU request is never repeated here. Accommodates Render cold start.
    for attempt in range(attempts):
        try:
            return send_fn(website, record, key, "register")
        except RegistrationError as error:
            if error.status in (400, 401, 403, 409, 404) or attempt == attempts - 1:
                raise
            print("Website registration waiting; AI processes remain running.", flush=True)
            sleep(10)

def services_alive(record):
    try:
        for field in ("api_pid", "tunnel_pid"):
            os.kill(record[field], 0)
        for port in (8765, 8800):
            with socket.socket() as connection:
                connection.settimeout(2)
                if connection.connect_ex(("127.0.0.1", port)) != 0:
                    return False
        return True
    except (OSError, KeyError, TypeError):
        return False

def heartbeat(website, record, key, *, send_fn=send, alive=services_alive, sleep=time.sleep, now=time.time):
    acknowledged_until = record["registration_expires_at"]
    while True:
        sleep(HEARTBEAT_SECONDS)
        if not alive(record):
            print("AI process stopped. Website lease will expire; start a fresh notebook session.", flush=True)
            return
        try:
            ack = send_fn(website, record, key, "renew")
            acknowledged_until = ack["expires_at"]
        except RegistrationError as error:
            if error.status in (400, 401, 403, 409, 404) or now() * 1000 >= acknowledged_until:
                print("Website lease expired or refused. Start a fresh session; do not replay generation.", flush=True)
                return
            print("Website heartbeat not acknowledged; existing lease has not been extended.", flush=True)

if __name__ == "__main__":
    record = json.loads(Path(sys.argv[2]).read_text())
    heartbeat(sys.argv[1], record, os.environ.get("AI_BACKEND_API_KEY", ""))

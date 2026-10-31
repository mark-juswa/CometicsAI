"""Versioned expansion approval data. Frozen model metadata is never rewritten."""

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re

PATH = Path(__file__).with_suffix(".json")
SCHEMA = "beautycore-style-release-v1"
FEATURES = ("hairstyle", "makeup", "nails")
ROUTES = {"hairstyle": "hair_prompt", "makeup": "makeup_profile", "nails": "nails_renderer"}
REVIEWS = frozenset(("untested", "held", "pending_visual", "accepted"))
ID = re.compile(r"[a-z][a-z0-9_-]{0,79}\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")


def canonical_digest(value) -> str:
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                             separators=(",", ":")).encode()).hexdigest()


def profile_digest(path: Path) -> str:
    """Canonical LF source digest; archive inventories still hash exact bytes."""
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate style release field")
        value[key] = item
    return value


@dataclass(frozen=True)
class Candidate:
    feature: str
    id: str
    name: str
    description: str
    route: str
    profile_id: str | None
    profile_sha256: str | None
    review_status: str
    enabled: bool
    tags: tuple[str, ...]
    services: tuple[str, ...]
    input_constraints: tuple[str, ...]
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class StyleRelease:
    release_id: str
    manifest_sha256: str
    candidates: tuple[Candidate, ...]

    def enabled(self, feature: str | None = None) -> tuple[Candidate, ...]:
        return tuple(c for c in self.candidates if c.enabled
                     and (feature is None or c.feature == feature))


def _strings(value, field, *, required=False, limit=240):
    if (not isinstance(value, list) or len(value) > 30
            or any(not isinstance(s, str) or not s.strip() or len(s) > limit for s in value)
            or len(value) != len(set(value)) or required and not value):
        raise ValueError("Invalid style release " + field)
    return tuple(value)


def parse_release(value) -> StyleRelease:
    if (not isinstance(value, dict) or set(value) != {"schema", "release_id", "candidates"}
            or value["schema"] != SCHEMA or not isinstance(value["release_id"], str)
            or not ID.fullmatch(value["release_id"]) or not isinstance(value["candidates"], list)
            or len(value["candidates"]) > 100):
        raise ValueError("Invalid style release header")
    fields = set(Candidate.__dataclass_fields__)
    found = []
    seen = set()
    for row in value["candidates"]:
        if not isinstance(row, dict) or set(row) != fields:
            raise ValueError("Invalid style release candidate fields")
        if (not isinstance(row["feature"], str) or row["feature"] not in FEATURES or not isinstance(row["id"], str)
                or not ID.fullmatch(row["id"]) or not row["id"].startswith("exp_") or row["id"] in seen
                or row["route"] != ROUTES[row["feature"]]
                or not isinstance(row["review_status"], str) or row["review_status"] not in REVIEWS
                or type(row["enabled"]) is not bool):
            raise ValueError("Invalid style release identity, route or review")
        for key, limit in (("name", 255), ("description", 240)):
            if not isinstance(row[key], str) or not row[key].strip() or len(row[key]) > limit:
                raise ValueError("Invalid style release " + key)
        profile, digest = row["profile_id"], row["profile_sha256"]
        if ((profile is None) != (digest is None)
                or profile is not None and (not isinstance(profile, str) or not ID.fullmatch(profile))
                or digest is not None and (not isinstance(digest, str) or not HASH.fullmatch(digest))):
            raise ValueError("Invalid style release profile")
        lists = {key: _strings(row[key], key, required=key in ("tags", "services"),
                               limit=500 if key == "evidence" else 240)
                 for key in ("tags", "services", "input_constraints", "evidence")}
        if row["enabled"] and (row["review_status"] != "accepted"
                               or profile is None or not lists["evidence"]):
            raise ValueError("Enabled style requires an accepted reviewed execution profile")
        found.append(Candidate(**{**row, **lists}))
        seen.add(row["id"])
    return StyleRelease(value["release_id"], canonical_digest(value), tuple(found))


def load_release(path: Path = PATH) -> StyleRelease:
    if path.stat().st_size > 65536:
        raise ValueError("Style release exceeds size limit")
    return parse_release(json.loads(path.read_text(encoding="utf-8"),
                                    object_pairs_hook=_unique_object))


RELEASE = load_release()

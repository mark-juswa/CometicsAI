"""Approved Hair inference profiles; frozen training registries stay intact."""
import json
from pathlib import Path
from app.style_release import profile_digest

PATH = Path(__file__).with_name("hair_profile.json")
PROFILE = json.loads(PATH.read_text(encoding="utf-8"))
STYLE_ID = "exp_french_bob_wispy"
PROFILE_ID = "hair-french-bob-v1"
WORKER_SCHEMA = "beautycore-worker-style-capabilities-v1"
EXTRA = {
    "exp_butterfly_cut": ("hair-butterfly-cut-v1", "train001"),
    "exp_wolf_cut": ("hair-wolf-cut-v1", "train002"),
    "exp_korean_two_block": ("hair-korean-two-block-v1", "train002"),
    "exp_comma_hair": ("hair-comma-hair-v1", "train002"),
}
STYLE_IDS = frozenset({STYLE_ID, *EXTRA})
ADAPTER_HASHES = {
    "train001": "7e3991f8a4e502573d3e82e9ac34c89fdf3f0b66fb337abb026a5b4c9ad080ff",
    "train002": "59d527217a68139bc2aaa4eedbfcd2d5789ef115f8ecb924410eea24a952939b",
}


def profile(release=None, registry=None, style_id=STYLE_ID):
    from app.style_release import RELEASE
    from app.styles import REGISTRY
    release = RELEASE if release is None else release
    registry = REGISTRY if registry is None else registry
    c = next((c for c in release.candidates if c.id == style_id), None)
    if c is None or c.profile_id is None:
        return None
    if style_id == STYLE_ID:
        path, p, profile_id, adapter_id = PATH, PROFILE, PROFILE_ID, "train001"
    elif style_id in EXTRA:
        profile_id, adapter_id = EXTRA[style_id]
        path = Path(__file__).with_name("hair_profile_" + style_id.removeprefix("exp_") + ".json")
        p = json.loads(path.read_text(encoding="utf-8"))
    else:
        raise ValueError("Style has no matching installed Hair execution profile: " + style_id)
    if (c.feature != "hairstyle" or c.route != "hair_prompt" or c.profile_id != profile_id
            or c.profile_sha256 != profile_digest(path)
            or set(p) != {"schema", "profile_id", "style_id", "adapter_id", "adapter_sha256",
                         "base_model_revision", "prompt", "settings", "limitations", "validation"}
            or p["schema"] != "beautycore-hair-profile-v1" or p["profile_id"] != profile_id
            or p["style_id"] != style_id or p["adapter_id"] != adapter_id
            or p["adapter_sha256"] != ADAPTER_HASHES[adapter_id]
            or p["settings"] != {"width": 512, "height": 512, "steps": 20, "guidance": 4.0,
                                "seed": 1977, "adapter_weight": 1.0}
            or not isinstance(p["prompt"], str) or not 20 <= len(p["prompt"]) <= 2000
            or registry["base_model_revision"] != p["base_model_revision"]
            or any(s["style_id"] == style_id for s in registry["styles"])):
        raise ValueError("Approved Hair inference profile differs from its release/artifact")
    # A registry without TRAIN-002 must never advertise its additional styles.
    info = registry["adapters"].get(adapter_id)
    if info is None or info["status"] != "enabled":
        return None
    if info["checkpoint_sha256"] != p["adapter_sha256"]:
        raise ValueError("Approved Hair inference profile differs from its release/artifact")
    return c, p


def hair_candidates(release=None, registry=None):
    from app.style_release import RELEASE
    release = RELEASE if release is None else release
    result = []
    for c in release.candidates:
        if c.feature != "hairstyle" or c.profile_id is None:
            continue
        if c.id not in STYLE_IDS:
            raise ValueError("Style has no matching installed Hair execution profile: " + c.id)
        verified = profile(release, registry, c.id)
        if verified is not None and verified[0].enabled:
            result.append(verified[0])
    return tuple(result)


def active_hair_styles(release=None):
    from app.styles import REAL_STYLES, Style
    return REAL_STYLES + tuple(Style(c.id, c.name, c.description, "available") for c in hair_candidates(release))


def active_hair_style_by_id(release=None):
    return {s.id: s for s in active_hair_styles(release)}


def model_profile(release=None):
    additions = hair_candidates(release)
    if any(c.id != STYLE_ID for c in additions):
        return "hair-expanded-v1"
    return PROFILE_ID if additions else "legacy-baseline"


def expected_contract(style_id, metadata=None):
    from hashlib import sha256
    from app.style_release import RELEASE
    from app.styles import REGISTRY
    if style_id not in {c.id for c in hair_candidates()}:
        raise ValueError("Additional Hair style is not approved/enabled")
    c, p = profile(style_id=style_id)
    info = REGISTRY["adapters"][p["adapter_id"]]
    if metadata is not None and (
            metadata.get("checkpoint_sha256") != p["adapter_sha256"]
            or metadata.get("training_steps") != info["training_steps"]
            or metadata.get("base_model_revision") != p["base_model_revision"]
            or metadata.get("base_model_id") != REGISTRY["base_model_id"]
            or style_id in metadata.get("supported_style_ids", [])):
        raise ValueError("Hair artifact metadata or original training claims differ")
    return {
        "feature": "hairstyle", "style_id": style_id,
        "adapter_id": p["adapter_id"], "adapter_sha256": p["adapter_sha256"],
        "adapter_steps": info["training_steps"], "base_model_id": REGISTRY["base_model_id"],
        "base_model_revision": p["base_model_revision"],
        "generator": "flux2_klein_base_" + p["adapter_id"] + "_profile", "prompt": p["prompt"],
        "execution_profile": c.profile_id, "execution_profile_sha256": c.profile_sha256,
        "prompt_sha256": sha256(p["prompt"].encode()).hexdigest(),
        "style_release_id": RELEASE.release_id, "style_manifest_sha256": RELEASE.manifest_sha256,
        "trained_style": False, "seed": 1977, "steps": 20, "guidance": 4.0,
    }


def validate_remote_result(payload, style_id):
    expected = expected_contract(style_id)
    metadata = payload.get("metadata")
    image = payload.get("image", {})
    if (not isinstance(image, dict) or image.get("width") != 512 or image.get("height") != 512
            or image.get("content_type") != "image/png"):
        raise ValueError("Additional Hair response has wrong image dimensions/type")
    if (not isinstance(metadata, dict) or payload.get("status") != "completed"
            or payload.get("generator") != expected["generator"]
            or metadata.get("trained_style") is not False
            or any(metadata.get(k) != v for k, v in expected.items() if k not in {"generator", "prompt"})
            or "prompt" in metadata and metadata["prompt"] != expected["prompt"]):
        raise ValueError("Additional Hair response has wrong profile/artifact provenance")


def worker_capabilities(model_styles, release=None):
    from app.style_release import RELEASE
    release = RELEASE if release is None else release
    additions = hair_candidates(release)
    return {"schema": WORKER_SCHEMA, "release_id": release.release_id,
            "manifest_sha256": release.manifest_sha256, "model_profile": model_profile(release),
            "model_styles": model_styles,
            "profile_sha256": {c.profile_id: c.profile_sha256 for c in additions}}

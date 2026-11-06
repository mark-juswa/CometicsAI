"""Verified installed release capabilities for renderer and additional Hair profiles."""
from pathlib import Path
from app.style_release import RELEASE, StyleRelease, profile_digest
from app.nails.expanded import PROFILE_ID, STYLE_IDS

CAPABILITY_SCHEMA = "beautycore-style-capabilities-v1"
EXPANDED_SOURCE = Path(__file__).with_name("nails") / "expanded.py"


def installed_candidates(release: StyleRelease = RELEASE):
    from app.hair_profiles import hair_candidates
    hair = hair_candidates(release)
    result = []
    for candidate in release.candidates:
        if candidate.profile_id is None or candidate.feature == "hairstyle":
            continue
        if candidate.feature == "makeup":
            from app import makeup_contract
            expected_ids = {"exp_cloud_berry_lips", "exp_manga_lash", "exp_icy_silver"}
            if (candidate.route != "makeup_profile" or candidate.id not in expected_ids
                    or candidate.profile_id != "makeup-corrective001-v1"
                    or candidate.profile_sha256 != profile_digest(Path(makeup_contract.__file__))
                    or makeup_contract.ADAPTER_SHA256 != "991a1037cc892c1a62e1a731be577ed1aec2f331d9568b4586ff3829a4ee32c3"
                    or candidate.id not in makeup_contract.PROMPTS):
                raise ValueError("Makeup release differs from the reviewed execution contract")
            if candidate.enabled:
                result.append(candidate)
            continue
        if (candidate.feature != "nails" or candidate.route != "nails_renderer"
                or candidate.id not in STYLE_IDS or candidate.profile_id != PROFILE_ID):
            raise ValueError("Style has no matching installed execution profile: " + candidate.id)
        try:
            digest = profile_digest(EXPANDED_SOURCE)
        except OSError as exc:
            raise ValueError("Renderer profile source is unavailable") from exc
        if candidate.profile_sha256 != digest:
            raise ValueError("Renderer execution profile hash differs: " + candidate.id)
        if candidate.enabled:
            result.append(candidate)
    return tuple(result) + hair


def baseline_model_styles():
    from app.styles import REAL_STYLE_BY_ID
    from app.makeup_contract import PROMPTS
    from app.nails.contract import MODEL_STYLES
    return {"hairstyle": sorted(REAL_STYLE_BY_ID), "makeup": sorted(PROMPTS),
            "nails": sorted(MODEL_STYLES)}


def model_styles(release=RELEASE):
    from app.hair_profiles import hair_candidates
    result = baseline_model_styles()
    if not release.enabled("makeup"):
        result["makeup"] = [sid for sid in result["makeup"] if not sid.startswith("exp_")]

    result["hairstyle"] = sorted(result["hairstyle"] + [c.id for c in hair_candidates(release)])
    return result


def style_capabilities(release: StyleRelease = RELEASE):
    from app.nails.styles import active_nail_styles
    from app.nails.contract import MODEL_STYLES
    from app.hair_profiles import model_profile
    installed_candidates(release)
    return {
        "schema": CAPABILITY_SCHEMA, "release_id": release.release_id,
        "manifest_sha256": release.manifest_sha256,
        "model_styles": model_styles(release),
        "renderer_styles": sorted(s.id for s in active_nail_styles(release) if s.id not in MODEL_STYLES),
        "model_profile": model_profile(release),
    }


def checked_capabilities(worker_health, worker_status, release=RELEASE):
    """An enabled model extension requires matching advertisements in both reports."""
    from app.hair_profiles import hair_candidates, worker_capabilities
    expected = style_capabilities(release)
    has_extension = bool(hair_candidates(release))
    if ("style_capabilities" in worker_health) != ("style_capabilities" in worker_status):
        raise ValueError("Worker capability advertisements are inconsistent")
    required = worker_capabilities(expected["model_styles"], release)
    for report in (worker_health, worker_status):
        if has_extension:
            if report.get("style_capabilities") != required:
                raise ValueError("Worker and facade model capabilities differ")
        elif "style_capabilities" in report:
            advertised = report["style_capabilities"]
            if (not isinstance(advertised, dict)
                    or advertised.get("model_profile") != expected["model_profile"]
                    or advertised.get("model_styles") != expected["model_styles"]):
                raise ValueError("Worker and facade model capabilities differ")
    return expected

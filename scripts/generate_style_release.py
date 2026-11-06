"""Generate/check Render release evidence and accepted business catalog additions.

No model loading, credentials, training or cloud access. Baseline descriptions
and service mappings remain in their existing business catalog.
"""

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.style_release import RELEASE, FEATURES, load_release
from app.style_capabilities import installed_candidates, style_capabilities

BUSINESS = ROOT / "beautycore/lib/business/style-catalog.json"
GENERATED = ROOT / "beautycore/lib/ai/style-release.json"


def model_catalogs(release=None):
    from app.makeup_contract import PROMPTS
    from app.nails.contract import MODEL_STYLES

    results = []
    for filename in ("style_registry.json", "style_registry_train002_smoke.json"):
        registry = json.loads((ROOT / "backend/app" / filename).read_text(encoding="utf-8"))
        catalog = {
            "hairstyle": sorted(s["style_id"] for s in registry["styles"]
                                if s["support_status"] != "disabled"
                                and registry["adapters"][s["adapter_id"]]["status"] == "enabled"),
            "makeup": sorted(PROMPTS) if release is not None and release.enabled("makeup") else sorted(s for s in PROMPTS if not s.startswith("exp_")),
            "nails": sorted(MODEL_STYLES),
        }
        if release is not None:
            from app.hair_profiles import hair_candidates
            catalog["hairstyle"] = sorted(catalog["hairstyle"] + [c.id for c in hair_candidates(release, registry)])
        if catalog not in results:
            results.append(catalog)
    return results


def outputs(business, release=RELEASE):
    installed_candidates(release)
    result = deepcopy(business)
    if set(result) != set(FEATURES):
        raise ValueError("Invalid business feature catalog")
    # Pending definitions never leak into public business/save metadata.
    for candidate in release.candidates:
        result[candidate.feature].pop(candidate.id, None)
    # Accepted metadata outlives generation availability and existing bookings.
    for candidate in release.candidates:
        if candidate.review_status != "accepted":
            continue
        result[candidate.feature][candidate.id] = {
            "name": candidate.name, "description": candidate.description,
            "services": list(candidate.services),
        }
    capabilities = style_capabilities(release)
    expected = {
        "schema": capabilities["schema"],
        "release_id": capabilities["release_id"],
        "manifest_sha256": capabilities["manifest_sha256"],
        "baseline_model_catalogs": model_catalogs(release),
        "renderer_styles": capabilities["renderer_styles"],
        "model_profile": capabilities["model_profile"],
    }
    expected["compatible_releases"] = []
    for path in sorted((ROOT / "backend/app/style_releases").glob("*.json")):
        historical = load_release(path)
        if historical.release_id == release.release_id:
            continue
        capability = style_capabilities(historical)
        expected["compatible_releases"].append({
            "schema": capability["schema"], "release_id": capability["release_id"],
            "manifest_sha256": capability["manifest_sha256"],
            "baseline_model_catalogs": model_catalogs(historical),
            "renderer_styles": capability["renderer_styles"], "model_profile": capability["model_profile"],
        })
    return result, expected


def encoded(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write generated release files.")
    args = parser.parse_args()
    current = json.loads(BUSINESS.read_text(encoding="utf-8"))
    business, expected = outputs(current)
    if args.write:
        # JSON-equivalent baseline formatting need not churn.
        if business != current:
            BUSINESS.write_bytes(encoded(business).encode())
        GENERATED.write_bytes(encoded(expected).encode())
    if current != business and not args.write:
        raise SystemExit("Business style additions differ; regenerate the reviewed release.")
    if not GENERATED.is_file() or json.loads(GENERATED.read_text(encoding="utf-8")) != expected:
        raise SystemExit("Render style release differs; run generate_style_release.py --write.")
    print("Release manifest, installed profiles and generated Render evidence agree; "
          + str(len(RELEASE.enabled())) + " expanded styles enabled.")


if __name__ == "__main__":
    main()

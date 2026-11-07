"""Mandatory corrective Makeup target review, shared by CPU and Kaggle gates.

This validates review provenance and refusal rules, not image realism by score.
No automatic ACCEPT, generated labels or production integration is provided.
"""
from hashlib import sha256
import json
from pathlib import Path

POLICY_SHA256 = "451b341d8210cfa543db82c058dfdc773202efea1cc63fb2c7f4ad711accba45"
CRITERIA = ("identity_geometry", "complexion_undertone", "texture_shading",
            "cosmetic_placement_blending", "visible_style_fidelity", "protected_content",
            "provenance_rights", "truthful_annotations")
ANNOTATIONS = ("eyes", "lips", "blush", "complexion_finish", "brows", "contour_highlight")
BINDINGS = ("pair_id", "identity_id", "split", "source_sha256", "target_sha256", "caption")


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def policy_path():
    # Bundles carry this file beside the standalone validator and training runner.
    beside = Path(__file__).with_name("makeup_target_policy.json")
    return beside if beside.is_file() else Path(__file__).resolve().parents[1] / "data/makeup/MAKEUP-CORRECTION-001/quality-policy.json"


def policy():
    path = policy_path()
    if digest(path) != POLICY_SHA256:
        raise ValueError("Corrective target policy hash mismatch")
    return json.loads(path.read_text(encoding="utf-8"))


def text(value):
    return isinstance(value, str) and bool(value.strip())


def quality_review_template(rows):
    """Prepare review work, never infer acceptance from an image or old approval."""
    rejected = set(policy()["rejected_target_sha256"])
    return {"schema": "makeup-target-quality-v1", "policy_sha256": POLICY_SHA256,
            "pairs": [{**{key: row[key] for key in BINDINGS},
                       "decision": "PENDING", "human_approved": False,
                       "reviewer": "", "evidence": "",
                       "historical_target_rejected": row["target_sha256"] in rejected,
                       "criteria": {key: {"verdict": "UNKNOWN", "note": ""} for key in CRITERIA},
                       "source_cosmetics": {key: "" for key in ANNOTATIONS},
                       "target_cosmetics": {key: "" for key in ANNOTATIONS}}
                      for row in rows]}


def validate_quality(rows, review, root):
    """Bind every ACCEPT to real images and individual qualitative criteria.

    Review is a human attestation. It cannot prove the reviewer's identity or
    replace native resolution visual assessment and a separate acceptance set.
    """
    from PIL import Image

    root = Path(root).resolve()
    rules = policy()
    if (review.get("schema") != "makeup-target-quality-v1"
            or review.get("policy_sha256") != POLICY_SHA256):
        raise ValueError("Corrective target quality review schema or policy mismatch")
    ids = [row["pair_id"] for row in rows]
    decisions = review.get("pairs", [])
    if (not ids or len(set(ids)) != len(ids) or len(decisions) != len(ids)
            or len({row["pair_id"] for row in decisions}) != len(decisions)
            or {row["pair_id"] for row in decisions} != set(ids)):
        raise ValueError("Exactly one corrective quality review per included pair is required")
    by_id = {row["pair_id"]: row for row in decisions}
    groups, source_splits, targets = {}, {}, set()
    for row in rows:
        checked = by_id[row["pair_id"]]
        if any(checked.get(key) != row.get(key) for key in BINDINGS):
            raise ValueError("Corrective review image, caption or identity binding mismatch")
        if row["split"] not in {"train", "validation"}:
            raise ValueError("Invalid identity split")
        groups.setdefault(row["identity_id"], set()).add(row["split"])
        source_splits.setdefault(row["source_sha256"], set()).add(row["split"])
        if row["target_sha256"] in rules["rejected_target_sha256"]:
            raise ValueError("Rejected historical Makeup target cannot enter corrective training")
        if row["target_sha256"] in targets:
            raise ValueError("Duplicate corrective target")
        targets.add(row["target_sha256"])
        for fields, hash_key in ((("reference", "source_path"), "source_sha256"),
                                 (("target", "target_path"), "target_sha256")):
            relative = next((row[key] for key in fields if key in row), None)
            if not isinstance(relative, str):
                raise ValueError("Missing corrective image path")
            path = (root / relative).resolve()
            if not path.is_relative_to(root) or not path.is_file() or digest(path) != row[hash_key]:
                raise ValueError("Corrective image path or hash mismatch")
            with Image.open(path) as image:
                if image.mode != "RGB" or image.size != (512, 512):
                    raise ValueError("Corrective image must be original size RGB512")
                if hash_key == "target_sha256" and sha256(image.tobytes()).hexdigest() in rules["rejected_target_rgb_sha256"]:
                    raise ValueError("Reencoded rejected historical Makeup target")
        if (checked.get("decision") != "ACCEPT" or checked.get("human_approved") is not True
                or not text(checked.get("reviewer")) or not text(checked.get("evidence"))):
            raise ValueError("Explicit human corrective target acceptance required")
        criteria = checked.get("criteria", {})
        if not isinstance(criteria, dict) or set(criteria) != set(CRITERIA) or any(
                not isinstance(criteria[key], dict) or criteria[key].get("verdict") != "PASS" or not text(criteria[key].get("note"))
                for key in CRITERIA):
            raise ValueError("Every preservation AND visible makeup quality criterion must pass")
        for name in ("source_cosmetics", "target_cosmetics"):
            annotations = checked.get(name, {})
            if set(annotations) != set(ANNOTATIONS) or not all(text(value) for value in annotations.values()):
                raise ValueError("Truthful source and target cosmetic annotations required")
        if row.get("target_variant_is_style_class") is not False:
            raise ValueError("Archive positions must not become style labels")
        credit = row.get("source_photo", {})
        if (not isinstance(credit, dict) or not all(text(credit.get(key))
                for key in ("author", "photo_url", "license", "license_url"))
                or not text(row.get("source_dataset_license"))):
            raise ValueError("Retain original photo credit and dataset terms")
    if any(len(value) != 1 for value in [*groups.values(), *source_splits.values()]):
        raise ValueError("Corrective train/validation identity or source leakage")
    return {"corrective_quality": "VERIFIED_REVIEW_RECORDS",
            "policy_sha256": POLICY_SHA256, "review_sha256": sha256(
                json.dumps(review, sort_keys=True).encode()).hexdigest(),
            "reviewed_pairs": len(rows), "appearance_is_human_attestation": True,
            "previously_used_validation_ids": sorted({row["identity_id"] for row in rows
                if row["split"] == "validation" and row["identity_id"] in rules["development_identity_ids"]})}


def validate_dataset_quality(dataset):
    dataset = Path(dataset)
    review_path = dataset / "reports/target_quality.json"
    if not review_path.is_file():
        raise ValueError("Corrective target quality review missing, historical FINALIZED is insufficient")
    rows = json.loads((dataset / "manifests/pairs.json").read_text(encoding="utf-8"))
    qa = json.loads((dataset / "reports/qa.json").read_text(encoding="utf-8"))
    if (qa.get("status") != "FINALIZED" or any(
            sum(row["split"] == split for row in rows) != qa.get(split + "_pairs")
            for split in ("train", "validation"))):
        raise ValueError("Corrective manifest and final QA counts differ")
    review = json.loads(review_path.read_text(encoding="utf-8"))
    return validate_quality(rows, review, dataset)

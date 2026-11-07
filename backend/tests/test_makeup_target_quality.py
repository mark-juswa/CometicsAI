"""Corrective training must refuse historical or unreviewed data before GPU work."""
import copy
from hashlib import sha256
import json
from pathlib import Path
import sys

from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from makeup_target_quality import validate_quality, validate_dataset_quality, policy, POLICY_SHA256, CRITERIA, ANNOTATIONS, BINDINGS
from data_m001_package_training import package


@pytest.fixture
def reviewed_pair(tmp_path):
    for name, color in [("source.jpg", (80, 60, 50)), ("target.jpg", (85, 58, 55))]:
        Image.new("RGB", (512, 512), color).save(tmp_path / name)
    row = {"pair_id": "test-only", "identity_id": "fixture", "split": "train",
           "source_path": "source.jpg", "target_path": "target.jpg", "caption": "test fixture",
           "source_sha256": sha256((tmp_path / "source.jpg").read_bytes()).hexdigest(),
           "target_sha256": sha256((tmp_path / "target.jpg").read_bytes()).hexdigest(),
           "target_variant_is_style_class": False, "source_photo": {"author": "fixture",
               "photo_url": "https://example.org/fixture", "license": "Synthetic fixture",
               "license_url": "https://example.org/fixture/terms"},
           "source_dataset_license": "Synthetic fixture only"}
    review = {"schema": "makeup-target-quality-v1", "policy_sha256": POLICY_SHA256,
              "pairs": [{**{key: row[key] for key in BINDINGS}, "decision": "ACCEPT",
                         "human_approved": True, "reviewer": "Synthetic test reviewer",
                         "evidence": "Synthetic fixture only",
                         "criteria": {key: {"verdict": "PASS", "note": "Synthetic fixture only"}
                                      for key in CRITERIA},
                         "source_cosmetics": {key: "Synthetic fixture only" for key in ANNOTATIONS},
                         "target_cosmetics": {key: "Synthetic fixture only" for key in ANNOTATIONS}}]}
    return [row], review, tmp_path


def test_individually_bound_review_allows_a_new_nonrejected_fixture(reviewed_pair):
    evidence = validate_quality(*reviewed_pair)
    assert evidence["reviewed_pairs"] == 1
    assert evidence["appearance_is_human_attestation"] is True


@pytest.mark.parametrize("failure", ["hash", "caption", "split", "reviewer", "human", "criterion", "annotations", "duplicate"])
def test_missing_or_stale_criteria_never_become_acceptance(reviewed_pair, failure):
    rows, review, root = reviewed_pair
    checked = review["pairs"][0]
    if failure == "hash": checked["target_sha256"] = "0" * 64
    elif failure == "caption": rows[0]["caption"] = "invented replacement caption"
    elif failure == "split": checked["split"] = "validation"
    elif failure == "reviewer": checked["reviewer"] = " "
    elif failure == "human": checked["human_approved"] = "true"
    elif failure == "criterion": checked["criteria"]["visible_style_fidelity"]["verdict"] = "UNKNOWN"
    elif failure == "annotations": del checked["source_cosmetics"]["lips"]
    elif failure == "duplicate": review["pairs"].append(copy.deepcopy(checked))
    with pytest.raises(ValueError):
        validate_quality(rows, review, root)


def test_path_escape_is_refused_even_with_matching_hash(reviewed_pair):
    rows, review, root = reviewed_pair
    rows[0]["source_path"] = "../outside.jpg"
    (root.parent / "outside.jpg").write_bytes((root / "source.jpg").read_bytes())
    with pytest.raises(ValueError, match="path or hash"):
        validate_quality(rows, review, root)


def test_rejected_hash_cannot_be_overridden_by_new_accept_text(reviewed_pair):
    rows, review, root = reviewed_pair
    rejected = policy()["rejected_target_sha256"][0]
    rows[0]["target_sha256"] = review["pairs"][0]["target_sha256"] = rejected
    with pytest.raises(ValueError, match="Rejected historical"):
        validate_quality(rows, review, root)


def test_reencoded_rejected_target_still_cannot_enter_training(reviewed_pair):
    rows, review, root = reviewed_pair
    dataset = ROOT / ".tmp/data_m001/paired_selection/final_v1"
    if not dataset.exists():
        pytest.skip("Private historical dataset unavailable")
    original = json.loads((dataset / "manifests/pairs.json").read_text(encoding="utf-8"))[0]
    with Image.open(dataset / original["target"]) as image:
        image.save(root / "target.png")
    rows[0]["target_path"] = "target.png"
    checksum = sha256((root / "target.png").read_bytes()).hexdigest()
    assert checksum not in policy()["rejected_target_sha256"]
    rows[0]["target_sha256"] = review["pairs"][0]["target_sha256"] = checksum
    with pytest.raises(ValueError, match="Reencoded rejected"):
        validate_quality(rows, review, root)


def test_all_actual_historical_targets_are_excluded_and_old_package_is_refused(tmp_path):
    ledger = json.loads((ROOT / "data/makeup/MAKEUP-CORRECTION-001/review.json").read_text())
    rules = policy()
    assert len(rules["rejected_target_sha256"]) == 60
    assert all(row["target_sha256"] in rules["rejected_target_sha256"] for row in ledger["pairs"])
    dataset = ROOT / ".tmp/data_m001/paired_selection/final_v1"
    if not dataset.exists():
        pytest.skip("Private historical dataset unavailable")
    with pytest.raises(ValueError, match="quality review missing"):
        validate_dataset_quality(dataset)
    bundle = tmp_path / "must-not-exist.zip"
    with pytest.raises(ValueError, match="quality review missing"):
        package(dataset, ROOT / "notebooks/train_m001_kaggle.py",
                ROOT / "data/makeup/DATA-M001-paired/inference_presets.json", bundle)
    assert not bundle.exists()


def test_real_historical_data_cannot_reach_gpu_preflight(tmp_path, monkeypatch):
    sys.path.insert(0, str(ROOT / "notebooks"))
    import train_m001_kaggle as trainer
    dataset = ROOT / ".tmp/data_m001/paired_selection/final_v1"
    if not dataset.exists():
        pytest.skip("Private historical dataset unavailable")
    def forbidden_preflight(*args):
        pytest.fail("Rejected data reached GPU preflight")
    monkeypatch.setattr(trainer, "preflight", forbidden_preflight)
    output = tmp_path / "not-started"
    with pytest.raises(ValueError, match="quality review missing"):
        trainer.prepare(dataset, output)
    with pytest.raises(ValueError, match="quality review missing"):
        trainer.execute(dataset, output, tmp_path / "toolkit")
    assert not output.exists()

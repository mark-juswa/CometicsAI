"""Review evidence integrity gates; synthetic fixtures, no inference."""
from copy import deepcopy
import json
from pathlib import Path
import sys

from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts import makeup_corrective_review as audit


@pytest.fixture
def frozen(tmp_path):
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    source, target = dataset / "source.jpg", dataset / "target.jpg"
    Image.new("RGB", (512, 512), (70, 60, 50)).save(source)
    Image.new("RGB", (512, 512), (90, 65, 55)).save(target)
    caption = dataset / "caption.txt"
    caption.write_text("Visible makeup.")
    rows = []
    for subject in range(12):
        for variant in range(5):
            rows.append({
                "pair_id": f"{subject:06}_makeup_{variant+1:02}",
                "identity_id": f"{subject:06}",
                "split": "train" if subject < 10 else "validation",
                "reference": source.name, "target": target.name,
                "source_sha256": audit.digest(source),
                "target_sha256": audit.digest(target),
                "caption_path": caption.name, "caption": "Visible makeup.",
                "source_photo": {"author": "Synthetic fixture", "license": "Test only"}
            })
    manifest = dataset / "manifests/pairs.json"
    manifest.parent.mkdir()
    manifest.write_text(json.dumps(rows))
    review = {
        "source_manifest_sha256": audit.digest(manifest),
        "training_allowed": False,
        "pairs": [dict(row, decision="REJECT", reason="Synthetic test observation.",
                       reviewer="Synthetic test reviewer", human_approval="PENDING",
                       eligible_for_training=False) for row in rows]
    }
    return dataset, rows, review


def test_complete_provenance_and_counts(frozen):
    dataset, _, review = frozen
    result = audit.validate_review(review, dataset)
    assert result == {
        "decisions": {"REJECT": 60},
        "by_split": {"train": {"REJECT": 50}, "validation": {"REJECT": 10}},
        "training_allowed": False,
    }


@pytest.mark.parametrize("mutation", [
    "omit", "duplicate", "reorder", "split", "hash", "approve",
    "eligible", "train", "manifest", "empty_reason", "invalid_decision", "license"
])
def test_modified_or_fabricated_ledger_rejected(frozen, mutation):
    dataset, _, original = frozen
    review = deepcopy(original)
    row = review["pairs"][0]
    if mutation == "omit": review["pairs"].pop()
    elif mutation == "duplicate": review["pairs"][-1] = deepcopy(row)
    elif mutation == "reorder": review["pairs"].reverse()
    elif mutation == "split": row["split"] = "validation"
    elif mutation == "hash": row["target_sha256"] = "0" * 64
    elif mutation == "approve": row["human_approval"] = "ACCEPT"
    elif mutation == "eligible": row["eligible_for_training"] = True
    elif mutation == "train": review["training_allowed"] = True
    elif mutation == "manifest": review["source_manifest_sha256"] = "0" * 64
    elif mutation == "empty_reason": row["reason"] = ""
    elif mutation == "invalid_decision": row["decision"] = "PASS"
    elif mutation == "license": row["source_photo"]["license"] = "Unrestricted"
    with pytest.raises(ValueError):
        audit.validate_review(review, dataset)


@pytest.mark.parametrize("mutation", ["image", "caption", "escape", "leak"])
def test_changed_source_evidence_rejected(frozen, mutation):
    dataset, rows, _ = frozen
    if mutation == "image": (dataset / "source.jpg").write_bytes(b"changed")
    elif mutation == "caption": (dataset / "caption.txt").write_text("Different.")
    elif mutation == "escape":
        outside = dataset.parent / "outside.jpg"
        outside.write_bytes((dataset / "source.jpg").read_bytes())
        rows[0]["reference"] = "../outside.jpg"
    elif mutation == "leak": rows[0]["split"] = "validation"
    (dataset / "manifests/pairs.json").write_text(json.dumps(rows))
    with pytest.raises(ValueError):
        audit.verified_pairs(dataset)


def test_sheets_never_overwrite_evidence(frozen, tmp_path):
    dataset, _, _ = frozen
    output = tmp_path / "review"
    report = audit.prepare(dataset, output)
    assert len(report["pairs"]) == 60 and len(report["sheets"]) == 12
    assert report["training_allowed"] is False
    assert report["originals_modified"] is False
    before = audit.digest(output / "inventory.json")
    with pytest.raises(ValueError, match="New review folder"):
        audit.prepare(dataset, output)
    assert audit.digest(output / "inventory.json") == before

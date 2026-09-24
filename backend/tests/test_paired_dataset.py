"""Synthetic file-contract checks; no hairstyle generation or training."""

import hashlib
import json
from pathlib import Path
import sys

from PIL import Image
import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.paired_dataset import finalize, instruction, load_manifest, plan  # noqa: E402


def fixture_manifest():
    return {"schema_version": 1, "dataset_id": "DATA-002", "source_revision": "pinned",
            "base_model_id": "base", "base_model_revision": "pinned-base",
            "generation": {"method": "v1_global", "seed": 1977, "steps": 20, "guidance": 4.0},
            "styles": {"a": {"training_label": "A", "prompt_phrase": "style A"},
                       "b": {"training_label": "B", "prompt_phrase": "style B"}},
            "samples": [
                {"sample_id": "a1", "identity_group_id": "a1", "source_style": "a", "target_style": "b",
                 "source_member": "image/A/1.jpg", "source_path": "archive!image/A/1.jpg",
                 "source_filename": "1.jpg", "source_sha256": "a" * 64,
                 "status": "selected", "split": "train"},
                {"sample_id": "b1", "identity_group_id": "b1", "source_style": "b", "target_style": "a",
                 "source_member": "image/B/1.jpg", "source_path": "archive!image/B/1.jpg",
                 "source_filename": "1.jpg", "source_sha256": "b" * 64,
                 "status": "selected", "split": "val"}]}


def test_manifest_plan_calculates_counts_and_rejects_imbalance(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(fixture_manifest()), encoding="utf-8")
    manifest = load_manifest(manifest_path)
    assert plan(manifest)["pair_counts"] == {"train": 2, "val": 2}
    assert plan(manifest)["target_distribution"] == {
        "train/a": 1, "train/b": 1, "val/a": 1, "val/b": 1}
    manifest["samples"][0]["target_style"] = "a"
    with pytest.raises(ValueError):
        plan(manifest)


def test_finalizer_requires_review_and_preserves_split(tmp_path):
    manifest = fixture_manifest()
    generation = tmp_path / "generated"
    reviews = {}
    for index, sample in enumerate(manifest["samples"]):
        folder = generation / sample["sample_id"]
        folder.mkdir(parents=True)
        original, generated = folder / "original.png", folder / "generated.png"
        Image.new("RGB", (512, 512), (10 + index, 20, 30)).save(original)
        Image.new("RGB", (512, 512), (40 + index, 50, 60)).save(generated)
        sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        metadata = {"sample_id": sample["sample_id"], "source_member": sample["source_member"],
                    "source_member_sha256": sample["source_sha256"],
                    "source_style": sample["source_style"], "target_style": sample["target_style"],
                    "split": sample["split"], "attempt": 1, "source_revision": "pinned",
                    "base_model_id": "base", "base_model_revision": "pinned-base",
                    "prompt": instruction(manifest["styles"], sample["target_style"]),
                    "seed": 1977, "steps": 20, "guidance": 4.0, "method": "v1_global",
                    "width": 512, "height": 512, "original_sha256": sha(original),
                    "generated_sha256": sha(generated)}
        (folder / "generated.json").write_text(json.dumps(metadata), encoding="utf-8")
        reviews[sample["sample_id"]] = {"status": "ACCEPT", "attempt": 1, "notes": "checked"}
    review_path = tmp_path / "reviews.json"
    review_path.write_text(json.dumps(reviews), encoding="utf-8")
    output = tmp_path / "final"
    reviews["b1"]["status"] = "REGENERATE"
    review_path.write_text(json.dumps(reviews), encoding="utf-8")
    with pytest.raises(ValueError, match="Explicit ACCEPT"):
        finalize(manifest, generation, review_path, output)
    assert not output.exists()
    reviews["b1"]["status"] = "ACCEPT"
    review_path.write_text(json.dumps(reviews), encoding="utf-8")
    report = finalize(manifest, generation, review_path, output)
    assert report["identity_counts"] == {"train": 1, "val": 1}
    assert report["pair_counts"] == {"train": 2, "val": 2}
    rows = json.loads((output / "manifests/pairs.json").read_text(encoding="utf-8"))
    assert {row["split"] for row in rows if row["sample_id"] == "a1"} == {"train"}
    assert {row["split"] for row in rows if row["sample_id"] == "b1"} == {"val"}
    assert len(report["contact_sheets"]) == 2

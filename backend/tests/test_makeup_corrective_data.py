"""Synthetic data contracts only. These fixtures are not accepted project data."""
import copy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys

import numpy as np
from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from scripts import makeup_corrective_data as data
from scripts.makeup_corrective_catalog import build_catalog, teacher_prompt
from makeup_target_quality import CRITERIA, ANNOTATIONS
from notebooks import train_m001_kaggle as trainer


def test_all_actual_styles_have_distinct_complete_supervision():
    catalog = build_catalog()
    styles = data.validate_catalog(catalog)
    assert set(styles) == data.STYLE_IDS
    assert len({s["caption"] for s in styles.values()}) == 13
    for style in styles.values():
        assert style["caption"] in teacher_prompt(style)
        assert "Foundation" in style["caption"]
    wrong = copy.deepcopy(catalog)
    wrong["styles"][0]["id"] = "invented_style"
    with pytest.raises(ValueError): data.validate_catalog(wrong)


@pytest.fixture(scope="module")
def candidates(tmp_path_factory):
    base = tmp_path_factory.mktemp("corrective-synthetic")
    old = base / "old"
    selection = {"source_archive_sha256": data.SOURCE_ARCHIVE_SHA256,
        "train_ids": ["003681", "006553", "015406", "017290", "020867", "022625", "035149", "036948", "051141", "059106"],
        "validation_ids": ["054109", "056266"], "source_dataset_license": "Synthetic test fixture only"}
    rows = []
    for split in ("train", "validation"):
        for i, identity in enumerate(selection[split + "_ids"]):
            path = old / split / (identity + ".jpg")
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (512, 512), (40 + i + (20 if split == "validation" else 0), 70, 90)).save(path)
            rows.append({"identity_id": identity, "split": split, "reference": path.relative_to(old).as_posix(),
                "source_sha256": data.digest(path), "caption": "Generic synthetic fixture caption",
                "source_photo": {"author": "Synthetic test fixture", "photo_url": "https://example.org/test",
                    "license": "Test only", "license_url": "https://example.org/test/terms"}})
    data.write(old / "manifests/pairs.json", rows)
    data.write(old / "manifests/selection.json", selection)
    workspace = base / "candidate"
    frozen = data.initialize(workspace, source_dataset=old)
    for i, pair in enumerate(frozen["planned_pairs"]):
        source = next(s for s in frozen["sources"] if s["identity_id"] == pair["identity_id"])
        prepared = base / "prepared" / pair["pair_id"]
        prepared.mkdir(parents=True)
        Image.new("RGB", (512, 512), (i + 1, 100, 110)).save(prepared / "prepared.png")
        Image.new("L", (512, 512), 0).save(prepared / "alpha.png")
        raw = prepared / "raw.png"
        Image.new("RGB", (512, 512), (i + 1, 120, 130)).save(raw)
        data.write(prepared / "report.json", {"source_id": pair["identity_id"], "style_id": pair["style_id"],
            "source_sha256": source["sha256"], "prepared_sha256": data.digest(prepared / "prepared.png"),
            "raw_sha256": data.digest(raw), "training_accepted": False, "not_our_makeup_model_output": True})
        generation = {"source_id": pair["identity_id"], "style_id": pair["style_id"], "tool": "built-in image_gen",
            "model_id": "synthetic unit test, not an actual model", "prompt": "Synthetic unit test only",
            "prompt_record": "EXACT", "training_accepted": False, "production_enabled": False}
        data.register_target(workspace, prepared, raw, generation)
    return workspace


def attest_fixture(workspace):
    review = data.read(workspace / "reports/target_quality.json")
    for row in review["pairs"]:
        row.update(decision="ACCEPT", human_approved=True, reviewer="Synthetic fixture reviewer",
            evidence="UNIT TEST ONLY, not actual project target admission",
            criteria={key: {"verdict": "PASS", "note": "Synthetic unit test only"} for key in CRITERIA},
            source_cosmetics={key: "Synthetic fixture only" for key in ANNOTATIONS},
            target_cosmetics={key: "Synthetic fixture only" for key in ANNOTATIONS})
    data.write(workspace / "reports/target_quality.json", review)


def test_full_candidate_plan_still_cannot_finalize_without_human_review(candidates, tmp_path):
    destination = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="human corrective target acceptance"):
        data.finalize(candidates, destination)
    assert not destination.exists()
    with pytest.raises(ValueError, match="not finalized"):
        trainer.prepare(candidates, tmp_path / "must-not-train")


def test_finalized_corrective_contract_prepares_separate_fresh_base_run(candidates, tmp_path):
    workspace = tmp_path / "candidate"
    shutil.copytree(candidates, workspace)
    attest_fixture(workspace)
    final = tmp_path / "final"
    evidence = data.finalize(workspace, final)
    assert evidence["pair_counts"] == {"train": 52, "validation": 26}
    assert evidence["identity_counts"] == {"train": 10, "validation": 2}
    assert data.read(workspace / "reports/qa.json")["status"] == "DRAFT"
    prepared = trainer.prepare(final, tmp_path / "new-run")
    config = Path(prepared["config"]).read_text()
    assert "makeup001_corrective001_250step" in config
    assert trainer.MODEL_REVISION in config
    assert "pretrained_lora" not in config
    assert prepared["dataset_schema"] == data.SCHEMA
    evaluation = trainer.evaluation_plan(final, final / "catalog.json")
    assert evaluation["expected_outputs"] == 52
    assert set(evaluation["prompts"]) == data.STYLE_IDS
    for row in data.read(final / "manifests/pairs.json"):
        assert evaluation["prompts"][row["style_id"]] == row["caption"]
    with pytest.raises(ValueError):
        trainer.evaluation_plan(final, ROOT / "data/makeup/DATA-M001-paired/inference_presets.json")


def test_corrective_bundle_runs_cpu_prepare_standalone(candidates, tmp_path):
    import subprocess
    from zipfile import ZipFile
    from data_m001_package_training import package
    workspace = tmp_path / "candidate"
    shutil.copytree(candidates, workspace)
    attest_fixture(workspace)
    final = tmp_path / "final"
    data.finalize(workspace, final)
    archive = tmp_path / "corrective.zip"
    receipt = package(final, ROOT / "notebooks/train_m001_kaggle.py", final / "catalog.json", archive)
    assert receipt["dataset_pairs"] == 78
    extracted = tmp_path / "standalone"
    with ZipFile(archive) as opened:
        assert "makeup_corrective_data.py" in opened.namelist()
        opened.extractall(extracted)
    result = subprocess.run([sys.executable, str(extracted / "train_m001_kaggle.py"), "--phase", "prepare",
        "--dataset", str(extracted / "data_m001"), "--out", str(extracted / "fresh-run")],
        cwd=extracted, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["status"] == "PREPARED_NOT_STARTED"


@pytest.mark.parametrize("failure", ["caption", "split", "coverage", "provenance", "source_pixels", "rgba"])
def test_correction_refuses_changed_supervision_or_sources(candidates, tmp_path, failure):
    workspace = tmp_path / "candidate"
    shutil.copytree(candidates, workspace)
    attest_fixture(workspace)
    rows = data.read(workspace / "manifests/pairs.json")
    row = rows[0]
    if failure == "caption": row["caption"] = "Generic apply makeup caption"
    if failure == "split": row["split"] = "validation"
    if failure == "coverage": rows.pop()
    if failure == "provenance":
        name = next(iter(row["provenance_files"]))
        (workspace / name).write_text("changed")
    if failure == "source_pixels": Image.new("RGB", (512, 512), "blue").save(workspace / row["reference"])
    if failure == "rgba": Image.new("RGBA", (512, 512), "red").save(workspace / row["target"])
    data.write(workspace / "manifests/pairs.json", rows)
    destination = tmp_path / "must-not-finalize"
    with pytest.raises(ValueError): data.finalize(workspace, destination)
    assert not destination.exists()


def test_legacy_training_name_is_preserved(tmp_path):
    config = trainer.training_config(tmp_path / "legacy", tmp_path / "run")
    assert 'name: "makeup001_250step"' in config
    assert "corrective001" not in config


def test_extra_complexion_sources_keep_validation_and_style_coverage(candidates, tmp_path, monkeypatch):
    old = tmp_path / "old"
    shutil.copytree(candidates.parent / "old", old)
    selection = data.read(old / "manifests/selection.json")
    selection["ffhq_metadata_md5"] = "synthetic metadata identity"
    data.write(old / "manifests/selection.json", selection)
    extras = []
    for i, identity in enumerate(("900001", "900002")):
        path = tmp_path / (identity + ".jpg")
        Image.new("RGB", (512, 512), (20 + i * 10, 15, 10)).save(path)
        extras.append({"identity_id": identity, "split": "train", "path": path.name, "sha256": data.digest(path),
            "source_archive_sha256": data.SOURCE_ARCHIVE_SHA256, "ffhq_metadata_md5": selection["ffhq_metadata_md5"],
            "source_archive_member": identity + "/bare.jpg", "source_photo": {"author": "Synthetic fixture"},
            "source_dataset_license": "Synthetic fixture only"})
    monkeypatch.setattr(data, "ROOT", tmp_path)
    frozen = data.initialize(tmp_path / "expanded", source_dataset=old, extra_training_sources=extras)
    assert len(frozen["source_selection"]["train_ids"]) == 12
    assert frozen["source_selection"]["validation_ids"] == selection["validation_ids"]
    assert frozen["historical_source_selection"]["train_ids"] == selection["train_ids"]
    assert frozen["planned_counts"] == {"train": 52, "validation": 26}
    for style in data.STYLE_IDS:
        train = [p for p in frozen["planned_pairs"] if p["style_id"] == style and p["split"] == "train"]
        assert len(train) == 4
        assert len({p["identity_id"] for p in train} & {"900001", "900002"}) == 1


def test_frozen_warp_padding_can_be_excluded_by_target_support():
    from scripts.makeup_selected_cosmetics import warp_reference
    rng = np.random.default_rng(73)
    points = np.column_stack((rng.uniform(.1, .9, (478, 2)), np.zeros(478)))
    points[:4, :2] = [[.1, .1], [.9, .1], [.1, .9], [.9, .9]]
    reference = points.copy(); reference[:, 0] += .4
    image = np.full((512, 512, 3), 80, np.uint8)
    labels = np.ones((512, 512), np.uint8)
    pixels, _, hull = warp_reference(image, labels, points, reference)
    support, _, _ = warp_reference(np.ones_like(image, dtype=np.float32), labels, points, reference)
    valid = hull & (support[..., 0] >= 1 - 1e-6)
    assert np.any(hull & ~valid)
    assert np.all(pixels[valid] == 80)


@pytest.mark.parametrize("wrong_cache", [False, True])
def test_teacher_preparation_preserves_unicode_credit_and_binds_cache(tmp_path, monkeypatch, wrong_cache):
    from scripts import prepare_makeup_teacher as teacher
    monkeypatch.setattr(teacher, "ROOT", tmp_path)
    source = tmp_path / "source.jpg"
    Image.new("RGB", (512, 512), (75, 50, 35)).save(source)
    labels = tmp_path / "labels.png"
    Image.new("L", (512, 512), 1).save(labels)
    points = tmp_path / "points.json"
    data.write(points, {"points": np.zeros((478, 3)).tolist()})
    plan_path = tmp_path / "source-plan.json"
    data.write(plan_path, {"sources": [{"id": "fixture", "source": source.name, "sha256": data.digest(source),
        "labels": labels.name, "labels_sha256": data.digest(labels), "points478": points.name,
        "points478_sha256": data.digest(points), "source_photo": {"author": "Júlia 安娜"}}]})
    raw = tmp_path / "teacher.png"
    Image.new("RGB", (512, 512), (80, 52, 37)).save(raw)
    normalized = np.array(Image.open(raw))
    cache = {"normalized_rgb_sha256": "0" * 64 if wrong_cache else sha256(normalized.tobytes()).hexdigest(),
             "labels": np.ones((512, 512), np.uint8), "points": np.zeros((478, 3), np.float32)}
    def no_model(*args, **kwargs): pytest.fail("Cached anatomy unexpectedly loaded a model")
    monkeypatch.setattr(teacher, "analyze_images", no_model)
    monkeypatch.setattr(teacher, "fit", lambda original, *args, **kwargs:
                        (original.copy(), np.zeros((512, 512)), {"fit_version": "synthetic-test"}))
    output = tmp_path / "prepared"
    if wrong_cache:
        with pytest.raises(ValueError, match="different teacher"):
            teacher.prepare("fixture", "soft_glam", raw, output, source_plan=plan_path, target_anatomy=cache)
        assert not output.exists()
    else:
        teacher.prepare("fixture", "soft_glam", raw, output, source_plan=plan_path, target_anatomy=cache)
        assert data.read(output / "report.json")["source_photo"]["author"] == "Júlia 安娜"


def test_brow_gradient_fitting_keeps_hair_detail_and_protected_pixels():
    # AC2: source hairs must not become a uniform density plate on foundation.
    from scripts.prepare_makeup_teacher import restore_brow_gradients
    original = np.full((512, 512, 3), (200, 170, 145), np.uint8)
    target = np.full_like(original, (165, 135, 115))
    brow = np.zeros((512, 512), bool)
    brow[180:198, 100:170] = True
    original[183:195, 109:112] = (60, 45, 30)
    original[183:195, 125:128] = (90, 65, 45)
    allowed = np.ones((512, 512), bool)
    allowed[190:200, 145:155] = False
    result = restore_brow_gradients(original, target, brow, allowed)
    assert np.array_equal(result[~allowed], target[~allowed])
    assert np.array_equal(result[:170], target[:170])
    assert np.array_equal(result[210:], target[210:])
    assert result[187, 110, 0] < result[187, 120, 0] - 100
    assert result[187, 126, 0] < result[187, 120, 0] - 80
    assert result[187, 110, 0] < result[187, 126, 0] - 20


def test_brow_gradient_fitting_refuses_missing_support():
    from scripts.prepare_makeup_teacher import restore_brow_gradients
    pixels = np.zeros((512, 512, 3), np.uint8)
    with pytest.raises(ValueError, match="support unavailable"):
        restore_brow_gradients(pixels, pixels, np.zeros((512, 512), bool), np.ones((512, 512), bool))

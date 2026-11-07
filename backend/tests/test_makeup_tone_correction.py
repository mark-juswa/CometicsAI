"""CPU tone-correction invariants; no generative model or external images."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts import makeup_tone_correction as tone


@pytest.fixture
def portrait():
    labels = np.zeros((128, 128), np.uint8)
    labels[5:120, 8:120] = 1
    labels[46:51, 29:41] = 4
    labels[46:51, 85:97] = 5
    labels[35:39, 27:42] = 6
    labels[35:39, 83:98] = 7
    labels[86:90, 47:81] = 11
    labels[90:94, 47:81] = 12
    labels[89:91, 53:75] = 10
    labels[59:78, 60:68] = 2
    original = np.full((128,128,3), (95,70,45), np.uint8)
    raw = np.full_like(original, (175,146,138))
    raw[np.isin(labels,(11,12))] = (190,20,50)
    raw[np.isin(labels,(4,5))] = (30,20,25)
    return original, raw, labels, [26,10,100,30]


def test_bounded_correction_and_protected_rgb(portrait):
    source, raw, labels, box = portrait
    source_before, raw_before = source.copy(), raw.copy()
    result, masks, metrics = tone.correct(source,raw,labels,labels,box)
    changed = np.any(result != raw, axis=2)
    assert changed.any()
    assert np.array_equal(result[masks["alpha"] == 0],raw[masks["alpha"] == 0])
    assert np.array_equal(result[masks["protected"]],raw[masks["protected"]])
    assert np.array_equal(result[np.isin(labels,(4,5,6,7,10,11,12))],
                          raw[np.isin(labels,(4,5,6,7,10,11,12))])
    assert metrics["outside_mask_changed_pixels"] == 0
    assert metrics["protected_changed_pixels"] == 0
    assert -16.0 <= metrics["applied_lab_offset"][0] < 0
    assert np.linalg.norm(metrics["applied_lab_offset"][1:]) <= 8.00001
    assert metrics["estimated_lightness_gap_after"] < metrics["estimated_lightness_gap_before"]
    assert np.array_equal(source,source_before) and np.array_equal(raw,raw_before)
    assert np.any((masks["alpha"]>0) & (masks["alpha"]<1))


@pytest.mark.parametrize("kind",["matching","already_darker"])
def test_no_needless_darkening_or_brightening(portrait,kind):
    source, raw, labels, box = portrait
    if kind == "matching": raw=source.copy()
    else: raw=np.full_like(source,(55,35,25))
    result, _, metrics = tone.correct(source,raw,labels,labels,box)
    assert metrics["status"] == "NO_EXCESS_LIGHTNESS"
    assert metrics["changed_pixels"] == 0
    assert np.array_equal(result,raw)


@pytest.mark.parametrize("box",[[0,0,1,1],[-1,10,90,30],[10,10,200,30],[10.5,10,90,30]])
def test_ambiguous_or_invalid_neutral_regions_rejected(portrait,box):
    source, raw, labels, _ = portrait
    with pytest.raises(ValueError):
        tone.correct(source,raw,labels,labels,box)


@pytest.mark.parametrize("mutation",["float_rgb","shape","labels","features","config"])
def test_invalid_processing_inputs_rejected(portrait,mutation):
    source,raw,labels,box=portrait
    config=deepcopy(tone.CONFIG)
    if mutation=="float_rgb": raw=raw.astype(float)
    elif mutation=="shape": raw=raw[:-1]
    elif mutation=="labels": labels=labels.copy(); labels[0,0]=255
    elif mutation=="features": labels=np.ones_like(labels)
    elif mutation=="config": config["maximum_lightness_reduction"]=100
    with pytest.raises(ValueError):
        tone.correct(source,raw,labels,labels,box,config)


def test_plan_forbids_serving_training_and_changed_artifacts(tmp_path,monkeypatch):
    monkeypatch.setattr(tone,"ROOT",tmp_path)
    source=tmp_path/"source.png"; raw=tmp_path/"raw.png"; report=tmp_path/"raw-report.json"
    Image.new("RGB",(128,128),(95,70,45)).save(source)
    Image.new("RGB",(128,128),(170,145,135)).save(raw)
    report.write_text("{}")
    plan={"experiment":"MAKEUP-TONE-001","production_enabled":False,"training":False,
          "correction":deepcopy(tone.CONFIG),
          "subjects":[{"id":str(i),"source":source.name,"source_sha256":tone.digest(source)} for i in range(2)],
          "cases":[{"id":str(i),"raw":raw.name,"raw_sha256":tone.digest(raw)} for i in range(6)],
          "source_report":report.name,"source_report_sha256":tone.digest(report)}
    path=tmp_path/"plan.json"
    path.write_text(json.dumps(plan))
    assert tone.load_plan(path)["training"] is False
    for flag in ("production_enabled","training"):
        bad=deepcopy(plan);bad[flag]=True;path.write_text(json.dumps(bad))
        with pytest.raises(ValueError):tone.load_plan(path)
    path.write_text(json.dumps(plan))
    raw.write_bytes(b"changed")
    with pytest.raises(ValueError,match="Raw result hash differs"):tone.load_plan(path)


def test_refuses_overwrite_before_parser_loading(tmp_path,monkeypatch):
    monkeypatch.setattr(tone,"load_plan",lambda path:{})
    output=tmp_path/"existing";output.mkdir()
    sentinel=output/"keep.txt";sentinel.write_text("Preserve evidence.")
    with pytest.raises(ValueError,match="New evidence"):
        tone.prepare(tmp_path/"plan.json",output)
    assert sentinel.read_text()=="Preserve evidence."

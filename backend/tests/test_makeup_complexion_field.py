"""Source-complexion invariants and saved-result reproduction, entirely offline."""
from hashlib import sha256
import json
from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.makeup_complexion_field import complexion, CONFIG


def fixture():
    labels = np.zeros((512,512), np.uint8)
    cv2.ellipse(labels,(256,240),(145,185),0,0,360,1,-1)
    cv2.rectangle(labels,(205,400),(305,511),17,-1)
    for x, value in ((195,4),(317,5)):
        cv2.ellipse(labels,(x,205),(27,12),0,0,360,value,-1)
    cv2.rectangle(labels,(229,325),(283,346),10,-1)
    cv2.ellipse(labels,(256,321),(45,9),0,0,180,11,-1)
    cv2.ellipse(labels,(256,348),(45,9),180,0,180,12,-1)
    source = np.full((512,512,3),(30,35,40),np.uint8)
    source[np.isin(labels,(1,17))] = (140,95,65)
    source[np.isin(labels,(4,5,10))] = (245,245,245)
    source[np.isin(labels,(11,12))] = (130,70,65)
    raw = source.copy()
    raw[labels==1] = (205,180,165)
    raw[np.isin(labels,(11,12))] = (185,40,80)
    cv2.circle(raw,(340,275),23,(220,120,135),-1)
    return source, raw, labels


def lightness(image):
    return cv2.cvtColor(image.astype(np.float32)/255,cv2.COLOR_RGB2LAB)[:,:,0]


def test_identical_reference_is_exact_noop():
    source, _, labels = fixture()
    result, _, _, _, _, _ = complexion(source, source.copy(), labels, labels)
    assert np.array_equal(result, source)


def test_removes_known_cast_retains_visible_cosmetics_and_input_bytes():
    source, raw, labels = fixture()
    source_before, raw_before = source.copy(), raw.copy()
    result, allowed, metrics, _, field, neutral = complexion(source,raw,labels,labels)
    before = abs(float(lightness(raw)[130,256]-lightness(source)[130,256]))
    after = abs(float(lightness(result)[130,256]-lightness(source)[130,256]))
    assert after < before*.5
    assert np.linalg.norm(result[275,340].astype(float)-result[130,256]) > 25
    assert np.linalg.norm(np.median(result[labels==11],axis=0)-result[130,256]) > 25
    assert np.array_equal(source,source_before) and np.array_equal(raw,raw_before)
    assert np.array_equal(result[~allowed],raw[~allowed])
    assert metrics["anchor_cells"] >= CONFIG["minimum_anchor_cells"]
    assert neutral.sum() > 1000 and np.isfinite(field).all()


def test_inner_eye_and_neutral_teeth_protection_does_not_leave_whole_lip_island():
    source,raw,labels=fixture()
    result, _, metrics, _, _, _=complexion(source,raw,labels,labels)
    assert np.array_equal(result[205,195],raw[205,195])
    assert np.array_equal(result[335,256],raw[335,256])
    assert metrics["whole_lips_hard_protected"] is False
    assert np.any(result[labels==11]!=raw[labels==11])


@pytest.mark.parametrize("fault",["float_rgb","wrong_size","bad_labels","missing_eye","no_neutral_skin"])
def test_ambiguous_or_invalid_reference_fails_closed(fault):
    source,raw,labels=fixture()
    sl,rl=labels.copy(),labels.copy()
    if fault=="float_rgb": source=source.astype(np.float32)
    if fault=="wrong_size": raw=raw[:500]
    if fault=="bad_labels": rl[0,0]=255
    if fault=="missing_eye": rl[rl==4]=1
    if fault=="no_neutral_skin": sl[np.isin(sl,(1,17))]=18
    with pytest.raises(ValueError):
        complexion(source,raw,sl,rl)


CASES=[]
for relative in ("artifacts/makeup-complexion-20261101/run-02","artifacts/makeup-complexion-20261101/serving-controls"):
    folder=ROOT/relative
    if (folder/"report.json").exists():
        report=json.loads((folder/"report.json").read_text(encoding="utf-8"))
        for row in report["cases"]:
            CASES.append((folder,row))


@pytest.mark.parametrize("folder,row",CASES,ids=[row["id"] for _,row in CASES])
def test_exact_saved_output_reproduction_and_unchanged_influence_exterior(folder,row):
    plan=json.loads((ROOT/"data/makeup/MAKEUP-COMPLEXION-001/plan-v2.json").read_text(encoding="utf-8"))
    subject=next(s for s in plan["sources"] if s["id"]==row["subject_id"])
    source=ROOT/subject["source"]
    raw=ROOT/row["raw"]
    assert sha256(source.read_bytes()).hexdigest()==subject["source_sha256"]
    assert sha256(raw.read_bytes()).hexdigest()==row["raw_sha256"]
    labels=ROOT/(row["raw_labels"] if "raw_labels" in row else row["labels"])
    digest=row.get("raw_labels_sha256",row.get("labels_sha256"))
    assert sha256(labels.read_bytes()).hexdigest()==digest
    sl=ROOT/subject["source_labels"]
    assert sha256(sl.read_bytes()).hexdigest()==subject["source_labels_sha256"]
    read=lambda p:np.asarray(Image.open(p).convert("RGB")).copy()
    result,allowed,metrics,_,_,_=complexion(read(source),read(raw),np.asarray(Image.open(sl)).copy(),np.asarray(Image.open(labels)).copy())
    assert sha256(result.tobytes()).hexdigest()==row["rgb_sha256"]
    with Image.open(folder/row["output"]) as saved:
        assert np.array_equal(result,np.asarray(saved.convert("RGB")))
    assert np.array_equal(result[~allowed],read(raw)[~allowed])
    assert metrics["protected_changed_pixels"]==0


@pytest.mark.parametrize("fault",["automatic_promotion","algorithm_hash","duplicate_case","setting_matrix","raw_hash"])
def test_review_refuses_scope_or_evidence_drift_before_processing(tmp_path,fault):
    from scripts.evaluate_makeup_complexion import load
    path=ROOT/"data/makeup/MAKEUP-COMPLEXION-001/review-plan.json"
    plan=json.loads(path.read_text(encoding="utf-8"))
    if fault=="automatic_promotion": plan["automatic_promotion"]=True
    if fault=="algorithm_hash": plan["algorithm_sha256"]="0"*64
    if fault=="duplicate_case": plan["cases"][1]["id"]=plan["cases"][0]["id"]
    if fault=="setting_matrix": plan["cases"][0]["guidance"]=3.0
    if fault=="raw_hash": plan["cases"][0]["raw_sha256"]="0"*64
    changed=tmp_path/"changed.json"
    changed.write_text(json.dumps(plan),encoding="utf-8")
    with pytest.raises(ValueError):
        load(changed)

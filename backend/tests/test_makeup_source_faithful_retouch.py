"""Original-photo fidelity checks for the bounded subtle complexion prototype."""
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
from scripts.makeup_source_faithful_retouch import retouch, CONFIG, LUMA


def fixture():
    labels=np.zeros((512,512),np.uint8)
    cv2.ellipse(labels,(256,240),(140,185),0,0,360,1,-1)
    for x,eye,brow in ((195,4,6),(317,5,7)):
        cv2.ellipse(labels,(x,205),(26,12),0,0,360,eye,-1)
        cv2.rectangle(labels,(x-25,175),(x+25,180),brow,-1)
    cv2.rectangle(labels,(231,325),(281,345),10,-1)
    cv2.ellipse(labels,(256,320),(42,9),0,0,180,11,-1)
    cv2.ellipse(labels,(256,348),(42,9),180,0,180,12,-1)
    image=np.full((512,512,3),(35,45,55),np.uint8)
    yy,xx=np.mgrid[:512,:512]
    texture=(((xx*3+yy*7)%11)-5)
    for c,base in enumerate((145,100,75)):
        image[:,:,c][labels==1]=np.clip(base+texture[labels==1],0,255)
    image[np.isin(labels,(4,5,10))]=(240,235,225)
    image[np.isin(labels,(6,7))]=(40,35,30)
    image[np.isin(labels,(11,12))]=(125,65,70)
    # Source blemish/freckle details must not be painted over.
    image[270:273,210:213]=(75,55,42)
    reference=image.copy()
    cv2.circle(reference,(332,270),33,(235,95,115),-1)
    cv2.circle(reference,(177,270),33,(235,95,115),-1)
    reference[np.isin(labels,(4,5,10,11,12))]=(255,255,255)
    return image,reference,labels


def test_identical_reference_is_exact_noop():
    source,_,labels=fixture()
    result,_,_=retouch(source,source.copy(),labels,labels)
    assert np.array_equal(result,source)


def test_reference_makeover_cannot_replace_original_features_brightness_or_texture():
    source,reference,labels=fixture()
    original,previous=source.copy(),reference.copy()
    result,allowed,metrics=retouch(source,reference,labels,labels)
    diff=result.astype(np.int16)-source.astype(np.int16)
    assert np.abs(diff).max()<=4
    assert np.max(np.abs(diff.astype(float)@LUMA))<=.501
    assert np.array_equal(result[labels!=1],source[labels!=1])
    assert np.array_equal(result[~allowed],source[~allowed])
    assert np.array_equal(source,original) and np.array_equal(reference,previous)
    assert metrics["original_is_canvas"] and not metrics["generated_pixels_are_canvas"]
    assert not metrics["display_geometry_warped"] and not metrics["smoothing_or_glow_applied"]
    assert metrics["changed_pixels"]>0
    original_mark=float((source.astype(float)@LUMA)[271,211])
    output_mark=float((result.astype(float)@LUMA)[271,211])
    assert abs(original_mark-output_mark)<=.501


def test_global_reference_color_cast_is_removed_instead_of_recoloring_original():
    source,_,labels=fixture()
    reference=np.clip(source.astype(np.int16)+np.array([10,5,0]),0,255).astype(np.uint8)
    result,_,_=retouch(source,reference,labels,labels)
    assert np.array_equal(result,source)


def test_gamut_boundary_does_not_clip_original_or_change_source_luma():
    source,reference,labels=fixture()
    source[labels==1]=(254,120,253)
    reference[labels==1]=(30,245,20)
    cv2.circle(reference,(332,270),33,(240,20,30),-1)
    result,_,_=retouch(source,reference,labels,labels)
    diff=result.astype(np.int16)-source.astype(np.int16)
    assert np.abs(diff).max()<=4
    assert np.max(np.abs(diff.astype(float)@LUMA))<=.501


@pytest.mark.parametrize("fault",["float_source","wrong_size","bad_labels","missing_eye","missing_mouth","no_common_skin"])
def test_uncertain_inputs_fail_without_producing_a_retouch(fault):
    source,reference,labels=fixture()
    sl,rl=labels.copy(),labels.copy()
    if fault=="float_source": source=source.astype(np.float32)
    if fault=="wrong_size": reference=reference[:500]
    if fault=="bad_labels": sl[0,0]=255
    if fault=="missing_eye": sl[sl==4]=1
    if fault=="missing_mouth": rl[np.isin(rl,(10,11,12))]=1
    if fault=="no_common_skin": rl[rl==1]=13
    with pytest.raises(ValueError):
        retouch(source,reference,sl,rl)


@pytest.mark.parametrize("identity",["054109","056266"])
def test_saved_real_result_reproduces_and_preserves_all_original_non_skin_rgb(identity):
    folder=ROOT/"artifacts/makeup-faithful-20261101/run-02"
    plan=json.loads((folder/"plan.json").read_text(encoding="utf-8"))
    report=json.loads((folder/"report.json").read_text(encoding="utf-8"))
    row=next(r for r in report["cases"] if r["id"]==identity)
    assert plan["configuration"]==CONFIG
    for name,key in (("source","source_sha256"),("source_labels","source_labels_sha256"),
                     ("reference","reference_sha256"),("reference_labels","reference_labels_sha256")):
        assert sha256((ROOT/row[name]).read_bytes()).hexdigest()==row[key]
    rgb=lambda p:np.asarray(Image.open(p).convert("RGB")).copy()
    original,reference=rgb(ROOT/row["source"]),rgb(ROOT/row["reference"])
    labels=np.asarray(Image.open(ROOT/row["source_labels"])).copy()
    result,_,metrics=retouch(original,reference,labels,np.asarray(Image.open(ROOT/row["reference_labels"])).copy())
    assert sha256(result.tobytes()).hexdigest()==row["rgb_sha256"]
    assert np.array_equal(result,rgb(folder/row["output"]))
    assert np.array_equal(result[labels!=1],original[labels!=1])
    assert metrics["protected_source_pixels_changed"]==0


@pytest.mark.parametrize("fault",["production","strength","algorithm","source_hash"])
def test_review_refuses_unapproved_strengths_or_changed_evidence(tmp_path,fault):
    from scripts.evaluate_source_faithful_retouch import load_plan
    plan=json.loads((ROOT/"data/makeup/MAKEUP-FAITHFUL-001/plan-v2.json").read_text(encoding="utf-8"))
    if fault=="production": plan["production_enabled"]=True
    if fault=="strength": plan["configuration"]["strength"]=.8
    if fault=="algorithm": plan["algorithm_sha256"]="0"*64
    if fault=="source_hash": plan["cases"][0]["source_sha256"]="0"*64
    path=tmp_path/"changed.json";path.write_text(json.dumps(plan),encoding="utf-8")
    with pytest.raises(ValueError):
        load_plan(path)


def test_small_background_face_region_remains_exact_original():
    source,reference,labels=fixture()
    labels[25:50,10:35]=1
    source[25:50,10:35]=(120,80,60)
    reference[25:50,10:35]=(255,150,20)
    result,_,metrics=retouch(source,reference,labels,labels)
    assert np.array_equal(result[25:50,10:35],source[25:50,10:35])
    assert metrics["non_primary_face_pixels_changed"]==0


def test_comparable_second_face_is_rejected_before_retouch():
    source,reference,labels=fixture()
    labels[35:450,:80]=1
    with pytest.raises(ValueError,match="Multiple"):
        retouch(source,reference,labels,labels)

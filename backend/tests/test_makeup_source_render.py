"""Source-coordinate cosmetic rendering safeguards; synthetic CPU fixtures."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts import makeup_source_render as renderer


@pytest.fixture
def synthetic():
    labels=np.zeros((512,512),np.uint8)
    cv2.ellipse(labels,(256,270),(170,220),0,0,360,1,-1)
    cv2.ellipse(labels,(255,285),(20,40),0,0,360,2,-1)
    for center,code in (((185,210),4),((325,205),5)):
        cv2.ellipse(labels,center,(35,10),0,0,360,code,-1)
    for center,code in (((185,175),6),((325,170),7)):
        cv2.ellipse(labels,center,(40,7),0,0,360,code,-1)
    cv2.ellipse(labels,(255,370),(70,20),0,0,360,12,-1)
    labels[(labels==12)&(np.arange(512)[:,None]<370)]=11
    cv2.ellipse(labels,(255,367),(62,10),0,0,360,10,-1)
    yy,xx=np.mgrid[:512,:512]
    source=np.stack((135+18*np.sin(xx/20),95+15*np.cos(yy/15),
                     80+10*np.sin((xx+yy)/9)),axis=-1).clip(0,255).astype(np.uint8)
    return source,labels


@pytest.fixture
def profiles():
    return json.loads((ROOT/"data/makeup/MAKEUP-RENDER-001/plan-gamut-v2.json").read_text())["profiles"]


@pytest.mark.parametrize("style",renderer.STYLES)
def test_only_cosmetic_regions_change_and_preserve_protected_features(synthetic,profiles,style):
    source,labels=synthetic
    before=source.copy()
    result,fields,metrics=renderer.render(source,labels,profiles[style])
    _,protected,allowed,_=renderer.geometry(labels)
    assert np.array_equal(source,before)
    assert np.array_equal(result[~allowed],source[~allowed])
    assert np.array_equal(result[protected],source[protected])
    assert np.array_equal(result[60:120,180:300],source[60:120,180:300])
    assert metrics["outside_cosmetic_changed_pixels"]==0
    assert metrics["protected_changed_pixels"]==0
    assert metrics["changed_pixels"]>100
    assert all(metrics["region_changed_pixels"][name]>0 for name in fields)
    again,_,_=renderer.render(source,labels,profiles[style])
    assert np.array_equal(result,again)


def test_zero_opacity_is_exact_source(synthetic,profiles):
    source,labels=synthetic
    profile=deepcopy(profiles["natural_makeup"])
    for key in ("lip","shadow","liner","blush"):
        profile[key+"_opacity"]=0
    result,_,metrics=renderer.render(source,labels,profile)
    assert np.array_equal(source,result)
    assert metrics["changed_pixels"]==0


def test_styles_are_distinct_without_full_face_change(synthetic,profiles):
    source,labels=synthetic
    results=[renderer.render(source,labels,profiles[s])[0] for s in renderer.STYLES]
    for i in range(3):
        for j in range(i):
            assert np.any(results[i][np.isin(labels,(11,12))]!=results[j][np.isin(labels,(11,12))])
            assert np.array_equal(results[i][:100],results[j][:100])


@pytest.mark.parametrize("mutation",["missing_eye","missing_brow","missing_lip","bad_label","wrong_size","disconnected_face"])
def test_ambiguous_facial_regions_fail_closed(synthetic,mutation):
    _,labels=synthetic
    labels=labels.copy()
    if mutation=="missing_eye":labels[labels==4]=1
    elif mutation=="missing_brow":labels[labels==6]=1
    elif mutation=="missing_lip":labels[np.isin(labels,(11,12))]=1
    elif mutation=="bad_label":labels[0,0]=255
    elif mutation=="wrong_size":labels=labels[:-1]
    elif mutation=="disconnected_face":labels[10:150,0:60]=1
    with pytest.raises(ValueError):
        renderer.geometry(labels)


@pytest.mark.parametrize("field,value",[
    ("lip_opacity",1.1),("blush_opacity",0.7),("shadow_opacity",float("nan")),
    ("lip_rgb",[300,0,0]),("lip_lightness_cap",100)])
def test_invalid_profiles_rejected(profiles,field,value):
    profile=deepcopy(profiles["soft_glam"]);profile[field]=value
    with pytest.raises(ValueError):renderer.profile_check(profile)


def test_inverse_color_conversion_matches_known_linear_rgb():
    rgb=np.array([[[128,0,0],[80,120,160],[255,255,255],[0,0,0]]],np.uint8)
    f=rgb.astype(np.float32)/255
    expected=np.where(f<=0.04045,f/12.92,((f+0.055)/1.055)**2.4)
    assert np.allclose(renderer.linear_rgb(renderer.lab(rgb)),expected,atol=.004)


def test_gamut_mapping_preserves_lightness_and_hue_direction():
    values=np.array([[[60,100,100],[40,100,-100],[50,5,5]]],np.float32)
    result,count=renderer.gamut_safe(values,np.ones((1,3),bool))
    rgb=renderer.linear_rgb(result)
    assert count==2
    assert (rgb>=-1e-5).all() and (rgb<=1+1e-5).all()
    assert np.array_equal(values[:,:,0],result[:,:,0])
    assert np.array_equal(result[0,2],values[0,2])
    for i in (0,1):
        assert abs(np.cross(values[0,i,1:],result[0,i,1:]))<.01


@pytest.fixture
def local_plan(tmp_path,monkeypatch,synthetic):
    monkeypatch.setattr(renderer,"ROOT",tmp_path)
    plan=json.loads((ROOT/"data/makeup/MAKEUP-RENDER-001/plan-gamut-v2.json").read_text())
    source,_=synthetic
    for subject in plan["subjects"]:
        path=tmp_path/(subject["id"]+".png")
        Image.fromarray(source).save(path)
        subject["source"]=path.name;subject["sha256"]=renderer.digest(path)
    path=tmp_path/"plan.json";path.write_text(json.dumps(plan))
    return path,plan


@pytest.mark.parametrize("flag",["production_enabled","training","lora_active","project_trained_generator_used"])
def test_no_misleading_model_or_serving_flags(local_plan,flag):
    path,plan=local_plan;plan[flag]=True;path.write_text(json.dumps(plan))
    with pytest.raises(ValueError):renderer.load_plan(path)


def test_source_tamper_and_path_escape_rejected(local_plan):
    path,plan=local_plan
    assert renderer.load_plan(path)["training"] is False
    (path.parent/plan["subjects"][0]["source"]).write_bytes(b"changed")
    with pytest.raises(ValueError):renderer.load_plan(path)
    plan["subjects"][0]["source"]="../outside.png";path.write_text(json.dumps(plan))
    with pytest.raises(ValueError,match="escapes"):renderer.load_plan(path)


def test_existing_evidence_not_overwritten(local_plan,tmp_path):
    path,_=local_plan
    output=tmp_path/"results";output.mkdir()
    sentinel=output/"keep.txt";sentinel.write_text("Original evidence.")
    with pytest.raises(ValueError,match="New pilot"):
        renderer.prepare(path,output)
    assert sentinel.read_text()=="Original evidence."

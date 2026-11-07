"""Alignment and pixel-safety gates; no assertion of cosmetic realism."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import numpy as np
import pytest
from test_makeup_source_render import synthetic

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts import makeup_alignment_pilot as alignment
from scripts import makeup_aligned_soft_glam as painter


@pytest.fixture
def points():
    p=np.full((478,3),.5,np.float32);p[:,2]=0
    for side,cx,cy in (("right",185,210),("left",325,205)):
        for kind,sign in (("upper",-1),("lower",1)):
            ids=alignment.CHAINS[side+"_"+kind];u=np.linspace(0,1,len(ids))
            p[ids,0]=(cx-35+70*u)/512
            p[ids,1]=(cy+sign*10*np.sin(np.pi*u))/512
        for kind,y in (("brow_lower",cy-28),("brow_upper",cy-40)):
            ids=alignment.CHAINS[side+"_"+kind]
            p[ids,0]=np.linspace(cx-40,cx+40,len(ids))/512
            p[ids,1]=y/512
    for kind,cy,rx,ry in (("lip_outer",370,70,20),("lip_inner",367,62,10)):
        ids=alignment.CHAINS[kind];theta=np.linspace(0,2*np.pi,len(ids),endpoint=False)
        p[ids,0]=(255+rx*np.cos(theta))/512;p[ids,1]=(cy+ry*np.sin(theta))/512
    return p


def test_anatomy_matches_both_semantic_eyes(synthetic,points):
    _,labels=synthetic
    geometry=alignment.geometry(points,labels)
    assert {e["label"] for e in geometry["eyes"]}=={4,5}
    assert geometry["eyes"][0]["center"][0]<geometry["eyes"][1]["center"][0]
    assert all(65<e["width"]<75 for e in geometry["eyes"])


@pytest.mark.parametrize("mutation",["missing_point","nan","out_of_frame","closed_eye","shift_eye","shift_mouth"])
def test_bad_landmarks_fail_closed(synthetic,points,mutation):
    _,labels=synthetic;p=points.copy()
    if mutation=="missing_point":p=p[:-1]
    elif mutation=="nan":p[1,0]=np.nan
    elif mutation=="out_of_frame":p[1,0]=1.1
    elif mutation=="closed_eye":
        p[alignment.CHAINS["right_lower"],1]=p[alignment.CHAINS["right_upper"],1]
    elif mutation=="shift_eye":
        ids=list(set(alignment.CHAINS["right_lower"]+alignment.CHAINS["right_upper"]))
        p[ids,0]+=.2
    elif mutation=="shift_mouth":p[alignment.CHAINS["lip_outer"],1]-=.2
    with pytest.raises(ValueError):
        alignment.geometry(p,labels)


def test_render_exact_protection_and_determinism(synthetic,points):
    source,labels=synthetic;before=source.copy();maps=labels.copy();landmarks=points.copy()
    result,fields,metrics=painter.render(source,labels,points)
    repeated=painter.render(source,labels,points)[0]
    _,protected,support,eye_safe=painter.fields_for(labels,points)
    assert np.array_equal(source,before) and np.array_equal(labels,maps)
    assert np.array_equal(points,landmarks) and np.array_equal(result,repeated)
    assert np.array_equal(result[protected],source[protected])
    assert np.array_equal(result[~support],source[~support])
    assert np.array_equal(result[eye_safe],source[eye_safe])
    assert np.array_equal(result[:100],source[:100])
    assert metrics["changed_pixels"]>100
    assert metrics["eye_interior_changes"]==metrics["protected_changes"]==metrics["outside_support_changes"]==0
    assert (fields["lashes"]>0).any()
    for field in fields.values():
        assert np.isfinite(field).all() and field.min()>=0 and field.max()<=1


def test_only_eye_rim_may_change_not_semantic_core(synthetic,points):
    source,labels=synthetic
    result,_,_=painter.render(source,labels,points)
    core=painter.cv2.erode(np.isin(labels,(4,5)).astype(np.uint8),np.ones((3,3),np.uint8))>0
    assert np.array_equal(source[core],result[core])
    assert np.array_equal(source[labels==10],result[labels==10])
    assert np.array_equal(source[labels==2],result[labels==2])


@pytest.fixture
def local_plan(tmp_path,monkeypatch,synthetic):
    source,labels=synthetic
    monkeypatch.setattr(alignment,"ROOT",tmp_path)
    def save(name,data):
        path=tmp_path/name;path.write_bytes(data)
        return name,alignment.base.digest(path)
    image,sha=save("source.png",b"test-source")
    mapping,mhash=save("labels.png",b"test-map")
    model,msha=save("model.task",b"test-model")
    helper,hsha=save("helper.py",b"test-helper")
    plan={"experiment":"MAKEUP-ALIGN-001","case_count":4,"mediapipe":"0.10.33",
      "training":False,"lora_active":False,"production_enabled":False,
      "new_model_inference":"PRETRAINED_LANDMARK_DETECTION_ONLY","chains":alignment.CHAINS,
      "subjects":[{"id":str(i),"source":image,"sha256":sha,"previous":image,"previous_sha256":sha} for i in range(4)],
      "maps":[{"id":str(i),"labels":mapping,"sha256":mhash} for i in range(4)],
      "model":{"path":model,"sha256":msha},"helpers":[{"path":helper,"sha256":hsha}]}
    path=tmp_path/"plan.json";path.write_text(json.dumps(plan))
    return path,plan


@pytest.mark.parametrize("flag",["training","lora_active","production_enabled","new_model_inference"])
def test_incorrect_scope_flags_rejected(local_plan,flag):
    path,plan=local_plan;plan[flag]=True;path.write_text(json.dumps(plan))
    with pytest.raises(ValueError,match="scope"):
        alignment.load_plan(path)


@pytest.mark.parametrize("asset",["model.task","source.png","labels.png","helper.py"])
def test_model_source_map_helper_tampering_rejected(local_plan,asset):
    path,_=local_plan
    assert alignment.load_plan(path)["case_count"]==4
    (path.parent/asset).write_bytes(b"tampered")
    with pytest.raises(ValueError,match="differ"):
        alignment.load_plan(path)


def test_path_escape_rejected(local_plan):
    path,plan=local_plan;plan["model"]["path"]="../outside.task"
    path.write_text(json.dumps(plan))
    with pytest.raises(ValueError,match="escapes"):
        alignment.load_plan(path)


def test_existing_output_not_overwritten(local_plan,tmp_path):
    path,_=local_plan
    with pytest.raises(ValueError,match="Preserve"):
        alignment.detect(path,tmp_path)
    with pytest.raises(ValueError,match="Preserve"):
        painter.run(path,tmp_path,tmp_path)


def test_unreviewed_alignment_not_rendered(local_plan,tmp_path):
    path,_=local_plan
    folder=tmp_path/"alignment";folder.mkdir()
    (folder/"report.json").write_text("{}")
    (folder/"visual-review.json").write_text("{}")
    with pytest.raises((ValueError,KeyError)):
        painter.run(path,folder,tmp_path/"new-output")
    assert not (tmp_path/"new-output").exists()

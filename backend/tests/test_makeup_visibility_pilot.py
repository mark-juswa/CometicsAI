"""Offline non-lip comparison: preserve the prior mouth, protect source anatomy."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import numpy as np
import pytest
from test_makeup_source_render import synthetic

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts import makeup_visibility_pilot as pilot


@pytest.fixture
def profiles():
    return json.loads((ROOT/"data/makeup/MAKEUP-VISIBILITY-001/plan.json").read_text())["profiles"]


@pytest.mark.parametrize("style",pilot.STYLES)
def test_nonlip_change_preserves_entire_previous_mouth_and_inputs(synthetic,profiles,style):
    source,labels=synthetic
    previous=source.copy()
    _,protected,mouth=pilot.regions(labels)
    previous[mouth]=[180,25,90]
    originals=(source.copy(),previous.copy(),labels.copy())
    result,fields,metrics=pilot.render(source,previous,labels,profiles[style])
    assert metrics["nonlip_changed_pixels"]>100
    assert metrics["lip_mouth_changed_pixels"]==0
    assert metrics["protected_changed_pixels"]==0
    assert metrics["outside_allowed_changed_pixels"]==0
    assert np.array_equal(result[mouth],previous[mouth])
    assert np.array_equal(result[protected],previous[protected])
    assert np.array_equal(result[:120],previous[:120])
    for value,before in zip((source,previous,labels),originals):
        assert np.array_equal(value,before)
    again=pilot.render(source,previous,labels,profiles[style])[0]
    assert np.array_equal(result,again)
    support=np.logical_or.reduce([field>0 for field in fields.values()])
    assert np.array_equal(result[~support],previous[~support])
    delta=pilot.base.lab(result)-pilot.base.lab(source)
    nonlip=(labels==1)&~mouth
    # Permit RGB8 round-trip error after the bounded Lab edit.
    assert delta[:,:,0][nonlip].min()>=-16.6
    assert delta[:,:,0][nonlip].max()<=2.6
    assert np.linalg.norm(delta[:,:,1:],axis=2)[nonlip].max()<=41.5


@pytest.mark.parametrize("key,value",[
    ("shadow_opacity",float("nan")),("crease_opacity",1.1),
    ("liner_darkening",26),("blush_opacity",.26),("lower_opacity",.31),
    ("shadow_rgb",[256,0,0]),("crease_rgb",[True,0,0]),("extra",1)])
def test_invalid_profile_rejected(profiles,key,value):
    profile=deepcopy(profiles["soft_glam"]);profile[key]=value
    with pytest.raises(ValueError):
        pilot.check_profile(profile)


@pytest.mark.parametrize("label",[4,5,6,7,"all_lips"])
def test_missing_anatomy_fails_closed(synthetic,label):
    _,labels=synthetic
    labels=labels.copy();labels[np.isin(labels,(11,12)) if label=="all_lips" else labels==label]=1
    with pytest.raises(ValueError):
        pilot.regions(labels)


def test_invalid_image_contract_rejected(synthetic,profiles):
    source,labels=synthetic
    for previous in (source[:-1],source.astype(np.float32)):
        with pytest.raises(ValueError):
            pilot.render(source,previous,labels,profiles["soft_glam"])


def test_frozen_plan_scope_and_duplicate_guards(tmp_path):
    plan=json.loads((ROOT/"data/makeup/MAKEUP-VISIBILITY-001/plan.json").read_text())
    path=tmp_path/"plan.json"
    path.write_text(json.dumps(plan))
    assert pilot.load_plan(path)["case_count"]==12
    plan["cases"][1]=deepcopy(plan["cases"][0])
    path.write_text(json.dumps(plan))
    with pytest.raises(ValueError,match="Duplicate"):
        pilot.load_plan(path)
    plan["production_enabled"]=True
    path.write_text(json.dumps(plan))
    with pytest.raises(ValueError,match="scope"):
        pilot.load_plan(path)


def test_existing_evidence_not_overwritten(tmp_path,monkeypatch):
    monkeypatch.setattr(pilot,"load_plan",lambda path:{})
    with pytest.raises(ValueError,match="New visibility"):
        pilot.prepare(tmp_path/"unused.json",tmp_path)
    (tmp_path/"report.json").write_text("{}")
    with pytest.raises(ValueError,match="overwrite"):
        pilot.apply(tmp_path/"unused.json",tmp_path)

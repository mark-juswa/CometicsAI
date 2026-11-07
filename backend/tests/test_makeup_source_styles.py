"""Seven-style extension: local finish bounds and original-photo preservation."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts import makeup_source_styles as extra
from test_makeup_source_render import synthetic


@pytest.fixture
def profiles():
    return json.loads((ROOT/"data/makeup/MAKEUP-RENDER-002/plan.json").read_text())["profiles"]


@pytest.mark.parametrize("style",extra.STYLES)
def test_all_seven_profiles_preserve_protected_source(synthetic,profiles,style):
    source,labels=synthetic
    before=source.copy()
    result,fields,metrics=extra.render(source,labels,profiles[style])
    allowed=extra.support(fields,profiles[style])
    protected=~np.isin(labels,(1,11,12))
    assert np.array_equal(source,before)
    assert np.array_equal(result[~allowed],source[~allowed])
    assert np.array_equal(result[protected],source[protected])
    assert np.array_equal(result[60:120,180:300],source[60:120,180:300])
    assert metrics["outside_cosmetic_changed_pixels"]==0
    assert metrics["protected_changed_pixels"]==0
    assert metrics["changed_pixels"]>0
    again,_,_=extra.render(source,labels,profiles[style])
    assert np.array_equal(result,again)
    assert metrics["supported_description"]==profiles[style]["description"]
    assert metrics["unsupported_features"]==profiles[style]["unsupported_features"]


def blank(profile):
    p=deepcopy(profile)
    for key in ("lip","shadow","liner","blush"):
        p["pigment"][key+"_opacity"]=0
    for key in ("lower_eye_opacity","cheek_highlight","lip_gloss","lip_matte","gold_sheen"):
        p[key]=0
    return p


def test_no_effect_configuration_is_exact_source(synthetic,profiles):
    source,labels=synthetic
    p=blank(profiles["dewy_peach"])
    result,_,metrics=extra.render(source,labels,p)
    assert np.array_equal(source,result) and metrics["changed_pixels"]==0


@pytest.mark.parametrize("finish,region",[
    ("cheek_highlight","cheek_highlight"),("lip_gloss","lip"),
    ("lip_matte","lip"),("gold_sheen","gold"),("lower_eye_opacity","lower_eye")])
def test_finish_never_changes_unrelated_regions(synthetic,profiles,finish,region):
    source,labels=synthetic
    p=blank(profiles["dewy_peach"])
    p[finish]=.3
    result,fields,metrics=extra.render(source,labels,p)
    assert np.array_equal(source[fields[region]==0],result[fields[region]==0])
    assert metrics["changed_pixels"]>0
    assert metrics["protected_changed_pixels"]==0


@pytest.mark.parametrize("field,value",[
    ("cheek_highlight",1.0),("lip_matte",2),("gold_sheen",float("nan")),
    ("eye_shape","whole_face"),("lower_eye_opacity",-.1)])
def test_unbounded_or_unknown_finishes_rejected(profiles,field,value):
    p=deepcopy(profiles["matte_nude"]);p[field]=value
    with pytest.raises(ValueError):extra.check_profile(p)


def test_missing_eye_still_fails_closed(synthetic,profiles):
    source,labels=synthetic
    bad=labels.copy();bad[bad==4]=1
    with pytest.raises(ValueError):extra.render(source,bad,profiles["smoky_glam"])


@pytest.fixture
def local_plan(tmp_path,monkeypatch,synthetic):
    monkeypatch.setattr(extra,"ROOT",tmp_path)
    plan=json.loads((ROOT/"data/makeup/MAKEUP-RENDER-002/plan.json").read_text())
    source,labels=synthetic
    maps=[]
    for subject in plan["subjects"]:
        sid=subject["id"]
        p=tmp_path/(sid+".png");Image.fromarray(source).save(p)
        subject["source"]=p.name;subject["sha256"]=extra.base.digest(p)
        m=tmp_path/(sid+"-labels.png");Image.fromarray(labels).save(m)
        maps.append({"id":sid,"labels":m.name,"labels_sha256":extra.base.digest(m)})
    plan["cached_maps"]=maps
    old=tmp_path/"baseline-plan.json"
    old.write_text(json.dumps({"subjects":plan["subjects"],"parser":plan["parser"]}))
    report=tmp_path/"baseline-report.json";report.write_text("{}")
    runner=tmp_path/"baseline-renderer.py";runner.write_text("# immutable fixture")
    for key,p in (("baseline_plan",old),("baseline_report",report),("baseline_renderer",runner)):
        plan[key]=p.name;plan[key+"_sha256"]=extra.base.digest(p)
    path=tmp_path/"plan.json";path.write_text(json.dumps(plan))
    return path,plan


@pytest.mark.parametrize("flag",["production_enabled","training","lora_active","project_trained_generator_used"])
def test_rendering_not_misrepresented_as_trained_generation(local_plan,flag):
    path,plan=local_plan;plan[flag]=True;path.write_text(json.dumps(plan))
    with pytest.raises(ValueError):extra.load_plan(path)


@pytest.mark.parametrize("kind",["source","labels","baseline"])
def test_tampered_references_rejected(local_plan,kind):
    path,plan=local_plan
    assert extra.load_plan(path)["case_count"]==28
    if kind=="source":target=plan["subjects"][0]["source"]
    elif kind=="labels":target=plan["cached_maps"][0]["labels"]
    else:target=plan["baseline_report"]
    (path.parent/target).write_bytes(b"changed")
    with pytest.raises(ValueError):extra.load_plan(path)


def test_no_overwrite_of_complete_or_partial_outputs(local_plan,tmp_path):
    path,_=local_plan;out=tmp_path/"existing";out.mkdir()
    with pytest.raises(ValueError,match="New extension"):extra.prepare(path,out)
    marker=out/"partial-rendered.png";marker.write_bytes(b"preserve")
    with pytest.raises(ValueError,match="overwrite"):extra.apply(path,out)
    assert marker.read_bytes()==b"preserve"

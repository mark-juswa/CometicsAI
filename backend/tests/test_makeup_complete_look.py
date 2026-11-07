"""Safety tests for the rejected offline complete-look prototype, not realism tests."""
import json
from pathlib import Path
import sys

import numpy as np
import pytest
from test_makeup_source_render import synthetic

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts import makeup_complete_look as pilot


def test_deterministic_and_no_mutation(synthetic):
    source,labels=synthetic
    before=source.copy();maps=labels.copy()
    result,fields,metrics=pilot.render(source,labels)
    again,_,_=pilot.render(source,labels)
    assert np.array_equal(result,again)
    assert np.array_equal(source,before)
    assert np.array_equal(labels,maps)
    assert metrics["changed_pixels"]>100
    assert metrics["outside_allowed_changes"]==0
    assert metrics["protected_changes"]==0
    assert np.array_equal(result[:100],source[:100])


@pytest.mark.parametrize("region",[(4,5),(2,),(10,),(0,3,8,9,13,14,15,16,17,18)])
def test_eye_interior_nose_mouth_and_nonface_exact(synthetic,region):
    source,labels=synthetic
    result,_,_=pilot.render(source,labels)
    mask=np.isin(labels,region)
    assert np.array_equal(result[mask],source[mask])


def test_effects_restricted_to_explicit_cosmetics(synthetic):
    source,labels=synthetic
    result,fields,_=pilot.render(source,labels)
    support=np.logical_or.reduce([f>0 for f in fields.values()])
    assert np.array_equal(result[~support],source[~support])
    for name,field in fields.items():
        assert np.isfinite(field).all() and field.min()>=0 and field.max()<=1
        if name not in ("lip","brow"):
            assert not (field[labels!=1]>0).any()
    assert (fields["lashes"]>0).any()
    assert (fields["brow"]>0).any()


@pytest.mark.parametrize("label",[4,5,6,7])
def test_missing_eye_or_brow_fails_closed(synthetic,label):
    _,labels=synthetic
    bad=labels.copy();bad[bad==label]=1
    with pytest.raises(ValueError):
        pilot.fields_for(bad)


@pytest.mark.parametrize("flag",["production_enabled","training","lora_active","new_model_inference"])
def test_false_model_and_deployment_flags_enforced(tmp_path,flag):
    plan=json.loads((ROOT/"data/makeup/MAKEUP-COMPLETE-001/plan.json").read_text())
    plan[flag]=True
    path=tmp_path/"plan.json";path.write_text(json.dumps(plan))
    with pytest.raises(ValueError,match="scope"):
        pilot.load_plan(path)


def test_existing_evidence_refused(tmp_path):
    with pytest.raises(ValueError,match="new directory"):
        pilot.run(ROOT/"data/makeup/MAKEUP-COMPLETE-001/plan.json",tmp_path)


def test_invalid_rgb_contract(synthetic):
    source,labels=synthetic
    with pytest.raises(ValueError,match="512 RGB8"):
        pilot.render(source.astype(np.float32),labels)

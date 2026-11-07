"""Source material regressions. These do not approve cosmetic appearance."""
from pathlib import Path
from functools import lru_cache
from hashlib import sha256
import json,sys
import cv2,numpy as np,pytest
from PIL import Image

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.makeup_materials import (STYLE_MATERIALS,guided_probability,source_lip_matte,
    lip_material,reference_eye_materials,fit_eye_material,source_finish)
from scripts.makeup_source_layers import catalog,apply_counterfactual
from scripts.makeup_surface_application import lip_coverage,palette


@lru_cache(maxsize=6)
def material_case(sid='035149',style='bold_evening_glam'):
    workspace=ROOT/'artifacts/makeup-refinement-20261105'
    if not (workspace/'catalog-review/report.json').is_file():
        pytest.skip('Private local material review artifacts unavailable')
    base=ROOT/'artifacts/makeup-local-transfer-20261104/catalog-review'
    raw=ROOT/'artifacts/makeup-local-transfer-20261104/catalog-01'
    plan=json.loads((base/'plan.json').read_text());s=next(r for r in plan['sources'] if r['id']==sid)
    guide=next(r for r in plan['guides'] if r['id']==style)
    prep=next(r for r in json.loads((raw/'prepared.json').read_text())['guides'] if r['style_id']==style)
    rgb=lambda path:np.array(Image.open(path).convert('RGB'))
    a,b=rgb(ROOT/s['source']),rgb(ROOT/guide['reference'])
    labels,refs=np.array(Image.open(ROOT/s['labels'])),np.array(Image.open(raw/prep['labels']))
    points=json.loads((ROOT/s['points478']).read_text())['points']
    detail=workspace/'detail-reference';record=json.loads((detail/'report.json').read_text())
    context={'lip_probability':np.load(workspace/'lip-probabilities'/(sid+'-lip.npy'),allow_pickle=False),
        'detail_image':rgb(ROOT/record['source']),'detail_labels':np.array(Image.open(detail/'labels.png')),
        'detail_points68':np.load(detail/'points68.npy',allow_pickle=False),
        'reference_points68':np.load(raw/prep['points68'],allow_pickle=False)}
    with np.load(raw/'results'/(sid+'-'+style+'-fields.npz'),allow_pickle=False) as f:
        saved={key:f[key].copy() for key in f.files}
    return a,b,labels,refs,points,context,saved


def test_every_existing_and_expanded_style_has_material_intent():
    assert set(STYLE_MATERIALS)=={r['id'] for r in catalog()}
    assert len(STYLE_MATERIALS)==13


def test_guided_filter_keeps_constant_confidence_without_changing_source():
    a=np.random.default_rng(19).integers(0,256,(512,512,3),dtype=np.uint8);before=a.copy()
    p=np.full((512,512),.7,np.float32)
    assert np.allclose(guided_probability(a,p),.7,atol=2e-5)
    assert np.array_equal(a,before) and np.all(p==.7)


@pytest.mark.parametrize('value',[np.nan,np.inf,-.01,1.01])
def test_invalid_confidence_refused(value):
    a=np.zeros((512,512,3),np.uint8);p=np.zeros((512,512),np.float32);p[1,1]=value
    with pytest.raises(ValueError):guided_probability(a,p)


def test_source_confidence_does_not_spill_past_validated_lip_anatomy():
    a,b,l,r,p,c,_=material_case()
    old,support,_=lip_coverage(l,p)
    alpha,refined_support,_=source_lip_matte(a,l,p,c['lip_probability'])
    assert np.array_equal(refined_support,support)
    assert np.all(alpha[~support]==0)
    distance=cv2.distanceTransform(support.astype(np.uint8),cv2.DIST_L2,5)
    old_hole=support&(distance<=1)
    assert np.all(old[old_hole]==0) and np.count_nonzero(alpha[old_hole]>.2)>20
    assert np.all(alpha[old_hole]<1)  # soft coverage, not a filled hard polygon


def test_insufficient_source_probability_fails_closed():
    a,b,l,r,p,c,_=material_case()
    with pytest.raises(ValueError,match='Insufficient'):
        source_lip_matte(a,l,p,np.zeros((512,512),np.float32))


def test_identical_palette_is_exact_lip_noop():
    a,b,l,r,p,c,_=material_case()
    output,_,meta=lip_material(a,a.copy(),l,l.copy(),p,c['lip_probability'])
    assert np.array_equal(output,a) and meta['palette_no_change']


def test_lip_cannot_copy_unrelated_reference_skin_and_geometry():
    a,b,l,r,p,c,_=material_case()
    altered=b.copy();altered[~np.isin(r,(11,12))]=255-altered[~np.isin(r,(11,12))]
    first,_,_=lip_material(a,b,l,r,p,c['lip_probability'])
    second,_,_=lip_material(a,altered,l,r,p,c['lip_probability'])
    assert np.array_equal(first,second)
    assert np.array_equal(first[~np.isin(l,(11,12))],a[~np.isin(l,(11,12))])


@pytest.mark.parametrize('sid,style',[('035149','bold_evening_glam'),('006553','classic_red_lip'),('054109','natural_makeup')])
def test_full_dose_lip_hue_error_improves_over_frozen_offset(sid,style):
    a,b,l,r,p,c,_=material_case(sid,style)
    result,alpha,_=lip_material(a,b,l,r,p,c['lip_probability'])
    before=np.array(Image.open(ROOT/'artifacts/makeup-local-transfer-20261104/catalog-review/results'/(sid+'-'+style+'.png')))
    chosen=palette(b,r);target=np.arctan2(chosen[2],chosen[1]);core=alpha>.95
    def error(value):
        lab=cv2.cvtColor(value.astype(np.float32)/255,cv2.COLOR_RGB2LAB)
        hue=np.arctan2(lab[:,:,2][core],lab[:,:,1][core])
        return np.median(np.abs(np.angle(np.exp(1j*(hue-target)))))
    assert error(result)<error(before)


def test_observed_eye_mattes_and_fitting_leave_inputs_and_eye_core_intact():
    a,b,l,r,p,c,_=material_case()
    detail=c['detail_image'];before=detail.copy();points=c['detail_points68'].copy()
    observed=reference_eye_materials(detail,c['detail_labels'],points)
    for kind,field in observed.items():
        fitted,core=fit_eye_material(field,p,points,l,kind,a,detail)
        assert np.isfinite(fitted).all() and fitted.min()>=0 and fitted.max()<=1
        assert not np.any(fitted[core])
        assert not np.any(fitted[~np.isin(l,(1,4,5))])
    assert np.array_equal(detail,before) and np.array_equal(points,c['detail_points68'])


@pytest.mark.parametrize('strength',[-3,3])
def test_skin_finish_is_local_bounded_and_does_not_shift_median_complexion(strength):
    a,b,l,r,p,c,_=material_case('056266','dewy_peach')
    output,weight=source_finish(a,a,l,np.ones((512,512),np.float32),strength)
    lab=lambda x:cv2.cvtColor(x.astype(np.float32)/255,cv2.COLOR_RGB2LAB)
    change=lab(output)-lab(a);skin=l==1
    assert np.array_equal(output[weight==0],a[weight==0])
    assert np.array_equal(output[~skin],a[~skin])
    assert np.max(np.abs(change[:,:,0]))<3.3
    assert np.abs(np.median(change[:,:,0][skin]))<.05
    assert np.count_nonzero(weight)>0 and np.count_nonzero(weight)<.11*np.count_nonzero(skin)


@pytest.mark.parametrize('strength',[float('nan'),float('inf'),3.01])
def test_invalid_skin_finish_refused(strength):
    a,b,l,r,p,c,_=material_case()
    with pytest.raises(ValueError):
        source_finish(a,a,l,np.ones((512,512),np.float32),strength)


@pytest.mark.parametrize('sid,style',[('054109','exp_manga_lash'),('056266','exp_icy_silver'),('035149','bold_evening_glam')])
def test_frozen_material_result_reproduces_without_mutating_inputs(sid,style):
    a,b,l,r,p,c,f=material_case(sid,style)
    arrays=[a,b,l,r,*c.values(),*f.values()]
    hashes=[sha256(np.ascontiguousarray(v).tobytes()).hexdigest() for v in arrays]
    output,_,metrics=apply_counterfactual(a,b,l,r,p,f['baseline'],f['edited'],{k:f[k] for k in ('eye','cheek')},style,materials=c)
    expected=np.array(Image.open(ROOT/'artifacts/makeup-refinement-20261105/catalog-review/results'/(sid+'-'+style+'.png')))
    assert np.array_equal(output,expected)
    assert metrics['protected_changed_pixels']==metrics['eye_core_changed_pixels']==metrics['brow_changed_pixels']==0
    assert metrics['source_spatially_smoothed'] is False
    assert hashes==[sha256(np.ascontiguousarray(v).tobytes()).hexdigest() for v in arrays]

"""Automatic cosmetic surface controls, not claims of full visual acceptance."""
from pathlib import Path
import sys,json

import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.makeup_source_layers import automatic_support,apply_counterfactual,pigment_projection
from scripts.makeup_surface_application import apply_lipstick
from scripts.makeup_local_features import LocalCosmeticFeatures,prepare_inputs,array_hash
from test_makeup_surface_application import fixture


def geometry(index=0):
    data=fixture(index)
    subject=data[2]['subject_id']
    receipt=json.loads((ROOT/'artifacts/makeup-render-20261030/stable-makeup-pilot/controls-receipt.json').read_text(encoding='utf-8'))
    coarse=np.asarray(next(row for row in receipt['subjects'] if row['id']==subject)['landmarks'],np.float32)[0]
    fields=automatic_support(data[6],data[8],coarse)
    return data,coarse,fields


def test_uniform_whitening_is_not_cosmetic_pigment():
    data,_,fields=geometry()
    _,_,_,_,original,_,labels,_,points=data
    baseline=np.full((256,256,3),.3,np.float32)
    brighter=np.full_like(baseline,.6)
    output,_,metrics=apply_counterfactual(original,original,labels,labels,points,baseline,brighter,fields,'natural_makeup')
    assert np.array_equal(output,original)
    assert metrics['maximum_cosmetic_density']==0


@pytest.mark.parametrize('style',['natural_makeup','smoky_glam','exp_icy_silver'])
def test_identical_decoder_fields_and_identical_reference_leave_source_exact(style):
    data,_,fields=geometry()
    _,_,_,_,original,_,labels,_,points=data
    baseline=np.full((256,256,3),.5,np.float32)
    output,_,_=apply_counterfactual(original,original,labels,labels,points,baseline,baseline.copy(),fields,style)
    assert np.array_equal(output,original)


@pytest.mark.parametrize('index',range(6))
def test_retained_lip_and_protected_source_survive_visible_eye_cheek_material(index):
    data,_,fields=geometry(index)
    _,_,_,_,original,reference,labels,refs,points=data
    baseline=np.full((256,256,3),.6,np.float32)
    edited=baseline.copy();edited[:,:,1]*=.8;edited[:,:,2]*=.9
    output,masks,metrics=apply_counterfactual(original,reference,labels,refs,points,baseline,edited,fields,data[2]['style_id'])
    lip,alpha,_=apply_lipstick(original,reference,labels,refs,points)
    assert np.array_equal(output[alpha>0],lip[alpha>0])
    assert np.array_equal(output[~np.isin(labels,(1,11,12))],original[~np.isin(labels,(1,11,12))])
    skin=(fields['eye']>0)|(fields['cheek']>0)
    assert np.all(output[skin]<=original[skin])
    assert metrics['region_changed_pixels']['eye']>0
    assert metrics['region_changed_pixels']['cheek']>0
    assert metrics['protected_changed_pixels']==metrics['brow_changed_pixels']==metrics['eye_interior_changed_pixels']==0


def test_cyan_complexion_removal_cannot_become_rose_blush():
    # Actual failed direction: red is removed more than blue, making warm skin gray.
    bad=np.full((12,12,3),[.6,.3,0],np.float32)
    corrected=pigment_projection(bad,[175,77,83])
    assert np.all(corrected==0)
    good=np.full((12,12,3),[0,.6,.4],np.float32)
    corrected=pigment_projection(good,[175,77,83])
    assert np.all(corrected[:,:,0]==0)
    assert np.all(corrected[:,:,1:]>0)


def test_sheer_style_keeps_less_lip_pigment_while_classic_red_retains_its_component():
    data,_,fields=geometry(1)
    _,_,_,_,original,reference,labels,refs,points=data
    baseline=np.full((256,256,3),.5,np.float32)
    red,masks,_=apply_counterfactual(original,reference,labels,refs,points,baseline,baseline.copy(),fields,'classic_red_lip')
    sheer,_,_=apply_counterfactual(original,reference,labels,refs,points,baseline,baseline.copy(),fields,'no_makeup_makeup')
    region=masks['lip']>0
    assert np.mean(np.abs(sheer.astype(float)-original)[region])<np.mean(np.abs(red.astype(float)-original)[region])


def test_source_fields_never_mutate_input_landmarks():
    data,coarse,_=geometry()
    points=np.asarray(data[8],np.float32)
    before,coarse_before=points.copy(),coarse.copy()
    automatic_support(data[6],points,coarse)
    assert np.array_equal(points,before) and np.array_equal(coarse,coarse_before)


def test_strong_eye_field_fades_before_the_original_brow_boundary():
    from scripts.makeup_source_layers import eyelid_taper
    from scripts.makeup_alignment_pilot import CHAINS
    data,_,_=geometry()
    points=np.asarray(data[8],np.float32)
    field=eyelid_taper(points)
    for side in ('right','left'):
        brow=points[CHAINS[side+'_brow_lower'],:2]*512
        upper=points[CHAINS[side+'_upper'],:2]*512
        x=int(np.mean(upper[:,0]))
        brow=brow[np.argsort(brow[:,0])]
        y=int(np.floor(np.interp(x,brow[:,0],brow[:,1])))
        assert field[y,x]<.02


@pytest.mark.parametrize('failure',['nan','protected','style'])
def test_invalid_or_unsafe_automatic_fields_are_refused(failure):
    data,_,fields=geometry()
    _,_,_,_,original,reference,labels,refs,points=data
    base=np.full((256,256,3),.5,np.float32)
    style='natural_makeup'
    if failure=='nan':base[0,0,0]=np.nan
    elif failure=='protected':fields['eye'][0,0]=1
    else:style='invented'
    with pytest.raises(ValueError):
        apply_counterfactual(original,reference,labels,refs,points,base,base.copy(),fields,style)


def test_cpu_model_same_reference_and_style_switch_do_not_mutate_cached_content():
    folder=ROOT/'artifacts/makeup-local-transfer-20261104'
    if not (folder/'sow_pyramid_a5_e3d2_remapped.pth').is_file():
        pytest.skip('Private pinned offline provider unavailable')
    data,coarse,fields=geometry()
    _,_,_,_,original,reference,labels,refs,points=data
    ref_points=np.load(folder/'probe-reference-68.npy',allow_pickle=False)
    provider=LocalCosmeticFeatures(folder)
    coverage=np.maximum(fields['eye'],fields['cheek'])
    a,b,_=provider.counterfactual(original,labels,coarse,reference,refs,ref_points,coverage)
    first=b.copy()
    key,content=provider.encode(original,labels,coarse)
    saved=[value.clone() for value in content[0]]
    own_a,own_b,_=provider.counterfactual(original,labels,coarse,original,labels,coarse,coverage)
    output,_,_=apply_counterfactual(original,original,labels,labels,points,own_a,own_b,fields,'natural_makeup')
    assert np.array_equal(output,original)
    _,b,_=provider.counterfactual(original,labels,coarse,reference,refs,ref_points,coverage)
    assert np.array_equal(b,first)
    assert all(provider.torch.equal(x,y) for x,y in zip(saved,content[0]))


def test_preprocessing_preserves_true_68_topology_and_model_mask_semantics():
    import torch
    data,coarse,_=geometry()
    values=prepare_inputs(data[4],data[6],coarse,torch)
    assert [tuple(v.shape) for v in values]==[(1,3,256,256),(1,2,256,256),(1,136,256,256),(1,68,2)]
    assert torch.isfinite(values[2]).all()
    with pytest.raises(ValueError,match='true68'):
        prepare_inputs(data[4],data[6],np.zeros((478,3)),torch)

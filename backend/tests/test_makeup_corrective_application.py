"""Candidate admission and real response binding, with no GPU generation."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts import package_makeup_corrective_application as package
from scripts import makeup_corrective_application_probe as probe


@pytest.fixture
def accepted_review():
    review = json.loads((package.RETURN / 'human-model-review-01/makeup-corrective-model-review.json').read_text())
    bindings = json.loads((package.RETURN / 'model-review/bindings.json').read_text())
    return review, bindings


def test_acceptance_is_for_exact_model_outputs_and_not_production(accepted_review):
    package.check_review(*accepted_review)
    assert accepted_review[0]['production_approved'] is False


@pytest.mark.parametrize('change', ['duplicate','missing','pending','source','output','caption','checkpoint','production'])
def test_invalid_review_cannot_admit_candidate(accepted_review, change):
    review, bindings = deepcopy(accepted_review)
    if change == 'duplicate':
        review['cases'][1] = review['cases'][0]
    elif change == 'missing':
        review['cases'].pop()
    elif change == 'pending':
        review['cases'][0]['verdict'] = 'PENDING'
    elif change == 'production':
        review['production_approved'] = True
    else:
        key = {'source':'source_sha256','output':'corrective_sha256','caption':'caption','checkpoint':'checkpoint_sha256'}[change]
        review['cases'][0][key] = 'changed'
    with pytest.raises(ValueError):
        package.check_review(review, bindings)


def test_candidate_uses_exact_thirteen_accepted_captions_without_changing_legacy_contract(tmp_path):
    from app import makeup_contract as legacy
    frozen = legacy.ADAPTER_SHA256, dict(legacy.PROMPTS)
    catalog = json.loads((package.DATA/'catalog.json').read_text())
    contract, presets = package.candidate_contract(catalog)
    target = tmp_path/package.PRESETS_PATH
    target.parent.mkdir(parents=True)
    target.write_bytes(presets)
    filename=tmp_path/package.CONTRACT_PATH
    namespace={'__file__':str(filename)}
    exec(compile(contract,str(filename),'exec'),namespace)
    assert namespace['PROMPTS']=={s['id']:s['caption'] for s in catalog['styles']}
    assert namespace['ADAPTER_SHA256']==package.CHECKPOINT_SHA
    assert namespace['PRESETS_SHA256']==sha256(presets).hexdigest()
    assert (legacy.ADAPTER_SHA256,legacy.PROMPTS)==frozen


@pytest.mark.parametrize('key,bad', [('prompt','wrong caption'),('steps',4),('seed',99),('guidance',1),
                                    ('adapter_sha256','old'),('lora_active',False)])
def test_application_probe_rejects_generation_drift_before_accepting_png(key,bad):
    candidate={'adapter_id':'MAKEUP-001-CORRECTIVE-001','checkpoint_sha256':package.CHECKPOINT_SHA,
               'base_model_id':'base','base_model_revision':'pinned','prompt_presets_sha256':'prompts'}
    metadata={'feature':'makeup','style_id':'soft_glam','adapter_id':candidate['adapter_id'],
              'adapter_sha256':candidate['checkpoint_sha256'],'base_model_id':'base','base_model_revision':'pinned',
              'prompt_presets_sha256':'prompts','lora_active':True,'steps':20,'seed':1977,'guidance':4.0,'prompt':'accepted caption'}
    metadata[key]=bad
    payload={'status':'completed','generator':'flux2_klein_base_makeup001_corrective001','metadata':metadata}
    with pytest.raises(ValueError,match='accepted corrective'):
        probe.validate_makeup(payload,'soft_glam',candidate,'accepted caption')

"""Backup staging integrity and deliberate cutover, no cloud or GPU operations."""
import base64
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from urllib.error import HTTPError

import pytest

from scripts.kaggle_backup_update import install_cpu_update
from scripts.kaggle_backup_controls import backup_connect, backup_validate


def payload():
    raw = b'answer = 42\n'
    return {'backend/app/example.py':base64.b64encode(raw).decode()}, {'backend/app/example.py':sha256(raw).hexdigest()}


def test_cpu_installer_validates_every_member_before_writing(tmp_path):
    data, inventory = payload()
    data['backend/app/bad.py'] = base64.b64encode(b'bad').decode()
    inventory['backend/app/bad.py'] = '0' * 64
    with pytest.raises(ValueError, match='hash differs'):
        install_cpu_update(tmp_path, data, inventory)
    assert not (tmp_path / 'cpu-src').exists()


@pytest.mark.parametrize('path', ['../outside.py', 'C:/outside.py', 'backend\\bad.py'])
def test_cpu_installer_rejects_path_escape(tmp_path, path):
    data, inventory = payload()
    data = {path:next(iter(data.values()))}
    inventory = {path:next(iter(inventory.values()))}
    with pytest.raises(ValueError, match='Unsafe'):
        install_cpu_update(tmp_path, data, inventory)


def test_cpu_installer_preserves_old_receipt(tmp_path):
    data, inventory = payload()
    install_cpu_update(tmp_path, data, inventory)
    before = (tmp_path / 'photo-check-update.json').read_bytes()
    with pytest.raises(RuntimeError, match='already installed'):
        install_cpu_update(tmp_path, data, inventory)
    assert (tmp_path / 'photo-check-update.json').read_bytes() == before


def test_run_all_cannot_register_without_visual_acceptance(tmp_path):
    with pytest.raises(RuntimeError, match='explicitly confirm'):
        backup_connect(tmp_path, 'https://beautycore-demo.onrender.com')
    assert not list(tmp_path.iterdir())


def test_distributed_notebook_keeps_environment_guard_and_manual_connection():
    import ast
    root = Path(__file__).resolve().parents[2]
    book = json.loads((root / 'client/beautycore_kaggle_backup_20261113.ipynb').read_bytes())
    for index, cell in enumerate(book['cells']):
        if cell['cell_type'] == 'code':
            compile(''.join(cell['source']), f'cell-{index}', 'exec')
            assert cell['outputs'] == []
    tree = ast.parse(''.join(book['cells'][1]['source']))
    guard = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'check_host')
    assert all(name in ast.unparse(guard) for name in ('python', 'torch', 'cuda', 'gpu'))
    runner = ''.join(book['cells'][2]['source'])
    assert "BEAUTYCORE_PUBLIC_URL = ''" in runner
    assert 'check_readiness(readiness, STYLE_RELEASE_EXPECTED, BACKUP_CATALOG)' in runner
    assert 'face-detector-load' in runner
    assert 'VISUAL_ACCEPTANCE_CONFIRMED = False' in ''.join(book['cells'][-1]['source'])


def test_negative_validation_does_not_accept_detector_service_failure(tmp_path):
    (tmp_path / 'photo-check-update.json').write_text(json.dumps({'schema':'beautycore-photo-check-update-v1'}))
    calls = []
    def unavailable(request, timeout):
        calls.append(request.full_url)
        raise HTTPError(request.full_url, 503, '', {}, BytesIO(b'{"detail":"Photo checking is temporarily unavailable. Please try again later."}'))
    with pytest.raises(RuntimeError, match='no retry'):
        backup_validate(tmp_path, key='x'*32, opener=unavailable)
    assert len(calls) == 1
    assert not (tmp_path / 'backup-validation.json').exists()


def test_subject_checks_require_exact_public_rejections(tmp_path):
    from app.photo_suitability import MESSAGES
    (tmp_path / 'photo-check-update.json').write_text(json.dumps({'schema':'beautycore-photo-check-update-v1'}))
    calls = []
    def rejected(request, timeout):
        feature = request.full_url.split('/')[4]
        calls.append(feature)
        raise HTTPError(request.full_url, 422, '', {}, BytesIO(json.dumps({'detail':MESSAGES[feature]}).encode()))
    report = backup_validate(tmp_path, key='x'*32, opener=rejected)
    assert set(calls) == {'hairstyle','makeup','nails'}
    assert report['real_generation_verified'] is False
    assert report['website_connected'] is False

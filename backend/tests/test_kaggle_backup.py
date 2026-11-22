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


def test_subject_validation_resolves_the_actual_hosted_gateway_ticket(tmp_path):
    """The hosted facade returns 202 even when the inner handler rejects the photo."""
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from fastapi.testclient import TestClient
    from app.demo_gateway import create_gateway
    from app.photo_suitability import MESSAGES

    (tmp_path / 'photo-check-update.json').write_text(json.dumps({'schema': 'beautycore-photo-check-update-v1'}))
    inner = FastAPI()
    dispatched = []
    @inner.post('/features/{feature}/generate')
    async def reject_subject(feature: str):
        dispatched.append(feature)
        return JSONResponse({'detail': MESSAGES[feature]}, status_code=422)

    calls = []
    secret = 'test-only-backup-gateway-key-0123456789'
    with TestClient(create_gateway(inner, secret)) as client:
        def gateway_opener(request, timeout):
            calls.append((request.get_method(), request.full_url))
            response = client.request(request.get_method(), request.full_url,
                                      headers=dict(request.header_items()), content=request.data)
            if response.status_code >= 400:
                raise HTTPError(request.full_url, response.status_code, '', {}, BytesIO(response.content))
            body = BytesIO(response.content)
            body.status = response.status_code
            return body

        report = backup_validate(tmp_path, key=secret, opener=gateway_opener)
    assert report['status'] == 'SUBJECT_REJECTION_PASS'
    assert dispatched == ['hairstyle', 'makeup', 'nails']
    assert len([method for method, _ in calls if method == 'POST']) == 3
    assert len([method for method, url in calls if method == 'GET' and url.endswith('/result')]) == 3
    assert all(case['wrong_subject_status'] == 422 for case in report['cases'])
    assert all(case['admission_status'] == 202 for case in report['cases'])


def test_admitted_validation_keeps_detector_failure_closed_without_another_post(tmp_path):
    (tmp_path / 'photo-check-update.json').write_text(json.dumps({'schema': 'beautycore-photo-check-update-v1'}))
    identity = '11111111-1111-4111-8111-111111111111'
    calls = []
    def respond(request, timeout):
        calls.append(request)
        if request.get_method() == 'POST':
            body = BytesIO(json.dumps({'job_id': identity, 'status': 'generating'}).encode())
            body.status = 202
            return body
        assert request.headers.get('X-ai-user-id') == 'backup-validation'
        if request.full_url.endswith('/result'):
            raise HTTPError(request.full_url, 503, '', {}, BytesIO(b'{"detail":"Photo checking is temporarily unavailable. Please try again later."}'))
        body = BytesIO(json.dumps({'job_id': identity, 'status': 'failed'}).encode())
        body.status = 200
        return body
    with pytest.raises(RuntimeError, match=r'HTTP 503.*no retry'):
        backup_validate(tmp_path, key='x' * 32, opener=respond)
    assert [request.get_method() for request in calls] == ['POST', 'GET', 'GET']
    assert not (tmp_path / 'backup-validation.json').exists()


@pytest.mark.parametrize('ticket', ['../another/endpoint', 'https://other.test', None])
def test_validation_never_follows_invalid_job_tickets(tmp_path, ticket):
    (tmp_path / 'photo-check-update.json').write_text(json.dumps({'schema': 'beautycore-photo-check-update-v1'}))
    calls = []
    def respond(request, timeout):
        calls.append(request)
        body = BytesIO(json.dumps({'job_id': ticket, 'status': 'generating'}).encode())
        body.status = 202
        return body
    with pytest.raises(RuntimeError, match='Invalid validation job ticket'):
        backup_validate(tmp_path, key='x' * 32, opener=respond)
    assert len(calls) == 1


def test_validation_timeout_uses_reads_only_and_never_replays_admission(tmp_path):
    (tmp_path / 'photo-check-update.json').write_text(json.dumps({'schema': 'beautycore-photo-check-update-v1'}))
    identity = '11111111-1111-4111-8111-111111111111'
    calls, elapsed = [], [0]
    def respond(request, timeout):
        calls.append(request)
        body = BytesIO(json.dumps({'job_id': identity, 'status': 'generating'}).encode())
        body.status = 202 if request.get_method() == 'POST' else 200
        return body
    def sleep(_seconds):
        elapsed[0] += 61
    with pytest.raises(RuntimeError, match='unresolved.*no retry'):
        backup_validate(tmp_path, key='x' * 32, opener=respond, sleep=sleep, clock=lambda: elapsed[0])
    assert [request.get_method() for request in calls] == ['POST', 'GET']
    assert not (tmp_path / 'backup-validation.json').exists()


def test_corrected_notebook_updates_only_validation_and_keeps_connection_deliberate():
    root = Path(__file__).resolve().parents[2]
    old = json.loads((root / 'client/beautycore_kaggle_backup_20261113.ipynb').read_bytes())
    corrected = json.loads((root / 'client/beautycore_kaggle_backup_20261122.ipynb').read_bytes())
    for index, (before, after) in enumerate(zip(old['cells'], corrected['cells'], strict=True)):
        if index != 3:
            assert before == after
        if after['cell_type'] == 'code':
            compile(''.join(after['source']), f'corrected-cell-{index}', 'exec')
            assert after['outputs'] == []
    assert ''.join(corrected['cells'][3]['source']) == (root / 'scripts/kaggle_backup_controls.py').read_text() + '\nbackup_validate(CLIENT_WORK)\n'
    assert 'VISUAL_ACCEPTANCE_CONFIRMED = False' in ''.join(corrected['cells'][-1]['source'])

"""Kaggle backup validation and explicit website registration. Never starts a worker."""
from io import BytesIO
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import UUID, uuid4


def _backend_key():
    from kaggle_secrets import UserSecretsClient
    key = UserSecretsClient().get_secret('AI_BACKEND_API_KEY') or ''
    if len(key) < 32:
        raise RuntimeError('Enable the existing backend key in Kaggle Secrets')
    return key


def backup_validate(work, *, key=None, opener=urlopen, sleep=time.sleep, clock=time.monotonic):
    from PIL import Image
    work = Path(work)
    receipt = json.loads((work / 'photo-check-update.json').read_text())
    if receipt.get('schema') != 'beautycore-photo-check-update-v1':
        raise RuntimeError('Missing current CPU update receipt')
    key = key or _backend_key()
    headers = {'X-AI-Backend-Key': key, 'X-AI-User-Id':'backup-validation'}
    rows = []
    raw = BytesIO()
    Image.new('RGB', (512, 512), 'white').save(raw, format='PNG')

    def read(request, timeout=45):
        try:
            with opener(request, timeout=timeout) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    for feature, style in [('hairstyle','exp_french_bob_wispy'), ('makeup','natural_makeup'), ('nails','classic_red')]:
        boundary = 'backup-' + uuid4().hex
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="style_id"\r\n\r\n{style}\r\n'
                f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="blank.png"\r\n'
                'Content-Type: image/png\r\n\r\n').encode() + raw.getvalue() + f'\r\n--{boundary}--\r\n'.encode()
        request = Request(f'http://127.0.0.1:8800/features/{feature}/generate', data=body,
            headers={**headers, 'Content-Type':'multipart/form-data; boundary=' + boundary})
        # Submit once. The hosted gateway admits a job before the inner photo
        # guard returns, so 202 is a ticket, not the subject-check result.
        status, result = read(request)
        admission_status = status
        if status == 202:
            job_id = result.get('job_id') if isinstance(result, dict) else None
            try:
                valid_id = isinstance(job_id, str) and str(UUID(job_id)) == job_id
            except (ValueError, AttributeError):
                valid_id = False
            if not valid_id:
                raise RuntimeError('Invalid validation job ticket; no retry was made')
            job_url = 'http://127.0.0.1:8800/jobs/' + job_id
            deadline = clock() + 60
            while True:
                remaining = deadline - clock()
                if remaining <= 0:
                    raise RuntimeError('Validation job is unresolved; no retry was made')
                status, state = read(Request(job_url, headers=headers), timeout=min(45, remaining))
                if (status != 200 or not isinstance(state, dict) or state.get('job_id') != job_id
                        or state.get('status') not in ('generating', 'completed', 'failed')):
                    raise RuntimeError('Validation job status is unavailable; no retry was made')
                if state['status'] != 'generating':
                    remaining = deadline - clock()
                    if remaining <= 0:
                        raise RuntimeError('Validation job is unresolved; no retry was made')
                    status, result = read(Request(job_url + '/result', headers=headers), timeout=min(45, remaining))
                    break
                sleep(min(0.5, remaining))
        # Exact messages distinguish subject rejection from unrelated validation.
        expected = {'makeup':'Makeup requires one clear face. Upload a well-lit portrait, not a hand or another object.',
                    'hairstyle':'Hair preview requires one clear face with the head and hair in frame. Upload a portrait, not a hand or another object.',
                    'nails':'Nails requires one clear hand with visible nails. Upload a hand photo, not a portrait or another object.'}[feature]
        if status != 422 or not isinstance(result, dict) or result.get('detail') != expected:
            # Status is useful; arbitrary response detail can contain private data.
            safe_status = status if type(status) is int else 'unknown'
            raise RuntimeError('Local subject rejection failed for ' + feature
                               + ' (HTTP ' + str(safe_status) + '); no retry was made')
        rows.append({'feature':feature, 'admission_status':admission_status, 'wrong_subject_status':status})
    report = {'schema':'beautycore-backup-validation-v1', 'status':'SUBJECT_REJECTION_PASS',
              'cases':rows, 'real_generation_verified':False, 'website_connected':False}
    (work / 'backup-validation.json').write_text(json.dumps(report, indent=2))
    print('SUBJECT_REJECTION_PASS. Real generation and visual review still required.')
    return report


def backup_connect(work, website, *, visual_accepted=False):
    if not visual_accepted:
        raise RuntimeError('Review the real outputs first, then explicitly confirm visual acceptance in this cell')
    work = Path(work)
    validation = json.loads((work / 'backup-validation.json').read_text())
    application = json.loads((work / 'application-results/results.json').read_text())
    if (validation.get('status') != 'SUBJECT_REJECTION_PASS'
            or application.get('status') != 'TECHNICAL_PASS_VISUAL_REVIEW_PENDING'
            or len(application.get('cases', [])) != 16):
        raise RuntimeError('Complete the current photo checks and 16 real application cases before connecting')
    record_path = work / 'demo-session.json'
    record = json.loads(record_path.read_text())
    if record.get('heartbeat_pid') or record.get('status') == 'CONNECTED_FOR_REHEARSAL':
        raise RuntimeError('Already connected; do not create another heartbeat')
    spec = importlib.util.spec_from_file_location('backup_registrar', work / 'runtime_registration.py')
    registrar = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(registrar)
    if not registrar.services_alive(record):
        raise RuntimeError('Existing services are not alive; no registration attempted')
    key = _backend_key()
    ack = registrar.register(website, record, key)
    record.update(status='CONNECTED_FOR_REHEARSAL', registration_expires_at=ack['expires_at'],
                  full_generation_verified=True)
    record_path.write_text(json.dumps(record, indent=2))
    with (work / 'registration.log').open('a') as log:
        heartbeat = subprocess.Popen([sys.executable, str(work / 'runtime_registration.py'), website, str(record_path)],
            env={**os.environ, 'AI_BACKEND_API_KEY':key}, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    record['heartbeat_pid'] = heartbeat.pid
    record_path.write_text(json.dumps(record, indent=2))
    print('CONNECTED TO WEBSITE:', website)

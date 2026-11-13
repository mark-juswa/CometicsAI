"""Kaggle backup validation and explicit website registration. Never starts a worker."""
from io import BytesIO
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4


def _backend_key():
    from kaggle_secrets import UserSecretsClient
    key = UserSecretsClient().get_secret('AI_BACKEND_API_KEY') or ''
    if len(key) < 32:
        raise RuntimeError('Enable the existing backend key in Kaggle Secrets')
    return key


def backup_validate(work, *, key=None, opener=urlopen):
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
    for feature, style in [('hairstyle','exp_french_bob_wispy'), ('makeup','natural_makeup'), ('nails','classic_red')]:
        boundary = 'backup-' + uuid4().hex
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="style_id"\r\n\r\n{style}\r\n'
                f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="blank.png"\r\n'
                'Content-Type: image/png\r\n\r\n').encode() + raw.getvalue() + f'\r\n--{boundary}--\r\n'.encode()
        request = Request(f'http://127.0.0.1:8800/features/{feature}/generate', data=body,
            headers={**headers, 'Content-Type':'multipart/form-data; boundary=' + boundary})
        try:
            with opener(request, timeout=45) as response:
                status = response.status
                result = json.load(response)
        except HTTPError as error:
            status, result = error.code, json.load(error)
        # Exact messages distinguish subject rejection from unrelated validation.
        expected = {'makeup':'Makeup requires one clear face. Upload a well-lit portrait, not a hand or another object.',
                    'hairstyle':'Hair preview requires one clear face with the head and hair in frame. Upload a portrait, not a hand or another object.',
                    'nails':'Nails requires one clear hand with visible nails. Upload a hand photo, not a portrait or another object.'}[feature]
        if status != 422 or result.get('detail') != expected:
            raise RuntimeError('Local subject rejection failed for ' + feature + '; no retry was made')
        rows.append({'feature':feature, 'wrong_subject_status':status})
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

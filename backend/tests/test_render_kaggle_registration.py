"""Metadata-only registration and heartbeat never replay generation or disclose credentials."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import importlib.util
import json
import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('registration', ROOT / 'scripts/render_kaggle_registration.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
KEY = 'test-only-runtime-key-at-least-thirty-two-characters'
RECORD = {'session_id':'09b53a8b-e8a6-4a88-946e-355dbfab2c6d','url':'https://fixture-a.trycloudflare.com',
          'started_at':1791539940,'registration_expires_at':1791540180000,'api_pid':100,'tunnel_pid':200}

def test_cross_language_hmac_fixture():
    message={'schema':module.SCHEMA,'operation':'register','session_id':RECORD['session_id'],
             'endpoint':RECORD['url'],'started_at':RECORD['started_at'],'issued_at':1791540000}
    assert module.sign(message,KEY) == '875a28e74f807d27d8118f93d89908d35be2c8c896f3331208d83eaafa895483'
    assert KEY not in module.canonical(message).decode()

def test_only_registration_path_is_called_with_signed_metadata():
    requests=[]
    ack={'connected':True,'session_id':RECORD['session_id'],'expires_at':1791540180000}
    class Response:
        status=200
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,n):return json.dumps(ack).encode()
    def open_request(request,timeout):
        requests.append(request)
        return Response()
    got=module.send('https://beautycore-demo.onrender.com',RECORD,KEY,'register',
                    opener=SimpleNamespace(open=open_request),now=lambda:1791540000)
    assert got == ack
    assert len(requests)==1
    request=requests[0]
    assert request.full_url.endswith('/api/internal/ai-runtime/register')
    assert 'generation' not in request.full_url
    assert KEY not in request.data.decode() and KEY not in str(request.headers)
    assert request.headers.get('X-ai-runtime-signature')

@pytest.mark.parametrize('website',['http://localhost:3000','https://user:secret@example.com','https://example.com/path',
                                    'https://example.com:444','https://example.com?secret=value'])
def test_unsafe_website_configuration_refused(website):
    with pytest.raises(module.RegistrationError):module.website_root(website)

@pytest.mark.parametrize('status',[400,401,403,404,409])
def test_permanent_rejection_is_not_retried(status):
    calls=[]
    def send(*args):calls.append(args);raise module.RegistrationError(status)
    with pytest.raises(module.RegistrationError):module.register('https://website.example',RECORD,KEY,send_fn=send,sleep=lambda n:None)
    assert len(calls)==1

def test_cold_start_retries_only_metadata_and_keeps_same_session():
    calls=[]
    def send(*args):
        calls.append(args)
        if len(calls)<3:raise module.RegistrationError(503)
        return {'connected':True}
    assert module.register('https://website.example',RECORD,KEY,send_fn=send,sleep=lambda n:None)['connected']
    assert len(calls)==3
    assert all(args[1]['session_id']==RECORD['session_id'] and args[3]=='register' for args in calls)

def test_heartbeat_stops_when_process_stops_without_sending_renewal():
    calls=[]
    module.heartbeat('https://website.example',RECORD,KEY,send_fn=lambda *args:calls.append(args),alive=lambda r:False,sleep=lambda n:None)
    assert calls==[]

def test_old_or_expired_heartbeat_is_not_reregistered():
    calls=[]
    def send(*args):calls.append(args);raise module.RegistrationError(409)
    module.heartbeat('https://website.example',RECORD,KEY,send_fn=send,alive=lambda r:True,sleep=lambda n:None)
    assert len(calls)==1 and calls[0][3]=='renew'

def test_known_registry_expiry_stops_network_retry_loop():
    calls=[]
    def send(*args):calls.append(args);raise module.RegistrationError()
    module.heartbeat('https://website.example',RECORD,KEY,send_fn=send,alive=lambda r:True,sleep=lambda n:None,now=lambda:1791540181)
    assert len(calls)==1

def test_alive_requires_both_own_processes_and_gpu_api_ports():
    connection=SimpleNamespace(settimeout=lambda n:None,connect_ex=lambda endpoint:0)
    with patch.object(module.os,'kill') as kill,patch.object(module.socket,'socket') as sock:
        sock.return_value.__enter__.return_value=connection
        assert module.services_alive(RECORD)
        assert kill.call_count==2
        connection.connect_ex=lambda endpoint:1
        assert not module.services_alive(RECORD)

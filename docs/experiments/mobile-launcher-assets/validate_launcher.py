"""Reproducible CPU-only Windows launcher integration acceptance.

The resolver fixture permits runtime validation without changing this PC's Public
Wi-Fi profile. It is NOT evidence of USB transport, trusted LAN or native use.
Production launchers have no fixture/unsafe-network option.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts import mobile_launch as launcher


def child(fail_expo, fail_api):
    original = launcher.start_child
    original_wait = launcher.wait_ready

    def spawn(job, command, cwd, env, output=None):
        if fail_expo and command[0].lower().endswith('node.exe'):
            command = [sys.executable, '-c', 'import sys;sys.exit(23)']
        if fail_api and 'uvicorn' in command:
            command = [sys.executable, '-m', 'http.server', '8001', '--bind', '127.0.0.1']
        return original(job, command, cwd, env, output)

    def readiness(process, url, valid, label, stop, timeout):
        return original_wait(process, url, valid, label, stop, 2 if fail_api else timeout)

    with patch.object(launcher, 'choose_connection', return_value=launcher.Connection(
            'TEST_LOOPBACK', '127.0.0.1', 'controlled resolver fixture', adb='fixture')), \
            patch.object(launcher, 'start_child', side_effect=spawn), \
            patch.object(launcher, 'wait_ready', side_effect=readiness), \
            patch.object(sys, 'argv', ['mobile_launch.py']):
        return launcher.main()


def wait(predicate, timeout=90):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.25)
    raise AssertionError('Integration acceptance timed out')


def save_output(path, *parts):
    # cmd.exe's pause emits trailing spaces; retain content with Git-clean whitespace.
    path.write_text('\n'.join(line.rstrip() for line in ''.join(parts).splitlines()) + '\n', encoding='utf-8')


def acceptance():
    launcher.require_free_ports()
    if launcher.STATE.exists():
        raise AssertionError('Existing ownership record; refusing to interfere')
    result = {}
    evidence = Path(__file__).resolve().parent
    sentinel = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(300)'],
                                creationflags=subprocess.CREATE_NO_WINDOW)
    environment_files = {path: path.read_bytes() for path in
                         [ROOT / 'backend/.env', ROOT / 'mobile/.env.local'] if path.exists()}
    process = None
    try:
        with (evidence / 'startup.log').open('w', encoding='utf-8') as output:
            process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--child'],
                                       cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
            def ready():
                if process.poll() is not None:
                    raise AssertionError('Real startup exited; inspect startup.log')
                try:
                    return launcher.read_url('http://127.0.0.1:8081/status').strip() == 'packager-status:running'
                except OSError:
                    return False
            wait(ready)
            wait(lambda: 'MOBILE_DEV_RUNNING' in (evidence / 'startup.log').read_text(encoding='utf-8'))
            health = json.loads(launcher.read_url('http://127.0.0.1:8001/health'))
            assert health == {'status': 'ok', 'generator': 'mock'}, health
            result['health'] = health
            result['catalog_counts'] = {}
            for feature in ('hairstyle', 'makeup', 'nails'):
                catalog = json.loads(launcher.read_url(f'http://127.0.0.1:8001/features/{feature}/styles'))
                rows = catalog['styles'] if isinstance(catalog, dict) else catalog
                assert rows, feature
                result['catalog_counts'][feature] = len(rows)
            # Expo manifest must expose the fixture host, and JS must inline the process API origin.
            from urllib.request import Request
            request = Request('http://127.0.0.1:8081/', headers={'Expo-Platform': 'android',
                              'Accept': 'application/expo+json', 'Expo-Protocol-Version': '1'})
            with launcher.HTTP.open(request, timeout=30) as response:
                manifest = json.load(response)
            assert manifest['extra']['expoClient']['hostUri'] == '127.0.0.1:8081', manifest
            bundle_url = manifest['launchAsset']['url']
            with launcher.HTTP.open(bundle_url, timeout=120) as response:
                bundle = response.read().decode('utf-8')
            assert 'http://127.0.0.1:8001' in bundle
            private_values = []
            for path in (ROOT / 'backend/.env', ROOT / 'beautycore/.env.local'):
                if path.exists():
                    for line in path.read_text(encoding='utf-8-sig').splitlines():
                        if '=' not in line or line.lstrip().startswith('#'):
                            continue
                        key, value = line.split('=', 1)
                        value = value.strip().strip('\"\'')
                        if len(value) >= 16 and any(word in key.upper() for word in
                                ('SECRET', 'KEY', 'TOKEN', 'DATABASE', 'REMOTE_URL', 'REMOTE_ROOT')):
                            private_values.append(value)
            assert not any(value in bundle for value in private_values), 'Private value in bundle'
            result['private_values_scanned'] = len(private_values)
            result['bundle_secret_leaks'] = 0
            result['android_bundle_process_origin'] = True
            result['expo_host'] = manifest['extra']['expoClient']['hostUri']
            # Actual launcher repeated start uses existing ownership, no second process tree.
            duplicate = subprocess.run([sys.executable, str(ROOT / 'scripts/mobile_launch.py')],
                                       capture_output=True, text=True, timeout=10)
            assert duplicate.returncode == 0 and 'already running' in duplicate.stdout, duplicate
            result['duplicate_start_preserves_session'] = True
            # Exercise the matching real batch wrapper.
            stopped = subprocess.run(['cmd.exe', '/d', '/c', str(ROOT / 'STOP_MOBILE.bat')],
                                     cwd=ROOT, input='\n', capture_output=True, text=True, timeout=40)
            assert stopped.returncode == 0, stopped.stdout + stopped.stderr
            process.wait(timeout=10)
            assert process.returncode == 0, process.returncode
            launcher.require_free_ports()
            assert sentinel.poll() is None
            result['stop_owned_session_only'] = True
            result['stop_output'] = stopped.stdout.strip()
        with (evidence / 'expo-failure.log').open('w', encoding='utf-8') as output:
            process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                        '--child', '--fail-expo'], cwd=ROOT,
                                       stdout=output, stderr=subprocess.STDOUT)
            process.wait(timeout=60)
            assert process.returncode == 1
        launcher.require_free_ports()
        assert not launcher.STATE.exists()
        assert sentinel.poll() is None
        result['expo_failure_closes_owned_backend'] = True
        with (evidence / 'api-unhealthy.log').open('w', encoding='utf-8') as output:
            process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                        '--child', '--fail-api'], cwd=ROOT,
                                       stdout=output, stderr=subprocess.STDOUT)
            process.wait(timeout=15)
            assert process.returncode == 1
        launcher.require_free_ports()
        assert not launcher.STATE.exists() and sentinel.poll() is None
        result['unhealthy_api_closes_owned_session'] = True
        # Unrelated port owner must survive an actual START batch invocation.
        import socket
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 8001))
            listener.listen()
            occupied = subprocess.run(['cmd.exe', '/d', '/c', str(ROOT / 'START_MOBILE.bat')],
                                      cwd=ROOT, input='\n', capture_output=True, text=True, timeout=15)
            assert occupied.returncode == 1 and 'Port 8001 is occupied' in occupied.stderr, occupied
            with socket.create_connection(listener.getsockname(), timeout=1):
                pass
            save_output(evidence / 'occupied-port.log', occupied.stdout, occupied.stderr)
            result['occupied_8001_preserves_unrelated_listener'] = True
        # Inspect the actual network, without granting permission to publish on Public Wi-Fi.
        data = launcher.network_inventory()
        try:
            launcher.select_lan(data)
            result['actual_lan_selection'] = 'usable trusted route'
        except launcher.StartupError as error:
            result['actual_lan_selection'] = str(error)
        adb = launcher.find_adb()
        result['authorized_android_devices'] = launcher.authorized_devices(
            launcher.adb_call(adb, 'devices', '-l')) if adb else []
        if 'No usable trusted LAN' in result['actual_lan_selection'] and not result['authorized_android_devices']:
            blocked = subprocess.run(['cmd.exe', '/d', '/c', str(ROOT / 'START_MOBILE.bat')],
                                     cwd=ROOT, input='\n', capture_output=True, text=True, timeout=40)
            assert blocked.returncode == 1 and 'No usable trusted LAN' in blocked.stderr, blocked
            save_output(evidence / 'no-transport.log', blocked.stdout, blocked.stderr)
            launcher.require_free_ports()
            result['actual_no_transport_fails_without_children'] = True
        assert all(path.read_bytes() == content for path, content in environment_files.items())
        result['environment_files_unchanged'] = True
        result['native_acceptance'] = 'PENDING, no authorized device'
        (evidence / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result, indent=2))
    finally:
        if process is not None and process.poll() is None:
            # Only our child launcher is eligible; ask its controller first.
            try:
                launcher.stop_session()
                process.wait(timeout=10)
            finally:
                if process.poll() is None:
                    process.terminate()  # Job handle closure cleans its new children.
                    process.wait(timeout=10)
        sentinel.terminate()
        sentinel.wait(timeout=10)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--child', action='store_true')
    parser.add_argument('--fail-expo', action='store_true')
    parser.add_argument('--fail-api', action='store_true')
    args = parser.parse_args()
    if args.child:
        sys.exit(child(args.fail_expo, args.fail_api))
    acceptance()

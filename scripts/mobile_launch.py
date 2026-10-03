"""Isolated Windows MOBILE-01 dev session; no env-file edits or GPU discovery.

START stays in the foreground so Expo has its normal interactive QR console.
STOP authenticates to this session, whose job owns only newly spawned children.
"""

import argparse
import ctypes
from ctypes import wintypes
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
from urllib.error import URLError
from urllib.request import ProxyHandler, Request, build_opener
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.capstone_launch import WindowsJob  # Existing owned-job primitive only.
from scripts.capstone_discovery import StartupError

WORK = ROOT / '.tmp/mobile'
STATE = WORK / 'control.json'
API_PORT, EXPO_PORT = 8001, 8081
HTTP = build_opener(ProxyHandler({}))  # Local probes must never go through a proxy.
SAFE_ENV = {
    'PATH', 'PATHEXT', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'TEMP', 'TMP',
    'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'PROGRAMDATA', 'PROGRAMFILES',
    'PROGRAMFILES(X86)', 'HOMEDRIVE', 'HOMEPATH', 'USERNAME', 'USERDOMAIN',
    'ANDROID_HOME', 'ANDROID_SDK_ROOT', 'JAVA_HOME',
}


def base_environment():
    return {key: value for key, value in os.environ.items() if key.upper() in SAFE_ENV}


def child_environments(connection):
    backend = base_environment()
    backend.update(GENERATION_ENGINE='mock', MAKEUP_GENERATION_ENGINE='mock',
                   NAILS_PREVIEW_MODE='mock', CONSULTATION_PROVIDER='deterministic',
                   PYTHONUNBUFFERED='1', FRONTEND_ORIGINS=','.join(
                       f'http://{host}:{EXPO_PORT}' for host in
                       dict.fromkeys(['localhost', '127.0.0.1', connection.host])))
    expo = base_environment()
    expo.update(EXPO_PUBLIC_API_BASE_URL=connection.origin, EXPO_NO_DOTENV='1',
                REACT_NATIVE_PACKAGER_HOSTNAME=connection.host)
    return backend, expo


def private_ipv4(value):
    try:
        address = ipaddress.IPv4Address(value)
        return any(address in ipaddress.IPv4Network(block) for block in
                   ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'))
    except (ValueError, TypeError):
        return False


def select_lan(inventory):
    """Lowest effective-metric usable physical default route; never first IPv4."""
    candidates = []
    for route in inventory['routes']:
        index = route['InterfaceIndex']
        adapter = next((a for a in inventory['adapters'] if a['ifIndex'] == index), {})
        interface = next((i for i in inventory['interfaces'] if i['InterfaceIndex'] == index), {})
        profile = next((p for p in inventory['profiles'] if p['InterfaceIndex'] == index), {})
        if not (adapter.get('HardwareInterface') and not adapter.get('Virtual')
                and adapter.get('State') == 'Up' and interface.get('State') == 'Connected'
                and profile.get('Category') in ('Private', 'DomainAuthenticated')
                and private_ipv4(route.get('NextHop'))):
            continue
        addresses = [a['IPAddress'] for a in inventory['addresses']
                     if a['InterfaceIndex'] == index and a['State'] == 'Preferred'
                     and not a['SkipAsSource'] and private_ipv4(a['IPAddress'])]
        if len(set(addresses)) != 1:
            continue
        candidates.append((int(route['RouteMetric']) + int(interface['InterfaceMetric']),
                           addresses[0], adapter['Name']))
    candidates = sorted(set(candidates))
    if not candidates:
        raise StartupError('No usable trusted LAN default route. Connect an authorized Android '
                           'device by USB, or use trusted Wi-Fi/Ethernet marked Private in Windows '
                           'Settings > Network & internet. VPN/virtual, disconnected, Public, '
                           'ambiguous and non-private-address interfaces are excluded.')
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
        raise StartupError('Two trusted LAN default routes have equal priority; use USB or '
                           'resolve the Windows route priority before starting.')
    return candidates[0][1:]


def network_inventory():
    shell = shutil.which('powershell.exe')
    if not shell:
        raise StartupError('Windows PowerShell is required to inspect LAN routes.')
    result = subprocess.run([shell, '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File',
                             str(ROOT / 'scripts/mobile_network.ps1')],
                            capture_output=True, text=True, timeout=20,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise StartupError('Windows could not inspect LAN routes/profiles: ' + result.stderr.strip())
    try:
        return json.loads(result.stdout.lstrip('\ufeff'))
    except ValueError as error:
        raise StartupError('Windows returned an invalid network inventory.') from error


def find_adb():
    candidates = [Path(os.environ[key]) / 'platform-tools/adb.exe'
                  for key in ('ANDROID_HOME', 'ANDROID_SDK_ROOT') if os.environ.get(key)]
    located = shutil.which('adb.exe')
    if located:
        candidates.append(Path(located))
    if os.environ.get('LOCALAPPDATA'):
        candidates.append(Path(os.environ['LOCALAPPDATA']) / 'Android/Sdk/platform-tools/adb.exe')
    return next((str(path) for path in candidates if path.is_file()), None)


def adb_call(adb, *arguments):
    result = subprocess.run([adb, *arguments], capture_output=True, text=True,
                            timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise StartupError('ADB failed: ' + result.stderr.strip())
    return result.stdout


def authorized_devices(output):
    return [parts[0] for line in output.splitlines()
            if len(parts := line.split()) >= 2 and parts[1] == 'device']


def reverse_mappings(output):
    return {parts[-2]: parts[-1] for line in output.splitlines()
            if len(parts := line.split()) >= 3 and parts[-2].startswith('tcp:')}


@dataclass
class Connection:
    mode: str
    host: str
    description: str
    adb: str | None = None
    device: str | None = None
    created: list[str] = field(default_factory=list)

    @property
    def origin(self):
        return f'http://{self.host}:{API_PORT}'

    def cleanup(self):
        if not self.created:
            return
        try:
            mappings = reverse_mappings(adb_call(self.adb, '-s', self.device, 'reverse', '--list'))
            for port in self.created:
                if mappings.get(port) == port:
                    adb_call(self.adb, '-s', self.device, 'reverse', '--remove', port)
        except (StartupError, subprocess.TimeoutExpired, OSError):
            print('USB cleanup unavailable (device disconnected); no other mappings were removed.', flush=True)


def choose_connection():
    adb = find_adb()
    if adb:
        try:
            devices = authorized_devices(adb_call(adb, 'devices', '-l'))
        except (StartupError, subprocess.TimeoutExpired, OSError) as error:
            print(f'ADB unavailable; checking LAN ({error}).', flush=True)
            devices = []
        for device in devices:
            connection = Connection('USB/ADB', '127.0.0.1', f'Android device {device}', adb, device)
            try:
                mappings = reverse_mappings(adb_call(adb, '-s', device, 'reverse', '--list'))
                for number in (API_PORT, EXPO_PORT):
                    port = f'tcp:{number}'
                    if port in mappings:
                        if mappings[port] != port:
                            raise StartupError(f'{port} has an existing different reverse target; preserving it.')
                    else:
                        adb_call(adb, '-s', device, 'reverse', '--no-rebind', port, port)
                        connection.created.append(port)
                mappings = reverse_mappings(adb_call(adb, '-s', device, 'reverse', '--list'))
                if not all(mappings.get(f'tcp:{p}') == f'tcp:{p}' for p in (API_PORT, EXPO_PORT)):
                    raise StartupError('ADB reverse verification failed.')
                return connection
            except (StartupError, subprocess.TimeoutExpired, OSError) as error:
                print(f'USB reverse unavailable for {device}; checking another device/LAN ({error}).', flush=True)
                connection.cleanup()
    host, name = select_lan(network_inventory())
    return Connection('LAN', host, name)


def require_free_ports():
    for port in (API_PORT, EXPO_PORT):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            # Windows exclusive bind detects listeners on any local interface.
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            try:
                probe.bind(('0.0.0.0', port))
            except OSError as error:
                raise StartupError(f'Port {port} is occupied by a process outside this mobile session. '
                                   'Close its owner explicitly; this launcher will not stop it.') from error


def resume_child(process):
    """Popen closes its thread handle. Recover the suspended primary thread safely."""
    class ThreadEntry(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('usage', wintypes.DWORD),
                    ('thread', wintypes.DWORD), ('owner', wintypes.DWORD),
                    ('priority', wintypes.LONG), ('delta', wintypes.LONG), ('flags', wintypes.DWORD)]
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    api.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    api.Thread32First.argtypes = api.Thread32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(ThreadEntry)]
    api.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    api.OpenThread.restype = wintypes.HANDLE
    api.ResumeThread.argtypes = [wintypes.HANDLE]
    api.ResumeThread.restype = wintypes.DWORD
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    snapshot = api.CreateToolhelp32Snapshot(4, 0)  # TH32CS_SNAPTHREAD
    if snapshot == wintypes.HANDLE(-1).value:
        raise StartupError('Cannot inspect the new suspended child thread.')
    try:
        entry = ThreadEntry()
        entry.size = ctypes.sizeof(entry)
        available = api.Thread32First(snapshot, ctypes.byref(entry))
        while available:
            if entry.owner == process.pid:
                thread = api.OpenThread(2, False, entry.thread)  # THREAD_SUSPEND_RESUME
                if not thread:
                    break
                try:
                    if api.ResumeThread(thread) != 0xFFFFFFFF:
                        return
                finally:
                    api.CloseHandle(thread)
                break
            available = api.Thread32Next(snapshot, ctypes.byref(entry))
        raise StartupError('Cannot resume the safely owned child process.')
    finally:
        api.CloseHandle(snapshot)


def start_child(job, command, cwd, env, output=None):
    # Assign before any child code can run/spawn grandchildren. No PID-based ownership guess.
    process = subprocess.Popen(command, cwd=cwd, env=env, stdout=output,
                               stderr=subprocess.STDOUT if output else None,
                               creationflags=4 | (subprocess.CREATE_NO_WINDOW if output else 0))
    try:
        job.add(process)
        resume_child(process)
    except Exception:
        process.terminate()
        process.wait(timeout=10)
        raise
    return process


def read_url(url, token=None, method='GET'):
    request = Request(url, headers={'X-Mobile-Token': token} if token else {}, method=method)
    with HTTP.open(request, timeout=2) as response:
        return response.read(65536).decode('utf-8')


def wait_ready(process, url, valid, label, stop, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if stop.is_set():
            raise StartupError('Startup stopped by STOP_MOBILE.')
        if process.poll() is not None:
            raise StartupError(f'{label} exited during startup (code {process.returncode}).')
        try:
            if valid(read_url(url)) and process.poll() is None:
                return
        except (URLError, OSError, ValueError):
            pass
        stop.wait(0.5)
    raise StartupError(f'{label} did not become healthy within {timeout} seconds.')


def api_healthy(body):
    value = json.loads(body)
    return isinstance(value, dict) and value.get('status') == 'ok' and value.get('generator') == 'mock'


class Controller:
    def __init__(self):
        self.session = uuid4().hex
        self.token = secrets.token_hex(32)
        self.stop = threading.Event()
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def handle_request(self):
                if not secrets.compare_digest(self.headers.get('X-Mobile-Token', ''), owner.token):
                    self.send_error(403)
                    return
                if (self.command, self.path) not in (('GET', '/status'), ('POST', '/stop')):
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'session': owner.session}).encode())
                if self.command == 'POST':
                    owner.stop.set()

            do_GET = do_POST = handle_request

            def log_message(self, *_):
                pass

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def save(self, connection):
        self.record = {'session': self.session, 'token': self.token,
                       'port': self.server.server_port, 'mode': connection.mode,
                       'api': connection.origin}
        temporary = STATE.with_suffix('.new')
        temporary.write_text(json.dumps(self.record), encoding='utf-8')
        temporary.replace(STATE)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        if STATE.exists() and read_state()['session'] == self.session:
            STATE.unlink()


def read_state():
    try:
        value = json.loads(STATE.read_text(encoding='utf-8'))
        if (not isinstance(value['port'], int) or isinstance(value['port'], bool)
                or not 1 <= value['port'] <= 65535
                or not isinstance(value['token'], str) or len(value['token']) != 64
                or not isinstance(value['session'], str) or len(value['session']) != 32):
            raise ValueError('Invalid ownership data')
        return value
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise StartupError('Invalid mobile ownership file. No processes will be stopped. '
                           'Inspect .tmp/mobile/control.json before retrying.') from error


def contact(record, method='GET'):
    path = '/stop' if method == 'POST' else '/status'
    body = json.loads(read_url(f"http://127.0.0.1:{record['port']}{path}", record['token'], method))
    if not isinstance(body, dict) or body.get('session') != record['session']:
        raise StartupError('Mobile session identity mismatch; no process was stopped.')


def stop_session():
    if not STATE.exists():
        print('No mobile launcher session is running.')
        return
    record = read_state()
    try:
        contact(record)  # Verify identity before sending any stop request.
        contact(record, 'POST')
    except (URLError, OSError, ValueError) as error:
        raise StartupError('Mobile controller is unavailable. No PID was killed; the session '
                           'may already be closed. Start checks stale ownership and free ports.') from error
    deadline = time.monotonic() + 30
    while STATE.exists() and time.monotonic() < deadline:
        time.sleep(0.25)
    if STATE.exists():
        raise StartupError('Mobile stop was requested but cleanup did not finish in 30 seconds.')
    print('Mobile session stopped; only its owned children/reverse mappings were released.')


def run_session():
    if os.name != 'nt':
        raise StartupError('START_MOBILE requires Windows.')
    WORK.mkdir(parents=True, exist_ok=True)
    import msvcrt
    with (WORK / 'launch.lock').open('a+b') as lock:
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            if STATE.exists():
                contact(read_state())
                print('Mobile session already running. Use STOP_MOBILE before changing connections.')
                return
            raise StartupError('Another mobile launcher is starting; wait or use STOP_MOBILE.')
        try:
            require_free_ports()
            node = shutil.which('node.exe')
            cli = ROOT / 'mobile/node_modules/expo/bin/cli'
            if not node or not cli.is_file():
                raise StartupError('Node.js and mobile dependencies are required. Run npm ci in mobile/ once.')
            # Stale ownership never grants authority over a PID. Only remove after free-port checks.
            if STATE.exists():
                record = read_state()
                try:
                    contact(record)
                except (URLError, OSError):
                    STATE.unlink()
                else:
                    raise StartupError('A mobile controller is still active; use STOP_MOBILE.')
            connection = choose_connection()
            job, controller = None, None
            children = []
            try:
                print(f'Mobile connection: {connection.mode} ({connection.description})\n'
                      f'Application API: {connection.origin}\n'
                      f'Expo: http://{connection.host}:{EXPO_PORT}\n'
                      'Separate CPU mock backend; no GPU generation. Keep this window open.\n'
                      'Stop with Ctrl+C or STOP_MOBILE.bat.', flush=True)
                backend_env, expo_env = child_environments(connection)
                job = WindowsJob()
                controller = Controller()
                controller.save(connection)
                with (WORK / 'backend.log').open('w', encoding='utf-8') as log:
                    backend = start_child(job, [sys.executable, '-m', 'uvicorn', 'app.main:app',
                                               '--host', '0.0.0.0', '--port', str(API_PORT)],
                                          ROOT / 'backend', backend_env, log)
                    children.append(backend)
                    wait_ready(backend, f'http://127.0.0.1:{API_PORT}/health', api_healthy,
                               'FastAPI (see .tmp/mobile/backend.log)', controller.stop, 45)
                    # SDK 57 binds "localhost"; prefer IPv4 to match adb reverse/our fixed origin.
                    node_options = ['--dns-result-order=ipv4first'] if connection.adb else []
                    expo = start_child(job, [node, *node_options, str(cli), 'start', '--go', '--clear',
                                            '--port', str(EXPO_PORT),
                                            '--localhost' if connection.adb else '--lan'],
                                       ROOT / 'mobile', expo_env)
                    children.append(expo)
                    wait_ready(expo, f'http://127.0.0.1:{EXPO_PORT}/status',
                               lambda body: body.strip() == 'packager-status:running',
                               'Expo', controller.stop, 60)
                    print('MOBILE_DEV_RUNNING - open the Expo Go QR/address above.', flush=True)
                    while not controller.stop.wait(0.5):
                        for label, process in (('FastAPI', backend), ('Expo', expo)):
                            if process.poll() is not None:
                                raise StartupError(f'{label} stopped (code {process.returncode}); mobile session closed.')
            finally:
                if job:
                    job.close()
                for child in children:
                    child.wait(timeout=10)
                connection.cleanup()
                if controller:
                    controller.close()
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stop', action='store_true')
    arguments = parser.parse_args()
    try:
        stop_session() if arguments.stop else run_session()
    except KeyboardInterrupt:
        print('\nMobile session closed.')
        return 0
    except (StartupError, OSError, subprocess.TimeoutExpired, URLError, ValueError) as error:
        print(f'MOBILE_DEV_FAILED: {error}', file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

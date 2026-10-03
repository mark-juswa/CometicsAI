"""Connection selection and ownership regressions; no device or GPU required."""

import copy
from io import StringIO
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from scripts import mobile_launch as launcher


def inventory():
    return {
        'routes': [{'InterfaceIndex': 18, 'NextHop': '192.168.1.1', 'RouteMetric': 0}],
        'interfaces': [{'InterfaceIndex': 18, 'State': 'Connected', 'InterfaceMetric': 45}],
        'adapters': [{'ifIndex': 18, 'Name': 'Wi-Fi', 'HardwareInterface': True,
                      'Virtual': False, 'State': 'Up'}],
        'profiles': [{'InterfaceIndex': 18, 'Category': 'Private'}],
        'addresses': [{'InterfaceIndex': 18, 'IPAddress': '192.168.1.5',
                       'State': 'Preferred', 'SkipAsSource': False}],
    }


class MobileLauncherTests(unittest.TestCase):
    def test_beautycore_probe_requires_existing_session_route_and_anonymous_ai_denial(self):
        denied = HTTPError('http://local/api/ai/features', 401, 'Denied', {}, None)
        with patch.object(launcher, 'read_url', side_effect=['{"user":null}', denied]) as read:
            launcher.verify_beautycore()
            self.assertEqual([call.args[0] for call in read.call_args_list], [
                'http://127.0.0.1:3000/api/auth/session', 'http://127.0.0.1:3000/api/ai/features'])
        for replies in (['{"status":"ok"}'], ['{"user":null}', '[]'],
                        ['{"user":null}', HTTPError('http://local', 503, 'Unavailable', {}, None)]):
            with self.subTest(replies=replies), patch.object(launcher, 'read_url', side_effect=replies), \
                    self.assertRaisesRegex(launcher.StartupError, 'BeautyCore is not ready'):
                launcher.verify_beautycore()

    def test_authenticated_mode_refuses_lan_instead_of_exposing_private_backend(self):
        with patch.object(launcher, 'find_adb', return_value=None), \
                patch.object(launcher, 'network_inventory') as network, \
                self.assertRaisesRegex(launcher.StartupError, 'USB'):
            launcher.choose_connection(3000, usb_only=True)
        network.assert_not_called()

    def test_beautycore_connection_exports_only_application_origin_and_owned_reverse_cleanup(self):
        connection = launcher.Connection('USB/ADB', '127.0.0.1', 'test phone', 'adb', 'phone')
        connection.api_port = 3000
        connection.created = ['tcp:3000', 'tcp:8081']
        with patch.dict(os.environ, {'JWT_SECRET': 'never-public', 'AI_FASTAPI_URL': 'private', 'KAGGLE_KEY': 'private'}, clear=True):
            _, expo = launcher.child_environments(connection)
        self.assertEqual(expo['EXPO_PUBLIC_API_BASE_URL'], 'http://127.0.0.1:3000')
        self.assertEqual(expo['EXPO_NO_DOTENV'], '1')
        for key in ('JWT_SECRET', 'AI_FASTAPI_URL', 'KAGGLE_KEY'):
            self.assertNotIn(key, expo)

    def test_route_metric_and_physical_adapter_determine_source(self):
        data = inventory()
        # Virtual default route has a better metric but is not a usable LAN.
        for key, rows in inventory().items():
            virtual = copy.deepcopy(rows[0])
            for field in ('InterfaceIndex', 'ifIndex'):
                if field in virtual:
                    virtual[field] = 29
            if key == 'adapters':
                virtual.update(Name='Hyper-V', HardwareInterface=False, Virtual=True)
            if key == 'interfaces':
                virtual['InterfaceMetric'] = 1
            if key == 'addresses':
                virtual['IPAddress'] = '172.27.192.1'
            data[key].insert(0, virtual)
        self.assertEqual(launcher.select_lan(data), ('192.168.1.5', 'Wi-Fi'))
        # A second physical route wins only through its effective metric.
        for key, rows in inventory().items():
            second = copy.deepcopy(rows[0])
            for field in ('InterfaceIndex', 'ifIndex'):
                if field in second:
                    second[field] = 23
            if key == 'adapters':
                second['Name'] = 'Ethernet'
            if key == 'interfaces':
                second['InterfaceMetric'] = 5
            if key == 'addresses':
                second['IPAddress'] = '192.168.1.9'
            data[key].append(second)
        self.assertEqual(launcher.select_lan(data), ('192.168.1.9', 'Ethernet'))
        data['interfaces'][-1]['InterfaceMetric'] = 45
        with self.assertRaisesRegex(launcher.StartupError, 'equal priority'):
            launcher.select_lan(data)

    def test_unusable_and_ambiguous_networks_fail_closed(self):
        changes = [('profiles', 'Category', 'Public'), ('adapters', 'State', 'Disconnected'),
                   ('adapters', 'Virtual', True), ('addresses', 'IPAddress', '8.8.8.8'),
                   ('addresses', 'IPAddress', '169.254.1.2'), ('addresses', 'SkipAsSource', True),
                   ('interfaces', 'State', 'Disconnected'), ('routes', 'NextHop', '0.0.0.0')]
        for key, field, value in changes:
            with self.subTest(key=key, field=field, value=value):
                data = inventory()
                data[key][0][field] = value
                with self.assertRaisesRegex(launcher.StartupError, 'No usable trusted LAN'):
                    launcher.select_lan(data)
        data = inventory()
        data['addresses'].append(dict(data['addresses'][0], IPAddress='192.168.1.8'))
        with self.assertRaises(launcher.StartupError):
            launcher.select_lan(data)

    def test_usb_filters_authorization_reverses_both_ports_and_preserves_existing(self):
        devices = 'List of devices attached\nno unauthorized\noff offline\nphone device usb:1\n'
        responses = [devices, 'UsbFfs tcp:8001 tcp:8001\n', '',
                     'UsbFfs tcp:8001 tcp:8001\nUsbFfs tcp:8081 tcp:8081\n']
        with patch.object(launcher, 'find_adb', return_value='adb'), \
                patch.object(launcher, 'adb_call', side_effect=responses) as call, \
                patch.object(launcher, 'network_inventory') as lan:
            connection = launcher.choose_connection()
            self.assertEqual(connection.origin, 'http://127.0.0.1:8001')
            self.assertEqual(connection.device, 'phone')
            self.assertEqual(connection.created, ['tcp:8081'])
            self.assertIn(('adb', '-s', 'phone', 'reverse', '--no-rebind', 'tcp:8081', 'tcp:8081'),
                          [args.args for args in call.call_args_list])
            lan.assert_not_called()
        with patch.object(launcher, 'adb_call', side_effect=[
                'UsbFfs tcp:8001 tcp:8001\nUsbFfs tcp:8081 tcp:8081', '']) as call:
            connection.cleanup()
            self.assertEqual(call.call_args.args[-2:], ('--remove', 'tcp:8081'))
            self.assertEqual(call.call_count, 2)

    def test_reverse_conflict_and_unavailable_adb_fall_back_without_overwriting(self):
        cases = [launcher.StartupError('ADB unavailable'),
                 ['phone device', 'UsbFfs tcp:8001 tcp:9999']]
        for case in cases:
            with self.subTest(case=case), patch.object(launcher, 'find_adb', return_value='adb'), \
                    patch.object(launcher, 'adb_call', side_effect=case) as call, \
                    patch.object(launcher, 'network_inventory', return_value=inventory()), \
                    patch('sys.stdout', new=StringIO()):
                connection = launcher.choose_connection()
                self.assertEqual(connection.mode, 'LAN')
                self.assertTrue(all('--remove' not in args.args and '--no-rebind' not in args.args
                                    for args in call.call_args_list))

    def test_failed_second_reverse_removes_only_new_first_mapping(self):
        responses = ['phone device', '', '', launcher.StartupError('second port failed'),
                     'UsbFfs tcp:8001 tcp:8001', '']
        with patch.object(launcher, 'find_adb', return_value='adb'), \
                patch.object(launcher, 'adb_call', side_effect=responses) as call, \
                patch.object(launcher, 'network_inventory', return_value=inventory()), \
                patch('sys.stdout', new=StringIO()):
            self.assertEqual(launcher.choose_connection().mode, 'LAN')
            self.assertEqual(call.call_args.args[-2:], ('--remove', 'tcp:8001'))

    def test_cleanup_does_not_remove_changed_reverse(self):
        connection = launcher.Connection('USB/ADB', '127.0.0.1', 'phone', 'adb', 'phone', ['tcp:8081'])
        with patch.object(launcher, 'adb_call', return_value='UsbFfs tcp:8081 tcp:9999') as call:
            connection.cleanup()
            self.assertEqual(call.call_count, 1)

    def test_environment_is_process_only_whitelisted_and_mock(self):
        original = {'PATH': 'test', 'KAGGLE_KEY': 'private', 'GEMINI_API_KEY': 'private',
                    'EXPO_PUBLIC_OLD_SECRET': 'private', 'EXPO_PUBLIC_API_BASE_URL': 'stale', 'CI': '1'}
        with patch.dict(os.environ, original, clear=True):
            backend, expo = launcher.child_environments(launcher.Connection('LAN', '192.168.1.5', 'Wi-Fi'))
            self.assertEqual(dict(os.environ), original)
        self.assertEqual(expo['EXPO_PUBLIC_API_BASE_URL'], 'http://192.168.1.5:8001')
        self.assertEqual(expo['EXPO_NO_DOTENV'], '1')
        self.assertEqual(expo['REACT_NATIVE_PACKAGER_HOSTNAME'], '192.168.1.5')
        self.assertEqual(backend['GENERATION_ENGINE'], 'mock')
        for key in ('KAGGLE_KEY', 'GEMINI_API_KEY', 'EXPO_PUBLIC_OLD_SECRET', 'CI'):
            self.assertNotIn(key, expo)
            self.assertNotIn(key, backend)

    def test_health_requires_this_mock_backend_and_reports_exit_or_timeout(self):
        self.assertTrue(launcher.api_healthy('{"status":"ok","generator":"mock"}'))
        self.assertFalse(launcher.api_healthy('{"status":"ok","generator":"remote_flux"}'))
        process = Mock(returncode=1)
        process.poll.return_value = 1
        with self.assertRaisesRegex(launcher.StartupError, 'exited during startup'):
            launcher.wait_ready(process, 'http://unused', lambda _: True, 'Expo', threading.Event(), 1)
        process.poll.return_value = None
        with patch.object(launcher, 'read_url', return_value='wrong'), \
                self.assertRaisesRegex(launcher.StartupError, 'did not become healthy'):
            launcher.wait_ready(process, 'http://unused', lambda _: False, 'FastAPI', threading.Event(), 0.01)
        stop = threading.Event()
        stop.set()
        with self.assertRaisesRegex(launcher.StartupError, 'stopped by STOP_MOBILE'):
            launcher.wait_ready(process, 'http://unused', lambda _: True, 'Expo', stop, 1)

    def test_controller_requires_token_and_matching_session_before_stop(self):
        controller = launcher.Controller()
        try:
            record = {'session': controller.session, 'token': controller.token,
                      'port': controller.server.server_port}
            launcher.contact(record)
            with self.assertRaises(HTTPError):
                launcher.contact(dict(record, token='x' * 64), 'POST')
            with self.assertRaisesRegex(launcher.StartupError, 'identity mismatch'):
                launcher.contact(dict(record, session='x' * 32))
            self.assertFalse(controller.stop.is_set())
            launcher.contact(record, 'POST')
            self.assertTrue(controller.stop.wait(1))
        finally:
            controller.close()

    def test_invalid_or_foreign_ownership_cannot_authorize_stop(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(launcher, 'STATE', Path(directory) / 'control.json'):
            launcher.STATE.write_text('{"port":true,"token":"wrong","session":"wrong"}')
            with self.assertRaisesRegex(launcher.StartupError, 'Invalid mobile ownership'):
                launcher.stop_session()
        record = {'port': 12345, 'token': 'x' * 64, 'session': 'x' * 32}
        with patch.object(launcher, 'read_url', return_value='[]'), \
                self.assertRaisesRegex(launcher.StartupError, 'identity mismatch'):
            launcher.contact(record)

    @unittest.skipUnless(os.name == 'nt', 'Windows process ownership acceptance')
    def test_occupied_port_fails_and_keeps_unrelated_listener_alive(self):
        with socket.socket() as sentinel:
            sentinel.bind(('127.0.0.1', 0))
            sentinel.listen()
            with patch.object(launcher, 'API_PORT', sentinel.getsockname()[1]):
                with self.assertRaisesRegex(launcher.StartupError, 'occupied'):
                    launcher.require_free_ports()
            with socket.create_connection(sentinel.getsockname(), timeout=1):
                pass

    @unittest.skipUnless(os.name == 'nt', 'Windows process ownership acceptance')
    def test_job_close_kills_owned_child_and_grandchild_only(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'child.json'
            code = ('import subprocess,sys,json,time; '
                    'p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(120)"]); '
                    f'open({str(marker)!r},"w").write(json.dumps(p.pid)); time.sleep(120)')
            sentinel = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(120)'])
            job = launcher.WindowsJob()
            try:
                process = launcher.start_child(job, [sys.executable, '-c', code], directory,
                                               launcher.base_environment())
                deadline = time.monotonic() + 10
                while not marker.exists() and time.monotonic() < deadline:
                    time.sleep(0.1)
                self.assertTrue(marker.exists(), 'Suspended child did not resume')
                pid = json.loads(marker.read_text())
                api = launcher.ctypes.WinDLL('kernel32', use_last_error=True)
                api.OpenProcess.argtypes = [launcher.wintypes.DWORD, launcher.wintypes.BOOL, launcher.wintypes.DWORD]
                api.OpenProcess.restype = launcher.wintypes.HANDLE
                api.WaitForSingleObject.argtypes = [launcher.wintypes.HANDLE, launcher.wintypes.DWORD]
                api.CloseHandle.argtypes = [launcher.wintypes.HANDLE]
                handle = api.OpenProcess(0x100000, False, pid)
                self.assertTrue(handle)
                try:
                    job.close()
                    process.wait(timeout=5)
                    self.assertEqual(api.WaitForSingleObject(handle, 5000), 0)
                    self.assertIsNone(sentinel.poll(), 'Unrelated process was stopped')
                finally:
                    api.CloseHandle(handle)
            finally:
                job.close()
                sentinel.terminate()
                sentinel.wait(timeout=5)


if __name__ == '__main__':
    unittest.main()

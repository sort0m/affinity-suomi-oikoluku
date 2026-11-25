"""Integration smoke test of the actual frozen Windows distribution."""
from pathlib import Path
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / 'Affinity-suomi-ilman-Python-asennusta-1.7.1.zip'
TEST_ROOT = Path(os.environ.get('VOIKKO_TEST_ROOT', ROOT / '.work/VoikkoTest')).resolve()


@unittest.skipUnless(os.name == 'nt' and ARCHIVE.exists(), 'Build the Windows EXE package first')
class PortableExeTest(unittest.TestCase):
    def unpack_and_run(self, parent, subfolder):
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='exe-smoke-', dir=parent) as temp:
            self.check_lifecycle(Path(temp) / subfolder)

    def test_ascii_installation(self):
        if not str(TEST_ROOT).isascii():
            self.skipTest(r'Set VOIKKO_TEST_ROOT to a writable ASCII path, e.g. C:\VoikkoTest')
        self.unpack_and_run(TEST_ROOT, 'portable')

    def test_accented_installation(self):
        self.unpack_and_run(TEST_ROOT / 'Äänekoski', 'portable')

    def test_unicode_installation_under_profile(self):
        profile = Path.home().resolve()
        # The temp directory is usually in the profile and may be redirected.
        parent = Path(tempfile.gettempdir()).resolve()
        if not parent.is_relative_to(profile):
            parent = profile
        self.unpack_and_run(parent, 'Käyttäjä-東京')

    def test_missing_dictionary_reports_path_and_cause(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'Rikkinäinen'
            with zipfile.ZipFile(ARCHIVE) as archive:
                archive.extractall(folder)
            app = folder / 'Affinity-suomi'
            assets = app / '_internal/assets'
            (assets / '5/mor-standard/mor.vfst').unlink()
            data = app / 'data'
            data.mkdir()
            private_word = 'vainhenkilökohtaisessasanastossa'
            (data / 'user_words.txt').write_text(private_word, encoding='utf-8')
            result = subprocess.run([str(app / 'Affinity-oikoluku.exe'), '--quiet', '--port', '0'],
                                    cwd=folder, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(result.returncode, 1)
            token = (data / 'key.txt').read_text(encoding='ascii').strip()
            self.assertEqual(len(token), 64)
            report = (data / 'Voikko-vianetsinta.txt').read_text(encoding='utf-8')
            self.assertFalse(token in report, 'Report disclosed the service key')
            self.assertFalse(private_word in report, 'Report disclosed a personal dictionary entry')
            self.assertIn(str(assets.resolve()).casefold(), report.casefold())
            self.assertIn('mor.vfst', report)
            self.assertIn('Sanastotiedostojen tarkistus', report)

    def check_lifecycle(self, folder):
        with zipfile.ZipFile(ARCHIVE) as archive:
            self.assertIsNone(archive.testzip())
            self.assertFalse(any(n.endswith(('key.txt', 'Tarkista-suomi.js')) for n in archive.namelist()))
            archive.extractall(folder)
        app = folder / 'Affinity-suomi'
        exe = app / 'Affinity-oikoluku.exe'
        env = os.environ.copy()
        env['PATH'] = str(Path(os.environ['SystemRoot']) / 'System32')
        env['PYTHONHOME'] = str(folder / 'no-python-installed')
        env['PYTHONPATH'] = str(folder / 'no-python-packages')
        env.pop('VOIKKO_DICTIONARY_PATH', None)
        env.pop('VOIKKO_DICTIONARY', None)
        self.assertIsNone(shutil.which('python', path=env['PATH']))
        self.assertIsNone(shutil.which('pythonw', path=env['PATH']))
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        command = [str(exe), '--quiet', '--port', str(port)]
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        def call(path, token, method='GET'):
            request = urllib.request.Request(f'http://127.0.0.1:{port}' + path,
                                             headers={'X-Voikko-Key': token}, method=method)
            with opener.open(request, timeout=2) as response:
                return json.load(response)

        def start():
            process = subprocess.Popen(command, env=env, cwd=folder,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                try:
                    token = (app / 'data/key.txt').read_text(encoding='ascii')
                    if call('/health', token) == {'service': 'affinity-voikko', 'protocol': 1}:
                        return process, token
                except (OSError, ValueError):
                    pass
                if process.poll() is not None:
                    self.fail(f'Frozen helper exited early: {process.returncode}')
                time.sleep(0.1)
            process.kill()
            process.wait(timeout=5)
            self.fail('Frozen helper did not start within 20 seconds')

        process, token = start()
        try:
            generated = (app / 'Tarkista-suomi.js').read_text(encoding='utf-8')
            self.assertNotIn('__VOIKKO_KEY__', generated)
            self.assertIn(f'127.0.0.1:{port}', generated)
            query = urllib.parse.urlencode({'words': json.dumps(['mahdollisuutta', 'maahdollisuutta', 'äiti'])})
            result = call('/check?' + query, token)
            self.assertEqual([r['correct'] for r in result['results']], [True, False, True])
            result = call('/suggest?word=maahdollisuutta', token)
            self.assertIn('mahdollisuutta', result['suggestions'])
            new_word = 'kisssamaailma'
            query = urllib.parse.urlencode({'words': json.dumps([new_word])})
            self.assertFalse(call('/check?' + query, token)['results'][0]['correct'])
            self.assertEqual(call('/add?word=' + new_word, token, 'POST'), {'added': True})
            self.assertTrue(call('/check?' + query, token)['results'][0]['correct'])
            with self.assertRaises(urllib.error.HTTPError) as denied:
                call('/health', 'wrong-key')
            with denied.exception as response:
                self.assertEqual(response.code, 403)
            duplicate = subprocess.run(command, env=env, cwd=folder, timeout=30,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(duplicate.returncode, 0)
            self.assertIsNone(process.poll())
            # A fresh second installation has a different key and must not
            # start another listener on the port or stop the existing one.
            other_folder = folder / 'second-installation'
            with zipfile.ZipFile(ARCHIVE) as archive:
                archive.extractall(other_folder)
            other_exe = other_folder / 'Affinity-suomi/Affinity-oikoluku.exe'
            conflict = subprocess.run([str(other_exe), '--quiet', '--port', str(port)],
                                      env=env, cwd=folder, timeout=10,
                                      creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(conflict.returncode, 1)
            wrong_stop = subprocess.run([str(other_exe), '--stop', '--quiet', '--port', str(port)],
                                       env=env, cwd=folder, timeout=10,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(wrong_stop.returncode, 1, 'A different installation must not report a successful stop')
            self.assertEqual(call('/health', token)['service'], 'affinity-voikko')
            stopped = subprocess.run(command + ['--stop'], env=env, cwd=folder,
                                     timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(stopped.returncode, 0)
            self.assertEqual(process.wait(timeout=5), 0)
            process, restarted_token = start()
            self.assertEqual(restarted_token, token)
            self.assertTrue(call('/check?' + query, token)['results'][0]['correct'])
            self.assertIn(new_word, (app / 'data/user_words.txt').read_text(encoding='utf-8'))
            self.assertEqual((app / 'Tarkista-suomi.js').read_text(encoding='utf-8'), generated)
            self.assertEqual((app / 'fi_FI/hyph_fi_FI.dic').read_bytes(),
                             (ROOT / 'hyph_fi_FI.dic').read_bytes())
        finally:
            try:
                call('/shutdown', token)
                process.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                process.kill()
                process.wait(timeout=5)


if __name__ == '__main__':
    unittest.main(verbosity=2)

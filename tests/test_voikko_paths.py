"""Windows integration tests with the DLL, Python binding and v5 dictionary from setup.py."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1] / 'voikko'
RUNTIME = SOURCE / 'runtime'
SPELL_PROBE = """
import json
from pathlib import Path
import sys
sys.path.insert(0, sys.argv[1])
from server import Checker

cwd = Path.cwd()
checker = Checker()
try:
    print(json.dumps([checker.spell('äiti'), checker.spell('maahdollisuutta'),
                      checker.suggest('maahdollisuutta'), Path.cwd() == cwd]))
finally:
    checker.close()
"""


@unittest.skipUnless(os.name == 'nt' and (RUNTIME / 'libvoikko-1.dll').is_file(),
                     'Run voikko/setup.py on Windows to install the native test dependency')
class NativePathTests(unittest.TestCase):
    def installation_parent(self):
        base = Path(os.environ.get('VOIKKO_TEST_ROOT', tempfile.gettempdir())).resolve()
        base.mkdir(parents=True, exist_ok=True)
        return base

    def make_install(self, app):
        # Copy only source and shipped assets, never the developer's key or user data.
        assets = app / 'runtime'
        assets.mkdir(parents=True)
        for source in SOURCE.glob('*.py'):
            shutil.copyfile(source, app / source.name)
        shutil.copyfile(SOURCE / 'affinity-voikko.js', app / 'affinity-voikko.js')
        for name in ('libvoikko-1.dll', 'libvoikko.py'):
            shutil.copyfile(RUNTIME / name, assets / name)
        shutil.copytree(RUNTIME / '5', assets / '5')
        return assets

    def run_python(self, app, *args):
        # A separate process for each installation releases the mapped files and
        # cannot accidentally reuse the DLL or binding from a previous test.
        work = app.parent / 'unrelated-working-directory'
        work.mkdir(exist_ok=True)
        tmp = app / 'temp'
        tmp.mkdir(exist_ok=True)
        env = dict(os.environ, PATH=str(Path(os.environ['SystemRoot']) / 'System32'),
                   TEMP=str(tmp), TMP=str(tmp), LOCALAPPDATA=str(tmp), APPDATA=str(tmp))
        env.pop('VOIKKO_DICTIONARY_PATH', None)
        env.pop('VOIKKO_DICTIONARY', None)
        return subprocess.run([sys.executable, '-E', '-S', '-X', 'utf8', *args],
                              cwd=work, env=env, capture_output=True, encoding='utf-8',
                              timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)

    def check_spelling_from(self, install):
        self.make_install(install)
        result = self.run_python(install, '-c', SPELL_PROBE, install)
        self.assertEqual(result.returncode, 0, result.stderr)
        correct, typo, suggestions, cwd_restored = json.loads(result.stdout)
        self.assertTrue(correct)
        self.assertFalse(typo)
        self.assertIn('mahdollisuutta', suggestions)
        self.assertTrue(cwd_restored, 'Initialisation changed the caller\'s working directory')

    def test_ascii_installation(self):
        # On a Unicode-only profile, set VOIKKO_TEST_ROOT to a writable ASCII
        # directory (e.g. C:\VoikkoTest) to exercise the ASCII control case.
        base = self.installation_parent()
        if not str(base).isascii():
            self.skipTest('An ASCII parent is needed for this control. Set VOIKKO_TEST_ROOT.')
        with tempfile.TemporaryDirectory(dir=base) as folder:
            self.check_spelling_from(Path(folder) / 'VoikkoTest')

    def test_finnish_installation(self):
        with tempfile.TemporaryDirectory(dir=self.installation_parent()) as folder:
            self.check_spelling_from(Path(folder) / 'VoikkoTest' / 'Äänekoski')

    def test_unicode_installation_in_user_profile(self):
        base = Path(tempfile.gettempdir()).resolve()
        if not base.is_relative_to(Path.home()):
            base = Path.home()
        with tempfile.TemporaryDirectory(dir=base) as folder:
            self.check_spelling_from(Path(folder) / 'Käyttäjä' / 'Oikoluku 東京 🐈')

    def test_diagnostics_for_broken_installations(self):
        for broken in ('libvoikko-1.dll', '5/mor-standard/mor.vfst', '5/mor-standard/index.txt'):
            with self.subTest(broken=broken), tempfile.TemporaryDirectory() as folder:
                app = Path(folder) / 'Käyttäjä'
                assets = self.make_install(app)
                damaged = assets / broken
                if damaged.name == 'index.txt':
                    damaged.write_text('invalid dictionary format\n', encoding='ascii')
                else:
                    damaged.unlink()
                data = app / 'data'
                data.mkdir()
                test_key = 'b7' * 32
                user_word = 'Yksityistesti'
                (data / 'key.txt').write_text(test_key, encoding='ascii')
                (data / 'user_words.txt').write_text(user_word, encoding='utf-8')
                result = self.run_python(app, app / 'portable.py', '--quiet', '--port', '0')
                self.assertEqual(result.returncode, 1, result.stderr)
                report = (data / 'Voikko-vianetsinta.txt').read_text(encoding='utf-8')
                self.assertIn(f"DLL: {assets.resolve() / 'libvoikko-1.dll'}", report)
                self.assertIn(f'Sanaston juuri: {assets.resolve()}', report)
                reason = next(line for line in report.splitlines() if line.startswith('Syy:'))
                self.assertIn(damaged.name, reason)
                if damaged.name == 'index.txt':
                    self.assertIn('SHA-256', reason)
                self.assertNotIn(test_key, report)
                self.assertNotIn(user_word, report)


if __name__ == '__main__':
    unittest.main(verbosity=2)

"""Build Windows x64 portable distribution using PyInstaller 6.19.0."""
from pathlib import Path
from importlib.metadata import distribution
from hashlib import sha256
import shutil
import subprocess
import sys
import zipfile
from build_voikko_icon import make_icon

ROOT = Path(__file__).resolve().parent.parent
VOIKKO_SOURCES = {
    'libvoikko-4.3+win1.tar.gz': '594480de1e3611c63d20c2e1d159041aed18ca458dd272e9d7daa783362f4f89',
    'voikko-fi-snapshot.tar.gz': 'a22dc3f9d506e7d7d2022d7854abcae459818df0bd7a9de016e78992f4f535c1',
}


def main():
    if sys.platform != 'win32':
        raise SystemExit('Build this Windows distribution on Windows x64.')
    runtime = ROOT / 'voikko/runtime'
    for name in ['libvoikko-1.dll', 'libvoikko.py', '5/mor-standard/mor.vfst']:
        if not (runtime / name).is_file():
            raise SystemExit('Run voikko/setup.py before building.')
    work = ROOT / '.work/portable-build'
    dist = ROOT / 'dist/1.7'
    work.mkdir(parents=True, exist_ok=True)
    icon_path = work / 'voikko.ico'
    make_icon(icon_path)
    for path in (work, dist / 'Affinity-oikoluku'):
        if not path.resolve().is_relative_to(ROOT.resolve()):
            raise RuntimeError('Build output must remain inside the workspace.')
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
               '--onedir', '--windowed', '--noupx', '--name', 'Affinity-oikoluku',
               '--icon', str(icon_path),
               '--distpath', str(dist), '--workpath', str(work / 'work'),
               '--specpath', str(work), '--paths', str(runtime),
               '--hidden-import', 'libvoikko',
               '--add-binary', f'{runtime / "libvoikko-1.dll"};assets',
               '--add-data', f'{runtime / "5"};assets/5',
               '--add-data', f'{ROOT / "voikko/affinity-voikko.js"};assets',
               '--add-data', f'{icon_path};assets',
               str(ROOT / 'voikko/portable.py')]
    subprocess.run(command, check=True, cwd=ROOT)
    package = dist / 'Affinity-oikoluku'
    (package / 'fi_FI').mkdir(exist_ok=True)
    shutil.copy2(ROOT / 'hyph_fi_FI.dic', package / 'fi_FI/hyph_fi_FI.dic')
    shutil.copy2(ROOT / 'voikko/PORTABLE.txt', package / 'LUE-ENSIN.txt')
    (package / 'Pysayta-Affinity-oikoluku.cmd').write_text(
        '@echo off\nstart "" "%~dp0Affinity-oikoluku.exe" --stop\n', encoding='ascii')
    licenses = package / 'Lisenssit'
    licenses.mkdir(exist_ok=True)
    shutil.copy2(ROOT / 'LICENSE', licenses / 'Projekti-GPL3.txt')
    shutil.copy2(ROOT / 'LISENSSIT-JA-LAHTEET.md', licenses / 'LISENSSIT-JA-LAHTEET.md')
    shutil.copy2(Path(sys.base_prefix) / 'LICENSE.txt', licenses / 'Python.txt')
    shutil.copy2(runtime / 'libvoikko.py', licenses / 'libvoikko-rajapinta.py')
    for name, expected in VOIKKO_SOURCES.items():
        source_file = ROOT / 'kolmannen_osapuolen_lahdekoodi' / name
        if not source_file.is_file() or sha256(source_file.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f'Voikko source archive missing or changed: {name}')
        shutil.copy2(source_file, licenses / name)
    pyinstaller = distribution('pyinstaller')
    copying = next(p for p in pyinstaller.files if str(p).endswith('licenses/COPYING.txt'))
    shutil.copy2(pyinstaller.locate_file(copying), licenses / 'PyInstaller.txt')
    # Include application source with the license and reproducible build script.
    with zipfile.ZipFile(licenses / 'Sovelluksen-lahdekoodi.zip', 'w', zipfile.ZIP_DEFLATED) as source:
        for name in ['README.md', 'LICENSE', 'LISENSSIT-JA-LAHTEET.md',
                     'Kaynnista-Affinity-oikoluku.cmd', 'Pysayta-Affinity-oikoluku.cmd',
                     'voikko/portable.py', 'voikko/tray.py', 'voikko/server.py',
                     'voikko/setup.py', 'voikko/manage.py', 'voikko/launch.ps1',
                     'voikko/affinity-voikko.js', 'voikko/PORTABLE.txt',
                     'tools/build_portable.py', 'tools/build_voikko_icon.py',
                     'tools/build_hyphenation.py', 'tests/test_voikko.py',
                     'tests/test_voikko_script.cjs', 'tests/test_portable_exe.py',
                     'hyph_fi_FI.dic',
                     'hyphenation_patterns.txt']:
            source.write(ROOT / name, name)
    archive = ROOT / 'Affinity-suomi-ilman-Python-asennusta-1.7.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as output:
        for path in sorted(package.rglob('*')):
            if path.is_file():
                if path.name in ('key.txt', 'Tarkista-suomi.js', 'user_words.txt') or (package / 'data') in path.parents:
                    raise RuntimeError('Do not package a previously initialised application.')
                output.write(path, Path('Affinity-suomi') / path.relative_to(package))
    print('Archive:', archive)
    print('Size MiB:', round(archive.stat().st_size / 1024**2, 2))


if __name__ == '__main__':
    main()

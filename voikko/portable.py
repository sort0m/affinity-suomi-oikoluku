"""Standalone Windows entry point. Bundled runtime; no installed Python needed."""
from pathlib import Path
import argparse
import ctypes
import http.client
import json
import os
import secrets
import socket
import sys
import threading
import time

import server
from tray import TrayIcon


def locations():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent, Path(sys._MEIPASS) / 'assets'
    return Path(__file__).resolve().parent, Path(__file__).resolve().parent / 'runtime'


def notify(message, error=False, quiet=False):
    if not quiet:
        ctypes.windll.user32.MessageBoxW(None, message, 'Affinity-oikoluku',
                                       0x10 if error else 0x40)


def request(port, token, path):
    # Only loopback HTTP is needed. Avoid proxy and TLS initialisation entirely.
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=2)
    try:
        connection.request('GET', path, headers={'X-Voikko-Key': token})
        response = connection.getresponse()
        if response.status != 200:
            raise OSError('Local Voikko service did not accept this instance.')
        return json.loads(response.read())
    finally:
        connection.close()


def is_running(port, token):
    try:
        return request(port, token, '/health') == {'service': 'affinity-voikko', 'protocol': 1}
    except (OSError, ValueError):
        return False


def port_in_use(port):
    with socket.socket() as probe:
        probe.settimeout(0.3)
        return probe.connect_ex(('127.0.0.1', port)) == 0


def stop_service(root, port):
    keyfile = root / 'data/key.txt'
    token = keyfile.read_text(encoding='ascii').strip() if keyfile.exists() else ''
    if not is_running(port, token):
        if port_in_use(port):
            raise RuntimeError('Porttia käyttää toinen Affinity-oikoluku tai muu ohjelma.\n'
                               'Tämä pysäytin ei pysäyttänyt sitä.\n\n'
                               'Käytä sen kansion Pysayta-Affinity-oikoluku.cmd-tiedostoa,\n'
                               'josta käynnistit aiemman tarkistimen.')
        return 'Tämän kansion Affinity-oikoluku ei ollut käynnissä.'
    request(port, token, '/shutdown')
    deadline = time.monotonic() + 3
    while port_in_use(port) and time.monotonic() < deadline:
        time.sleep(0.1)
    if port_in_use(port):
        raise RuntimeError('Pysäytyspyyntö lähetettiin, mutta portti on vielä varattu.\n'
                           'Sulje mahdollinen Voikon käynnistysilmoitus ja yritä uudelleen.')
    return 'Affinity-oikoluku on pysäytetty.'


def initialise(root, assets, port):
    data = root / 'data'
    data.mkdir(exist_ok=True)
    keyfile = data / 'key.txt'
    try:
        with keyfile.open('x', encoding='ascii') as output:
            output.write(secrets.token_hex(32))
    except FileExistsError:
        pass
    token = keyfile.read_text(encoding='ascii').strip()
    if len(token) != 64 or any(c not in '0123456789abcdef' for c in token):
        raise ValueError('data/key.txt ei sisällä kelvollista avainta.')
    template_path = assets / 'affinity-voikko.js'
    if not getattr(sys, 'frozen', False):
        template_path = root / 'affinity-voikko.js'
    script = template_path.read_text(encoding='utf-8')
    script = script.replace('"__VOIKKO_KEY__"', json.dumps(token))
    script = script.replace('127.0.0.1:17655', f'127.0.0.1:{port}')
    target = root / 'Tarkista-suomi.js'
    if not target.exists() or target.read_text(encoding='utf-8') != script:
        temporary = root / f'.script-{os.getpid()}.tmp'
        try:
            temporary.write_text(script, encoding='utf-8', newline='\n')
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    return token


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stop', action='store_true')
    parser.add_argument('--quiet', action='store_true')
    parser.add_argument('--port', type=int, default=server.PORT)
    args = parser.parse_args()
    root, assets = locations()
    try:
        if args.stop:
            notify(stop_service(root, args.port), quiet=args.quiet)
            return 0
        token = initialise(root, assets, args.port)
        if is_running(args.port, token):
            notify('Affinity-oikoluku on jo käynnissä.\nAja Affinityssä Tarkista suomi -skripti.', quiet=args.quiet)
            return 0
        server.RUNTIME = assets
        checker = server.Checker(root / 'data/user_words.txt')
        try:
            try:
                httpd = server.make_server(checker, token, args.port)
            except OSError as error:
                if is_running(args.port, token):
                    return 0  # Another simultaneous launch won the bind race.
                raise RuntimeError('Oikoluvun paikallinen portti on varattu.\n'
                                   'Sulje aiemmin käynnistetty Affinity-oikoluku ja yritä uudelleen.') from error
            with httpd:
                tray = TrayIcon(root, assets / 'voikko.ico')
                def serve():
                    try:
                        httpd.serve_forever(poll_interval=0.25)
                    finally:
                        # Release the port even while the startup notice is open.
                        httpd.server_close()
                        tray.close()
                worker = threading.Thread(target=serve, daemon=True)
                worker.start()
                try:
                    tray.run()
                finally:
                    httpd.shutdown()
                    worker.join()
                    tray.dispose()
        finally:
            checker.close()
        return 0
    except Exception as error:
        # No document content or key is written to disk.
        message = 'Affinity-oikoluvun pysäytys ei onnistunut.' if args.stop else 'Affinity-oikoluku ei käynnistynyt.'
        notify(message + '\n\n' + str(error), error=True, quiet=args.quiet)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

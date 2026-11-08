"""Start/stop/status helper; starts the checker hidden, without installing a service."""
from pathlib import Path
import argparse
import json
import http.client
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / "runtime"


def call(path):
    token = (RUNTIME / "key.txt").read_text(encoding="ascii").strip()
    connection = http.client.HTTPConnection('127.0.0.1', 17655, timeout=2)
    try:
        connection.request('GET', path, headers={'X-Voikko-Key': token})
        response = connection.getresponse()
        if response.status != 200:
            raise OSError('Palvelu ei hyväksynyt tämän kansion avainta.')
        return json.loads(response.read())
    finally:
        connection.close()


def port_in_use():
    with socket.socket() as probe:
        probe.settimeout(0.3)
        return probe.connect_ex(('127.0.0.1', 17655)) == 0


def running():
    try:
        health = call("/health")
        return health == {"service": "affinity-voikko", "protocol": 1}
    except (OSError, ValueError):
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "stop", "status"])
    args = parser.parse_args()
    if args.action == "stop":
        if running():
            call("/shutdown")
            deadline = time.monotonic() + 3
            while port_in_use() and time.monotonic() < deadline:
                time.sleep(0.1)
            if port_in_use():
                raise SystemExit('Pysäytyspyyntö lähetettiin, mutta portti on vielä varattu.')
            print("Affinity-oikoluku pysäytetty.")
        elif port_in_use():
            raise SystemExit('Porttia käyttää toinen asennus. Käytä sen oman kansion pysäytintä.')
        else:
            print("Affinity-oikoluku ei ollut käynnissä.")
        return
    if args.action == "status":
        print("Affinity-oikoluku on käynnissä." if running() else "Affinity-oikoluku ei ole käynnissä.")
        return
    from setup import main as setup
    setup()
    if running():
        print("Affinity-oikoluku on jo käynnissä.")
        return
    exe = Path(sys.executable)
    pythonw = exe.with_name("pythonw.exe")
    if sys.platform == "win32" and pythonw.exists():
        exe = pythonw
    with (RUNTIME / "service.log").open("wb") as log:
        process = subprocess.Popen([str(exe), str(ROOT / "server.py")],
            cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            start_new_session=sys.platform != "win32")
    for _ in range(30):
        if running():
            print("Affinity-oikoluku valmis. Aja Affinityssä Tarkista suomi -skripti.")
            return
        if process.poll() is not None:
            break
        time.sleep(0.1)
    raise SystemExit("Affinity-oikoluku ei käynnistynyt. Katso voikko/runtime/service.log.")


if __name__ == "__main__":
    main()

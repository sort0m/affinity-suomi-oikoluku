"""Download pinned official Voikko files and build the personal Affinity script."""
from hashlib import sha256
from pathlib import Path
import io
import json
import secrets
import struct
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / "runtime"
BASE = "https://www.puimula.org/htp/testing/voikko-sdk/win-crossbuild/libvoikko-4.3+win1/"
FILES = [
    (BASE + "win64/libvoikko-1.dll", "libvoikko-1.dll",
     "bfffd537ff372b425a61940d4f5ac6c80e2a745dab33cc00ac50e8f50441d1b0"),
    (BASE + "libvoikko.py", "libvoikko.py",
     "72f6e4e468dc47d8bde73825c6886d5001d954f72a0b35b47fae31d063ed8536"),
    ("https://www.puimula.org/htp/testing/voikko-snapshot-v5/dict.zip", "dict.zip",
     "98f26bb67e08288910fbf1aa92521f28bee79538ba86aefa267713333e7fa537"),
]


def main():
    if struct.calcsize("P") != 8:
        raise SystemExit("Tarvitaan 64-bittinen Python 3.")
    RUNTIME.mkdir(exist_ok=True)
    for url, name, expected in FILES:
        target = RUNTIME / name
        data = target.read_bytes() if target.exists() else b""
        if sha256(data).hexdigest() != expected:
            print("Ladataan:", name)
            with urllib.request.urlopen(url, timeout=60) as response:
                data = response.read()
            if sha256(data).hexdigest() != expected:
                raise SystemExit(f"Tarkistussumma ei vastaa tunnettua versiota: {name}")
            target.write_bytes(data)
        if name.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                for item in archive.infolist():
                    destination = (RUNTIME / item.filename).resolve()
                    if not destination.is_relative_to(RUNTIME.resolve()):
                        raise ValueError("Unsafe archive path")
                    if item.is_dir():
                        destination.mkdir(parents=True, exist_ok=True)
                        continue
                    contents = archive.read(item)
                    # Voikko memory-maps its dictionary while the helper runs.
                    # Rebuilding the script must not overwrite unchanged files.
                    if destination.exists() and destination.read_bytes() == contents:
                        continue
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(contents)
    keyfile = RUNTIME / "key.txt"
    if not keyfile.exists():
        keyfile.write_text(secrets.token_hex(32), encoding="ascii")
    token = keyfile.read_text(encoding="ascii").strip()
    template = (ROOT / "affinity-voikko.js").read_text(encoding="utf-8")
    with (ROOT / "Tarkista-suomi.js").open("w", encoding="utf-8", newline="\n") as output:
        output.write(template.replace('"__VOIKKO_KEY__"', json.dumps(token)))
    print("Valmis: Tarkista-suomi.js")


if __name__ == "__main__":
    main()

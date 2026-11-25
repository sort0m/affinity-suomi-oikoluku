"""Load the pinned Windows Voikko runtime used by both application entry points."""
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import os
import sys
import threading


LIBRARY_NAME = "libvoikko-1.dll"
LIBRARY_SHA256 = "bfffd537ff372b425a61940d4f5ac6c80e2a745dab33cc00ac50e8f50441d1b0"
DICTIONARY_FILES = {
    "5/mor-standard/index.txt": "880093301e91cfc96d3e2ec1143c70536e251127c45be444b051be13fa9659d6",
    "5/mor-standard/mor.vfst": "772853c7bd98756ac2f01e1366dc24c68e2fd8ba5e9a62193bb1d227a4d64d3b",
    "5/mor-standard/autocorr.vfst": "0c27f8f07bf23fcbfd92962335139817066786ec2694d72ddfa2ca091764a7e0",
}
_init_lock = threading.Lock()


class VoikkoStartupError(RuntimeError):
    """Safe to show to the user and write to the startup report."""


def _binding(root):
    if getattr(sys, "frozen", False):
        import libvoikko  # Embedded in the PyInstaller archive.
        return libvoikko
    spec = spec_from_file_location("libvoikko", root / "libvoikko.py")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _verify(path, expected):
    if sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f"Tiedoston SHA-256-tarkistussumma poikkeaa julkaisusta: {path}")


def load_voikko(root):
    root = Path(root).resolve()
    dll = root / LIBRARY_NAME
    stage = "Python-rajapinnan lataus"
    version = "ei ladattu"
    try:
        binding = _binding(root)
        if os.name != "nt":
            binding.Voikko.setLibrarySearchPath(str(root))
            return binding.Voikko("fi", path=str(root))

        stage = "DLL:n tarkistus ja lataus"
        _verify(dll, LIBRARY_SHA256)
        # Open the absolute filename first. The upstream search helper would
        # otherwise silently try a system DLL when the bundled one cannot load.
        library = binding.VoikkoLibrary(str(dll))
        version = library.voikkoGetVersion().decode("ascii")
        stage = "Sanastotiedostojen tarkistus"
        for name, expected in DICTIONARY_FILES.items():
            _verify(root / name, expected)

        stage = "Sanaston avaus (fi-x-standard, DLL:lle annettu polku: .)"
        # Both entry points initialise before starting any service or tray
        # threads. libvoikko 4.3 maps its VFST files during voikkoInit. Give
        # its ANSI file APIs only ASCII names, even on volumes without 8.3
        # aliases. Python changes directory with the wide Windows API.
        with _init_lock:
            binding.Voikko.setLibrarySearchPath(str(root))
            previous = Path.cwd()
            os.chdir(root)
            try:
                return binding.Voikko("fi-x-standard", path=b".")
            finally:
                os.chdir(previous)
    except Exception as error:
        raise VoikkoStartupError(
            f"Voikon alustus epäonnistui.\nSanaston juuri: {root}\n"
            f"DLL: {dll}\nLibvoikon versio: {version}\nVaihe: {stage}\nSyy: {error}"
        ) from error

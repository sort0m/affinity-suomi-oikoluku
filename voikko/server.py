"""Local, on-demand spelling service for the Affinity script. Python stdlib only."""
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import argparse
import hmac
import json
import os
import socket
import sys
import threading
import unicodedata
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / "runtime"
PORT = 17655


class Checker:
    def __init__(self, user_words_path=None, voikko=None):
        self.user_words_path = Path(user_words_path) if user_words_path else RUNTIME / "user_words.txt"
        self.user_words = set()
        if self.user_words_path.exists():
            self.user_words = {word_key(line.strip()) for line in
                               self.user_words_path.read_text(encoding="utf-8").splitlines()
                               if valid_word(line.strip())}
        if voikko is None:
            sys.path.insert(0, str(RUNTIME))
            from libvoikko import Voikko
            Voikko.setLibrarySearchPath(str(RUNTIME))
            voikko = Voikko("fi", path=str(RUNTIME))
        self.voikko = voikko

    @lru_cache(maxsize=4096)
    def spell(self, word):
        return word_key(word) in self.user_words or self.voikko.spell(unicodedata.normalize("NFC", word))

    def add_word(self, word):
        key = word_key(word)
        if key not in self.user_words:
            words = sorted(self.user_words | {key})
            self.user_words_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.user_words_path.with_name(self.user_words_path.name + ".tmp")
            try:
                temporary.write_text("\n".join(words) + "\n", encoding="utf-8", newline="\n")
                os.replace(temporary, self.user_words_path)
            finally:
                temporary.unlink(missing_ok=True)
            self.user_words.add(key)
            self.spell.cache_clear()
        return key

    @lru_cache(maxsize=512)
    def suggest(self, word):
        return self.voikko.suggest(unicodedata.normalize("NFC", word))[:8]

    def close(self):
        self.voikko.terminate()


def valid_word(word):
    return (isinstance(word, str) and 1 <= len(word) <= 100
            and any(c.isalpha() for c in word)
            and all(c.isalpha() or unicodedata.category(c).startswith("M")
                    or c in "-'’" for c in word))


def word_key(word):
    return unicodedata.normalize("NFC", word).casefold()


def make_server(checker, token, port=PORT):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self, *_):
            pass  # Never write document words, query strings or the key to logs.

        def send_json(self, status, value):
            data = json.dumps(value, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            self.handle_request("GET")

        def do_POST(self):
            self.handle_request("POST")

        def handle_request(self, method):
            if (self.headers.get("Origin") is not None
                    or self.headers.get("Sec-Fetch-Site") is not None
                    or self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}"
                    or not hmac.compare_digest(self.headers.get("X-Voikko-Key", "").encode("utf-8"),
                                               token.encode("ascii"))):
                self.send_json(403, {"error": "Access denied"})
                return
            if len(self.path) > 12000:
                self.send_json(413, {"error": "Request too large"})
                return
            parsed = urlsplit(self.path)
            try:
                if method == "POST" and parsed.path == "/add":
                    query = parse_qs(parsed.query, strict_parsing=True, max_num_fields=1)
                    word = query["word"][0]
                    if not valid_word(word):
                        raise ValueError("Invalid word")
                    checker.add_word(word)
                    self.send_json(200, {"added": True})
                elif method != "GET":
                    self.send_json(404, {"error": "Unknown endpoint"})
                elif parsed.path == "/health":
                    self.send_json(200, {"service": "affinity-voikko", "protocol": 1})
                elif parsed.path == "/shutdown":
                    self.send_json(200, {"stopped": True})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                elif parsed.path == "/check":
                    query = parse_qs(parsed.query, strict_parsing=True, max_num_fields=1)
                    words = json.loads(query["words"][0])
                    if not isinstance(words, list) or not 1 <= len(words) <= 64:
                        raise ValueError("Expected 1 to 64 words")
                    if not all(valid_word(w) for w in words):
                        raise ValueError("Invalid word")
                    self.send_json(200, {"results": [
                        {"word": word, "correct": checker.spell(word)} for word in words]})
                elif parsed.path == "/suggest":
                    query = parse_qs(parsed.query, strict_parsing=True, max_num_fields=1)
                    word = query["word"][0]
                    if not valid_word(word):
                        raise ValueError("Invalid word")
                    self.send_json(200, {"suggestions": checker.suggest(word)})
                else:
                    self.send_json(404, {"error": "Unknown endpoint"})
            except (ValueError, KeyError, TypeError):
                self.send_json(400, {"error": "Invalid request"})
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception:
                self.send_json(500, {"error": "Voikko check failed"})

    class LocalHTTPServer(HTTPServer):
        # Windows SO_REUSEADDR permits multiple listeners on one port. Use an
        # exclusive bind so a second installation cannot hijack the listener.
        allow_reuse_address = sys.platform != 'win32'

        def server_bind(self):
            if sys.platform == 'win32':
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            super().server_bind()

    # One request at a time: libvoikko's instance is never used concurrently.
    return LocalHTTPServer(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    token = (RUNTIME / "key.txt").read_text(encoding="ascii").strip()
    if len(token) != 64:
        raise ValueError("Run setup.py first")
    checker = Checker()
    try:
        with make_server(checker, token, args.port) as server:
            server.serve_forever(poll_interval=0.25)
    finally:
        checker.close()


if __name__ == "__main__":
    main()

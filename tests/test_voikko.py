import json
from pathlib import Path
import threading
import tempfile
import unittest
import urllib.error
import urllib.parse
import urllib.request

from voikko.server import Checker, make_server, valid_word


class WordValidationTests(unittest.TestCase):
    def test_unicode_and_compounds(self):
        for word in ["äiti", "äidin", "EU-maissa", "vaa’an", "a\u0308iti"]:
            self.assertTrue(valid_word(word), word)
        for word in [None, 4, "", "kaksi sanaa", "a\n", "a" * 101, "<script>", "---"]:
            self.assertFalse(valid_word(word), word)

    def test_added_word_persists_and_clears_spelling_cache(self):
        class FakeVoikko:
            def spell(self, word): return False
            def suggest(self, word): return []
            def terminate(self): pass

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "user_words.txt"
            checker = Checker(path, FakeVoikko())
            self.assertFalse(checker.spell("Kisssa"))
            checker.add_word("Kisssa")
            self.assertTrue(checker.spell("kisssa"))
            self.assertTrue(checker.spell("KISSSA"))
            self.assertEqual(path.read_text(encoding="utf-8"), "kisssa\n")
            self.assertTrue(Checker(path, FakeVoikko()).spell("Kisssa"))


@unittest.skipUnless((Path(__file__).resolve().parents[1] / "voikko/runtime/libvoikko-1.dll").exists(),
                     "Run voikko/setup.py to install the native test dependency")
class NativeVoikkoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.words_folder = tempfile.TemporaryDirectory()
        cls.checker = Checker(Path(cls.words_folder.name) / "user_words.txt")
        cls.server = make_server(cls.checker, "a" * 64, 0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()
        cls.checker.close()
        cls.words_folder.cleanup()

    def request(self, path, headers=None, method="GET"):
        headers = {"X-Voikko-Key": "a" * 64} if headers is None else headers
        req = urllib.request.Request(self.url + path, headers=headers, method=method)
        try:
            with self.opener.open(req, timeout=3) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def test_real_spelling_suggestions_and_normalization(self):
        words = ["oikeinkirjoitus", "talossammekin", "yhdyssanoissa", "maahdollisuutta", "a\u0308iti"]
        status, data = self.request("/check?words=" + urllib.parse.quote(json.dumps(words)))
        self.assertEqual(status, 200)
        self.assertEqual([v["correct"] for v in data["results"]], [True, True, True, False, True])
        status, data = self.request("/suggest?word=maahdollisuutta")
        self.assertEqual(status, 200)
        self.assertIn("mahdollisuutta", data["suggestions"])

    def test_browser_and_unauthorized_requests_rejected(self):
        for headers in [{}, {"X-Voikko-Key": "wrong"}, {"X-Voikko-Key": "ä"},
                        {"X-Voikko-Key": "a" * 64, "Origin": "http://example.com"},
                        {"X-Voikko-Key": "a" * 64, "Host": "example.com"}]:
            self.assertEqual(self.request("/health", headers)[0], 403)

    def test_invalid_input_is_bounded(self):
        for words in [[], ["a"] * 65, [None], ["a" * 101], "kissa", ["a\u0000b"]]:
            self.assertEqual(self.request("/check?words=" + urllib.parse.quote(json.dumps(words)))[0], 400)
        self.assertEqual(self.request("/check?words=not-json")[0], 400)
        self.assertEqual(self.request("/check")[0], 400)
        self.assertEqual(self.request("/missing")[0], 404)

    def test_cache_reuses_native_results(self):
        self.checker.spell.cache_clear()
        self.assertTrue(self.checker.spell("kissa"))
        self.assertTrue(self.checker.spell("kissa"))
        self.assertEqual(self.checker.spell.cache_info().hits, 1)
        self.assertEqual(self.checker.spell.cache_info().maxsize, 4096)

    def test_add_word_endpoint_and_persistence(self):
        word = "kisssamaailma"
        self.assertFalse(self.checker.spell(word))
        self.assertEqual(self.request("/add?word=" + word, method="POST"),
                         (200, {"added": True}))
        self.assertTrue(self.checker.spell(word.upper()))
        self.assertEqual(self.request("/add?word=" + word)[0], 404)
        self.assertEqual(self.request("/add?word=kaksi%20sanaa", method="POST")[0], 400)
        self.assertEqual(self.request("/add?word=toinen", headers={}, method="POST")[0], 403)
        self.assertTrue(Checker(Path(self.words_folder.name) / "user_words.txt").spell(word))


if __name__ == "__main__":
    unittest.main()

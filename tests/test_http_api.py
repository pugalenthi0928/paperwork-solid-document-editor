"""Integration tests: actual HTTP requests to the running Python server."""
import json
import threading
from http.server import ThreadingHTTPServer
from tempfile import TemporaryDirectory
from pathlib import Path
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from document_editor import FileStorage
from server import create_handler


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = TemporaryDirectory()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0),
                                         create_handler(FileStorage(Path(cls.temp.name))))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        cls.temp.cleanup()

    def post(self, path, data):
        request = Request(self.base + path, data=json.dumps(data).encode("utf-8"),
                          headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=3) as response:
            return json.load(response)

    def test_homepage_is_served(self):
        with urlopen(self.base + "/", timeout=3) as response:
            self.assertIn(b"Build your document", response.read())

    def test_edit_preview_save_load_and_export(self):
        doc = {"title": "API test", "elements": [{"type": "text", "text": "A & B"}]}
        preview = self.post("/api/preview", {"document": doc})
        self.assertIn("A &amp; B", preview["html"])

        edited = self.post("/api/action", {"document": doc, "action": {
            "kind": "add", "element": {"type": "newline"}}})["document"]
        self.assertEqual(len(edited["elements"]), 2)
        self.assertTrue(self.post("/api/save", {"id": "api-test", "document": edited})["saved"])

        with urlopen(self.base + "/api/load?id=api-test", timeout=3) as response:
            self.assertEqual(json.load(response)["document"], edited)
        with urlopen(self.base + "/api/export?id=api-test&format=html", timeout=3) as response:
            self.assertIn(b"<title>API test</title>", response.read())

    def test_reject_unsafe_image_source(self):
        doc = {"elements": [{"type": "image", "src": "javascript:alert(1)"}]}
        with self.assertRaises(HTTPError) as caught:
            self.post("/api/preview", {"document": doc})
        self.assertEqual(caught.exception.code, 400)


if __name__ == "__main__":
    unittest.main()

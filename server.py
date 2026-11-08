"""Dependency-free local web server for the SOLID document editor.

Run: python server.py --storage file   (or --storage sqlite)
Then open: http://127.0.0.1:8765

Designed as a localhost learning app, not a public internet service.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from document_editor import (
    Document, DocumentEditor, DocumentElement,
    FileStorage, SQLiteStorage,
)

HERE = Path(__file__).resolve().parent
MAX_BYTES = 1_000_000


def create_handler(storage: FileStorage | SQLiteStorage):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, data: bytes, content_type: str, status: int = 200,
                  extra_headers: dict[str, str] | None = None) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'self' https: http: data: 'unsafe-inline'; object-src 'none'; base-uri 'none'")
            for name, value in (extra_headers or {}).items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(data)

        def _json(self, obj: dict[str, object], status: int = 200) -> None:
            self._send(json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8", status)

        def _error(self, message: str, status: int) -> None:
            self._json({"error": message}, status)

        def do_GET(self) -> None:
            parsed = urlsplit(self.path)
            assets = {
                "/": ("index.html", "text/html; charset=utf-8"),
                "/styles.css": ("styles.css", "text/css; charset=utf-8"),
                "/app.js": ("app.js", "text/javascript; charset=utf-8"),
            }
            if parsed.path in assets:
                filename, mime = assets[parsed.path]
                self._send((HERE / "static" / filename).read_bytes(), mime)
                return
            args = parse_qs(parsed.query)
            document_id = args.get("id", ["my-document"])[0]
            try:
                if parsed.path == "/api/load":
                    document = storage.load(document_id)
                    self._json({"document": document.to_dict()})
                elif parsed.path == "/api/export":
                    document = storage.load(document_id)
                    fmt = args.get("format", ["html"])[0]
                    if fmt not in {"html", "txt"}:
                        raise ValueError("format must be html or txt")
                    content = document.render_page() if fmt == "html" else document.as_text()
                    mime = "text/html" if fmt == "html" else "text/plain"
                    self._send(content.encode("utf-8"), f"{mime}; charset=utf-8", extra_headers={
                        "Content-Disposition": f'attachment; filename="{document_id}.{fmt}"',
                    })
                else:
                    self._error("Not found", 404)
            except FileNotFoundError:
                self._error("No saved document with that ID", 404)
            except (ValueError, TypeError, KeyError) as exc:
                self._error(str(exc), 400)

        def do_POST(self) -> None:
            try:
                length = int(self.headers.get("Content-Length", "-1"))
                if length < 0 or length > MAX_BYTES:
                    raise ValueError("Request size missing or too large")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("Request must be a JSON object")
                document = Document.from_dict(payload.get("document", {}))
                editor = DocumentEditor(document)
                path = urlsplit(self.path).path
                if path == "/api/action":
                    action = payload.get("action")
                    if not isinstance(action, dict):
                        raise ValueError("action must be an object")
                    kind = action.get("kind")
                    if kind == "add":
                        editor.add_element(DocumentElement.from_dict(action.get("element")))
                    elif kind == "replace":
                        index = self._index(action.get("index"), document)
                        editor.replace(index, DocumentElement.from_dict(action.get("element")))
                    elif kind == "remove":
                        editor.remove(self._index(action.get("index"), document))
                    elif kind == "move":
                        src = self._index(action.get("index"), document)
                        dst = self._index(action.get("to"), document)
                        editor.move(src, dst)
                    else:
                        raise ValueError("Unknown action")
                    self._json({"document": document.to_dict(), "html": document.render()})
                elif path == "/api/preview":
                    self._json({"html": document.render()})
                elif path == "/api/save":
                    document_id = payload.get("id", "my-document")
                    storage.save(document_id, document)
                    self._json({"saved": True, "id": document_id})
                else:
                    self._error("Not found", 404)
            except (ValueError, KeyError, TypeError, IndexError, UnicodeDecodeError,
                    json.JSONDecodeError) as exc:
                self._error(str(exc), 400)
            except OSError as exc:
                self._error(f"Storage error: {exc}", 500)

        @staticmethod
        def _index(value: object, document: Document) -> int:
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError("index must be a number")
            if not 0 <= value < len(document.elements):
                raise ValueError("index out of bounds")
            return value

        def log_message(self, format: str, *args: object) -> None:
            # Local development logs for each request.
            super().log_message(format, *args)

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="SOLID document editor (local web app)")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--storage", choices=["file", "sqlite"], default="file")
    args = parser.parse_args()
    storage = FileStorage(HERE / "data" / "documents") if args.storage == "file" else SQLiteStorage(HERE / "data" / "documents.db")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), create_handler(storage))
    print(f"Document editor running at http://127.0.0.1:{args.port}")
    print(f"Storage backend: {args.storage}. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

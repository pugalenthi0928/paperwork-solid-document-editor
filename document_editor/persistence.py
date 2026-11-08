"""Storage contract, implemented by independently swappable backends."""
from __future__ import annotations

from abc import ABC, abstractmethod
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile

from .document import Document


_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,60}$")


def validate_doc_id(document_id: str) -> str:
    if not isinstance(document_id, str) or not _ID_PATTERN.fullmatch(document_id):
        raise ValueError("Document ID must be 1–60 letters, numbers, hyphens or underscores")
    return document_id


class Persistence(ABC):
    @abstractmethod
    def save(self, document_id: str, document: Document) -> None:
        ...

    @abstractmethod
    def load(self, document_id: str) -> Document:
        ...


class FileStorage(Persistence):
    def __init__(self, directory: str | Path = "data/documents") -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, document_id: str) -> Path:
        return self.directory / (validate_doc_id(document_id) + ".json")

    def save(self, document_id: str, document: Document) -> None:
        target = self._path(document_id)
        contents = json.dumps(document.to_dict(), ensure_ascii=False, indent=2)
        # Atomic replace prevents partial files if the program is interrupted.
        fd, filename = tempfile.mkstemp(dir=self.directory, prefix=".writing-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(contents)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(filename, target)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def load(self, document_id: str) -> Document:
        with self._path(document_id).open("r", encoding="utf-8") as stream:
            return Document.from_dict(json.load(stream))


class SQLiteStorage(Persistence):
    def __init__(self, path: str | Path = "data/documents.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS documents ("
                               "id TEXT PRIMARY KEY, content TEXT NOT NULL)")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=5)

    def save(self, document_id: str, document: Document) -> None:
        validate_doc_id(document_id)
        contents = json.dumps(document.to_dict(), ensure_ascii=False)
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO documents (id, content) VALUES (?, ?) "
                "ON CONFLICT(id) DO UPDATE SET content=excluded.content",
                (document_id, contents),
            )

    def load(self, document_id: str) -> Document:
        validate_doc_id(document_id)
        with self._connect() as connection:
            row = connection.execute("SELECT content FROM documents WHERE id = ?",
                                     (document_id,)).fetchone()
        if row is None:
            raise FileNotFoundError(f"Document {document_id!r} does not exist")
        return Document.from_dict(json.loads(row[0]))

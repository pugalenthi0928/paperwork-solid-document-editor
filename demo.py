"""Console demonstration from the lecture, in Python.

Run: python demo.py
"""
from pathlib import Path
from tempfile import TemporaryDirectory

from document_editor import Document, DocumentEditor, FileStorage


def main() -> None:
    document = Document("My first SOLID document")
    editor = DocumentEditor(document)
    editor.add_text("Hello world!")
    editor.add_image("https://example.com/photo.jpg", "Example photo")
    editor.add_text("This is my document editor.")
    editor.add_newline()
    editor.add_tab()
    editor.add_text("And it follows the SOLID ideas from the lecture.")

    print("--- RENDERED DOCUMENT (plain text) ---")
    print(document.as_text())

    storage = FileStorage(Path("data") / "documents")
    storage.save("example", document)
    print("Saved to data/documents/example.json")
    print("Loaded title:", storage.load("example").title)


if __name__ == "__main__":
    main()

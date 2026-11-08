import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from document_editor import (
    Document, DocumentEditor, DocumentElement, FileStorage, ImageElement,
    NewlineElement, Persistence, SQLiteStorage, TabElement, TextElement,
)


class DocumentEditorTests(unittest.TestCase):
    def setUp(self):
        self.doc = Document("Test")
        self.editor = DocumentEditor(self.doc)

    def test_add_elements_in_order(self):
        self.editor.add_text("first")
        self.editor.add_image("https://example.com/cat.jpg", "Cat")
        self.editor.add_text("last")
        self.assertEqual([item.kind for item in self.doc.elements], ["text", "image", "text"])
        self.assertIn("first", self.doc.render())
        self.assertLess(self.doc.render().find("first"), self.doc.render().find("cat.jpg"))

    def test_html_is_escaped(self):
        self.editor.add_text('<script>alert("x")</script>')
        self.assertNotIn("<script>", self.doc.render())
        self.assertIn("&lt;script&gt;", self.doc.render())

    def test_image_src_is_validated(self):
        with self.assertRaises(ValueError):
            self.editor.add_image('javascript:alert(1)')
        with self.assertRaises(ValueError):
            self.editor.add_image('file:///etc/passwd')
        self.editor.add_image('https://example.com/img?x="onerror=1', 'a"b')
        self.assertIn('&quot;', self.doc.render())

    def test_replace_remove_and_move(self):
        self.editor.add_text("one")
        self.editor.add_text("two")
        self.editor.move(1, 0)
        self.assertEqual([x.text for x in self.doc.elements], ["two", "one"])
        self.editor.replace(1, TextElement("three"))
        self.editor.remove(0)
        self.assertEqual(self.doc.as_text(), "three\n")

    def test_fresh_render_after_edit(self):
        self.editor.add_text("before")
        self.assertIn("before", self.doc.render())
        self.editor.replace(0, TextElement("after"))
        self.assertNotIn("before", self.doc.render())
        self.assertIn("after", self.doc.render())

    def test_line_break_and_tab(self):
        self.editor.add_newline()
        self.editor.add_tab()
        self.assertEqual(self.doc.as_text(), "\n    ")
        self.assertIn('doc-newline', self.doc.render())

    def test_elements_are_read_only_snapshot(self):
        self.editor.add_text("A")
        self.assertIsInstance(self.doc.elements, tuple)
        with self.assertRaises(AttributeError):
            self.doc.elements.append(TextElement("B"))

    def test_invalid_input_is_rejected(self):
        with self.assertRaises(ValueError):
            Document.from_dict({"elements": [{"type": "invalid"}]})
        with self.assertRaises(ValueError):
            Document.from_dict({"elements": [1]})
        with self.assertRaises(ValueError):
            Document.from_dict({"elements": "not a list"})

    def test_file_storage_roundtrip(self):
        self.editor.add_text("Persistent value 💚")
        with TemporaryDirectory() as root:
            store = FileStorage(Path(root) / "docs")
            store.save("my_doc", self.doc)
            self.assertEqual(store.load("my_doc").to_dict(), self.doc.to_dict())

    def test_file_storage_rejects_path_traversal(self):
        with TemporaryDirectory() as root:
            store = FileStorage(root)
            with self.assertRaises(ValueError):
                store.save("../outside", self.doc)

    def test_sqlite_storage_roundtrip(self):
        self.editor.add_text("DB save")
        with TemporaryDirectory() as root:
            store = SQLiteStorage(Path(root) / "docs.db")
            store.save("my_doc", self.doc)
            self.assertEqual(store.load("my_doc").to_dict(), self.doc.to_dict())
            self.editor.add_text("second edit")
            store.save("my_doc", self.doc)
            self.assertEqual(len(store.load("my_doc").elements), 2)
            with self.assertRaises(FileNotFoundError):
                store.load("other")

    def test_new_element_type_without_changing_document(self):
        class QuoteElement(DocumentElement, kind="test-quote"):
            def __init__(self, text):
                self.text = text
            def render(self):
                return "<blockquote>" + self.text + "</blockquote>"
            def as_text(self):
                return '> ' + self.text + '\n'
            def to_dict(self):
                return {"type": self.kind, "text": self.text}
            @classmethod
            def _from_dict(cls, data):
                return cls(str(data['text']))

        self.editor.add_element(QuoteElement("Hello"))
        self.assertIn("<blockquote>Hello", self.doc.render())
        rebuilt = Document.from_dict(self.doc.to_dict())
        self.assertEqual(rebuilt.as_text(), "> Hello\n")

    def test_persistence_can_be_swapped(self):
        class MemoryStorage(Persistence):
            def __init__(self):
                self.records = {}
            def save(self, document_id, document):
                self.records[document_id] = document.to_dict()
            def load(self, document_id):
                return Document.from_dict(self.records[document_id])

        store: Persistence = MemoryStorage()
        store.save("hello", self.doc)
        self.assertEqual(store.load("hello").title, "Test")

    def test_page_includes_title(self):
        self.editor.add_text("body")
        self.assertIn("<title>Test</title>", self.doc.render_page())
        self.assertIn("body", self.doc.render_page())


if __name__ == "__main__":
    unittest.main()

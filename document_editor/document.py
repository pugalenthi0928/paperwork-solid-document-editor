"""The document owns and orders its elements; it delegates rendering to them."""
from __future__ import annotations

from dataclasses import dataclass, field
from html import escape

from .elements import DocumentElement


@dataclass
class Document:
    title: str = "Untitled document"
    _elements: list[DocumentElement] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.title, str) or len(self.title) > 150:
            raise ValueError("Title must be text up to 150 characters")

    @property
    def elements(self) -> tuple[DocumentElement, ...]:
        """Immutable snapshot: callers cannot silently mutate the underlying list."""
        return tuple(self._elements)

    def add_element(self, element: DocumentElement) -> None:
        if not isinstance(element, DocumentElement):
            raise TypeError("Expected a DocumentElement")
        if len(self._elements) >= 250:
            raise ValueError("A document can have at most 250 elements")
        self._elements.append(element)

    def replace_element(self, index: int, element: DocumentElement) -> None:
        if not isinstance(element, DocumentElement):
            raise TypeError("Expected a DocumentElement")
        self._elements[index] = element

    def remove_element(self, index: int) -> DocumentElement:
        return self._elements.pop(index)

    def move_element(self, index: int, new_index: int) -> None:
        if not (0 <= index < len(self._elements) and 0 <= new_index < len(self._elements)):
            raise IndexError("Element index out of range")
        self._elements.insert(new_index, self._elements.pop(index))

    def render(self) -> str:
        """Delegates each block to its own polymorphic render() implementation."""
        return "\n".join(element.render() for element in self._elements)

    def as_text(self) -> str:
        return "".join(element.as_text() for element in self._elements)

    def render_page(self) -> str:
        css = """body{font-family:Georgia,serif;background:#f5f4f1;margin:0;padding:36px;color:#262626}
        article{background:white;max-width:750px;margin:auto;padding:65px;min-height:650px;box-shadow:0 4px 30px #0001}
        h1{font-family:Arial,sans-serif;font-size:27px;margin:0 0 32px}
        .doc-paragraph{font-size:17px;line-height:1.7;white-space:pre-wrap;margin:0 0 18px}
        .doc-figure{margin:23px 0}.doc-figure img{max-width:100%;max-height:460px;border-radius:4px}
        figcaption{color:#666;font:12px Arial,sans-serif;margin-top:8px}
        .doc-newline{height:22px}.doc-tab{height:14px;margin-left:38px;border-left:2px solid #eee}"""
        return ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
                f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
                f"<title>{escape(self.title)}</title><style>{css}</style></head><body>"
                f"<article><h1>{escape(self.title)}</h1>{self.render()}</article></body></html>")

    def to_dict(self) -> dict[str, object]:
        return {"title": self.title, "elements": [e.to_dict() for e in self._elements]}

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Document:
        if not isinstance(data, dict):
            raise ValueError("Document must be an object")
        title = data.get("title", "Untitled document")
        if not isinstance(title, str):
            raise ValueError("Title must be text")
        blocks = data.get("elements", [])
        if not isinstance(blocks, list) or len(blocks) > 250:
            raise ValueError("elements must be a list of up to 250 items")
        document = cls(title=title)
        for block in blocks:
            document.add_element(DocumentElement.from_dict(block))
        return document

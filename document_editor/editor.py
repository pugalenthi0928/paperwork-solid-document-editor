"""Editing operations only; no rendering, file IO, or SQL here."""
from __future__ import annotations

from .document import Document
from .elements import DocumentElement, ImageElement, NewlineElement, TabElement, TextElement


class DocumentEditor:
    def __init__(self, document: Document) -> None:
        self.document = document

    def add_text(self, text: str) -> None:
        self.document.add_element(TextElement(text))

    def add_image(self, url: str, alt: str = "Document image") -> None:
        self.document.add_element(ImageElement(url, alt))

    def add_newline(self) -> None:
        self.document.add_element(NewlineElement())

    def add_tab(self) -> None:
        self.document.add_element(TabElement())

    def add_element(self, element: DocumentElement) -> None:
        self.document.add_element(element)

    def replace(self, index: int, element: DocumentElement) -> None:
        self.document.replace_element(index, element)

    def remove(self, index: int) -> None:
        self.document.remove_element(index)

    def move(self, index: int, new_index: int) -> None:
        self.document.move_element(index, new_index)

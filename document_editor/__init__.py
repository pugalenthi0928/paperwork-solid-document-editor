"""SOLID Document Editor — learn OOP by building a working application."""
from .document import Document
from .editor import DocumentEditor
from .elements import DocumentElement, TextElement, ImageElement, NewlineElement, TabElement
from .persistence import Persistence, FileStorage, SQLiteStorage

__all__ = ["Document", "DocumentEditor", "DocumentElement", "TextElement",
           "ImageElement", "NewlineElement", "TabElement", "Persistence", "FileStorage",
           "SQLiteStorage"]

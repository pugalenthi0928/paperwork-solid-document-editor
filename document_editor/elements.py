"""Document element contract and concrete elements.

Adding a new element type does not require modifying Document or DocumentEditor.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from html import escape
from typing import ClassVar
from urllib.parse import urlsplit


class DocumentElement(ABC):
    """Small, stable interface shared by all document elements."""

    registry: ClassVar[dict[str, type[DocumentElement]]] = {}
    kind: ClassVar[str]

    def __init_subclass__(cls, *, kind: str | None = None, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if kind is not None:
            if kind in DocumentElement.registry:
                raise ValueError(f"Duplicate element kind: {kind}")
            cls.kind = kind
            DocumentElement.registry[kind] = cls

    @abstractmethod
    def render(self) -> str:
        """Return safe HTML for this element."""

    @abstractmethod
    def as_text(self) -> str:
        """Return a readable plain-text representation."""

    @abstractmethod
    def to_dict(self) -> dict[str, str]:
        """Serialize to a JSON-friendly dictionary."""

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> DocumentElement:
        if not isinstance(data, dict):
            raise ValueError("Each element must be an object")
        kind = data.get("type")
        if not isinstance(kind, str) or kind not in cls.registry:
            raise ValueError(f"Unsupported element type: {kind!r}")
        subclass = cls.registry[kind]
        return subclass._from_dict(data)

    @classmethod
    @abstractmethod
    def _from_dict(cls, data: dict[str, object]) -> DocumentElement:
        ...


def _string(data: dict[str, object], key: str, limit: int) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be text")
    if len(value) > limit:
        raise ValueError(f"{key} is too long")
    return value


@dataclass(frozen=True)
class TextElement(DocumentElement, kind="text"):
    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or len(self.text) > 50000:
            raise ValueError("Text must be a string up to 50,000 characters")

    def render(self) -> str:
        return f'<p class="doc-paragraph">{escape(self.text).replace(chr(10), "<br>")}</p>'

    def as_text(self) -> str:
        return self.text + "\n"

    def to_dict(self) -> dict[str, str]:
        return {"type": self.kind, "text": self.text}

    @classmethod
    def _from_dict(cls, data: dict[str, object]) -> TextElement:
        return cls(_string(data, "text", 50000))


@dataclass(frozen=True)
class ImageElement(DocumentElement, kind="image"):
    src: str
    alt: str = "Document image"

    def __post_init__(self) -> None:
        if not isinstance(self.src, str) or len(self.src) > 2048:
            raise ValueError("Image URL must be text up to 2,048 characters")
        url = urlsplit(self.src)
        if url.scheme not in ("http", "https") or not url.netloc:
            raise ValueError("Image URL must start with http:// or https://")
        if url.username or url.password:
            raise ValueError("Image URL cannot contain credentials")
        if not isinstance(self.alt, str) or len(self.alt) > 200:
            raise ValueError("Alt text must be text up to 200 characters")

    def render(self) -> str:
        return (f'<figure class="doc-figure"><img loading="lazy" '
                f'src="{escape(self.src, quote=True)}" '
                f'alt="{escape(self.alt, quote=True)}"><figcaption>'
                f'{escape(self.alt)}</figcaption></figure>')

    def as_text(self) -> str:
        return f"[Image: {self.alt} — {self.src}]\n"

    def to_dict(self) -> dict[str, str]:
        return {"type": self.kind, "src": self.src, "alt": self.alt}

    @classmethod
    def _from_dict(cls, data: dict[str, object]) -> ImageElement:
        alt = data.get("alt", "Document image")
        if not isinstance(alt, str):
            raise ValueError("alt must be text")
        return cls(_string(data, "src", 2048), alt)


@dataclass(frozen=True)
class NewlineElement(DocumentElement, kind="newline"):
    def render(self) -> str:
        return '<div class="doc-newline" aria-hidden="true"></div>'

    def as_text(self) -> str:
        return "\n"

    def to_dict(self) -> dict[str, str]:
        return {"type": self.kind}

    @classmethod
    def _from_dict(cls, data: dict[str, object]) -> NewlineElement:
        return cls()


@dataclass(frozen=True)
class TabElement(DocumentElement, kind="tab"):
    def render(self) -> str:
        return '<div class="doc-tab" aria-hidden="true"></div>'

    def as_text(self) -> str:
        return "    "

    def to_dict(self) -> dict[str, str]:
        return {"type": self.kind}

    @classmethod
    def _from_dict(cls, data: dict[str, object]) -> TabElement:
        return cls()

from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Final

from access_audit.models import Attribute, Document, Element

MAX_SOURCE_BYTES: Final = 1_048_576
MAX_ELEMENTS: Final = 10_000
MAX_DEPTH: Final = 64
MAX_ATTRIBUTES: Final = 64
MAX_ATTRIBUTE_CODEPOINTS: Final = 4_096
VOID_ELEMENTS: Final = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "source",
        "track",
        "wbr",
    }
)


class ParseError(ValueError):
    """Raised when an HTML snapshot violates the parser contract."""


@dataclass(slots=True)
class _MutableElement:
    index: int
    tag: str
    attributes: tuple[Attribute, ...]
    line: int
    column: int
    depth: int
    parent_index: int | None
    has_text: bool = False
    children: list[int] = field(default_factory=list)


class _BoundedParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.nodes: list[_MutableElement] = []
        self.stack: list[int] = []
        self.doctype_seen = False

    def handle_decl(self, decl: str) -> None:
        if decl.strip().casefold() != "doctype html" or self.doctype_seen:
            raise ParseError("only one HTML5 doctype is supported")
        self.doctype_seen = True

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        normalized_tag = tag.casefold()
        if len(self.nodes) >= MAX_ELEMENTS:
            raise ParseError("element limit exceeded")
        if len(self.stack) >= MAX_DEPTH:
            raise ParseError("depth limit exceeded")
        if len(attrs) > MAX_ATTRIBUTES:
            raise ParseError("attribute limit exceeded")
        normalized: list[Attribute] = []
        names: set[str] = set()
        for raw_name, raw_value in attrs:
            name = raw_name.casefold()
            if name in names:
                raise ParseError("duplicate attribute")
            names.add(name)
            value = unicodedata.normalize("NFC", raw_value or "")
            if len(value) > MAX_ATTRIBUTE_CODEPOINTS:
                raise ParseError("attribute value limit exceeded")
            normalized.append(Attribute(name=name, value=value))
        normalized.sort(key=lambda item: item.name)
        line, column = self.getpos()
        index = len(self.nodes)
        parent = self.stack[-1] if self.stack else None
        node = _MutableElement(
            index=index,
            tag=normalized_tag,
            attributes=tuple(normalized),
            line=line,
            column=column,
            depth=len(self.stack),
            parent_index=parent,
        )
        self.nodes.append(node)
        if parent is not None:
            self.nodes[parent].children.append(index)
        if normalized_tag not in VOID_ELEMENTS:
            self.stack.append(index)

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        self.handle_starttag(tag, attrs)
        normalized_tag = tag.casefold()
        if normalized_tag not in VOID_ELEMENTS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.casefold()
        if normalized_tag in VOID_ELEMENTS:
            raise ParseError("void element has an end tag")
        if not self.stack or self.nodes[self.stack[-1]].tag != normalized_tag:
            raise ParseError("mismatched end tag")
        self.stack.pop()

    def handle_data(self, data: str) -> None:
        hidden = any(
            self.nodes[index].attributes
            and (
                any(attribute.name == "hidden" for attribute in self.nodes[index].attributes)
                or any(
                    attribute.name == "aria-hidden" and attribute.value.strip().casefold() == "true"
                    for attribute in self.nodes[index].attributes
                )
            )
            for index in self.stack
        )
        if data.strip() and not hidden:
            for index in self.stack:
                self.nodes[index].has_text = True

    def unknown_decl(self, _data: str) -> None:
        raise ParseError("unsupported declaration")

    def close_and_freeze(self, source: bytes) -> Document:
        super().close()
        if self.stack:
            raise ParseError("unclosed element")
        elements = tuple(
            Element(
                index=node.index,
                tag=node.tag,
                attributes=node.attributes,
                line=node.line,
                column=node.column,
                depth=node.depth,
                parent_index=node.parent_index,
                has_text=node.has_text,
            )
            for node in self.nodes
        )
        return Document(
            elements=elements,
            source_sha256=hashlib.sha256(source).hexdigest(),
            source_bytes=len(source),
            doctype_seen=self.doctype_seen,
        )


def parse_html(source: bytes) -> Document:
    """Parse a bounded UTF-8 HTML snapshot without retaining page text."""
    if len(source) > MAX_SOURCE_BYTES:
        raise ParseError("source byte limit exceeded")
    if b"\x00" in source:
        raise ParseError("NUL byte is not allowed")
    try:
        text = source.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ParseError("source must be UTF-8") from error
    parser = _BoundedParser()
    try:
        parser.feed(text)
        return parser.close_and_freeze(source)
    except ParseError:
        raise
    except (AssertionError, ValueError) as error:
        raise ParseError("malformed HTML") from error

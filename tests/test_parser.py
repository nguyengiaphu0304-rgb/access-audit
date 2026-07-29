from __future__ import annotations

import unicodedata

import pytest

from access_audit import ParseError, parse_html
from access_audit.parser import MAX_ATTRIBUTE_CODEPOINTS, MAX_ELEMENTS, MAX_SOURCE_BYTES


def test_parser_freezes_locations_and_discards_text() -> None:
    document = parse_html(
        b"<!doctype html><html lang='en'><body><p id='x'>Private text</p></body></html>",
    )
    paragraph = next(element for element in document.elements if element.tag == "p")
    assert paragraph.line == 1
    assert paragraph.has_text is True
    assert not hasattr(paragraph, "text")
    assert paragraph.attribute("id") == "x"


@pytest.mark.parametrize(
    ("source", "match"),
    [
        (b"\xff", "UTF-8"),
        (b"<html>\x00</html>", "NUL"),
        (b"<html><div id='a' id='b'></div></html>", "duplicate attribute"),
        (b"<html><div></span></html>", "mismatched"),
        (b"<html><div></div>", "unclosed"),
        (b"<html><img></img></html>", "void element"),
        (b"<!doctype svg><html></html>", "HTML5 doctype"),
        (b"<!doctype html><!doctype html><html></html>", "HTML5 doctype"),
    ],
)
def test_parser_rejects_malformed_or_ambiguous_input(source: bytes, match: str) -> None:
    with pytest.raises(ParseError, match=match):
        parse_html(source)


def test_parser_rejects_source_over_budget() -> None:
    with pytest.raises(ParseError, match="byte limit"):
        parse_html(b" " * (MAX_SOURCE_BYTES + 1))


def test_parser_normalizes_attribute_values_to_nfc() -> None:
    decomposed = unicodedata.normalize("NFD", "café")
    source = f"<html><body><div id='{decomposed}'></div></body></html>".encode()
    document = parse_html(source)
    element = next(node for node in document.elements if node.tag == "div")
    assert element.attribute("id") == "café"


def test_parser_rejects_excessive_depth() -> None:
    source = ("<div>" * 65 + "</div>" * 65).encode()
    with pytest.raises(ParseError, match="depth"):
        parse_html(source)


def test_parser_rejects_excessive_element_count() -> None:
    source = b"<br>" * (MAX_ELEMENTS + 1)
    with pytest.raises(ParseError, match="element limit"):
        parse_html(source)


def test_parser_rejects_excessive_attributes() -> None:
    attributes = " ".join(f"data-{index}='x'" for index in range(65))
    with pytest.raises(ParseError, match="attribute limit"):
        parse_html(f"<div {attributes}></div>".encode())


def test_parser_rejects_excessive_attribute_value() -> None:
    source = f"<div title='{'x' * (MAX_ATTRIBUTE_CODEPOINTS + 1)}'></div>".encode()
    with pytest.raises(ParseError, match="value limit"):
        parse_html(source)


def test_hidden_descendant_text_does_not_become_name_signal() -> None:
    document = parse_html(b"<button><span aria-hidden='true'>icon</span></button>")
    button = document.elements[0]
    assert button.has_text is False

"""Immutable public models for Access Audit."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    """Finding severity used for deterministic policy decisions."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class Attribute:
    """One normalized HTML attribute."""

    name: str
    value: str


@dataclass(frozen=True, slots=True)
class Element:
    """A bounded source element with no retained page text."""

    index: int
    tag: str
    attributes: tuple[Attribute, ...]
    line: int
    column: int
    depth: int
    parent_index: int | None
    has_text: bool

    def attribute(self, name: str) -> str | None:
        """Return one normalized attribute value."""
        for attribute in self.attributes:
            if attribute.name == name:
                return attribute.value
        return None

    def has_attribute(self, name: str) -> bool:
        """Return whether an attribute exists, including empty attributes."""
        return any(attribute.name == name for attribute in self.attributes)


@dataclass(frozen=True, slots=True)
class Document:
    """Parsed, immutable source document."""

    elements: tuple[Element, ...]
    source_sha256: str
    source_bytes: int
    doctype_seen: bool


@dataclass(frozen=True, slots=True)
class Finding:
    """A privacy-minimized static finding."""

    rule_id: str
    severity: Severity
    element_index: int
    element_tag: str
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class Rule:
    """Stable rule metadata."""

    rule_id: str
    severity: Severity
    title: str
    wcag_relationship: str
    limitation: str

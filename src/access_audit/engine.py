"""Deterministic static audit and canonical evidence."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections import Counter
from typing import Final

from access_audit.models import Document, Element, Finding
from access_audit.parser import parse_html
from access_audit.rules import RULE_BY_ID, RULES

SCHEMA_VERSION: Final = "access-audit/report-v1"
TOOL_VERSION: Final = "1.0.0"
MAX_FINDINGS: Final = 10_000
ARIA_IDREF_ATTRIBUTES: Final = (
    "aria-activedescendant",
    "aria-controls",
    "aria-describedby",
    "aria-labelledby",
    "aria-owns",
)
FORM_INPUT_TYPES_WITHOUT_LABEL: Final = {"hidden", "button", "submit", "reset", "image"}
LIMITATIONS: Final = (
    "source_html_not_rendered_dom",
    "no_computed_styles_or_contrast",
    "no_browser_accessible_name_computation",
    "no_keyboard_or_focus_simulation",
    "no_screen_reader_or_user_testing",
    "not_wcag_conformance_evidence",
)


class AuditError(ValueError):
    """Raised when an audit report cannot be safely created or verified."""


def _normalized_id(value: str) -> str:
    return unicodedata.normalize("NFC", value.strip())


def _hidden(element: Element, document: Document) -> bool:
    candidates = (element, *_ancestors(element, document))
    return any(
        candidate.has_attribute("hidden")
        or (candidate.attribute("aria-hidden") or "").strip().casefold() == "true"
        for candidate in candidates
    )


def _nonempty_attribute(element: Element, name: str) -> bool:
    value = element.attribute(name)
    return value is not None and bool(value.strip())


def _ancestors(element: Element, document: Document) -> tuple[Element, ...]:
    result: list[Element] = []
    parent = element.parent_index
    while parent is not None:
        node = document.elements[parent]
        result.append(node)
        parent = node.parent_index
    return tuple(result)


def _descendants(element: Element, document: Document) -> tuple[Element, ...]:
    result: list[Element] = []
    for candidate in document.elements[element.index + 1 :]:
        if candidate.depth <= element.depth:
            break
        result.append(candidate)
    return tuple(result)


def _valid_idrefs(element: Element, attribute: str, unique_ids: set[str]) -> bool:
    raw = element.attribute(attribute)
    if raw is None or not raw.strip():
        return False
    references = tuple(_normalized_id(value) for value in raw.split())
    return bool(references) and all(reference in unique_ids for reference in references)


def _name_signal(element: Element, document: Document, unique_ids: set[str]) -> bool:
    if _hidden(element, document):
        return False
    if _nonempty_attribute(element, "aria-label"):
        return True
    if _valid_idrefs(element, "aria-labelledby", unique_ids):
        return True
    return element.has_text


def _form_labelled(element: Element, document: Document, unique_ids: set[str]) -> bool:
    if _nonempty_attribute(element, "aria-label") or _valid_idrefs(
        element,
        "aria-labelledby",
        unique_ids,
    ):
        return True
    identifier = _normalized_id(element.attribute("id") or "")
    if identifier and any(
        candidate.tag == "label"
        and _normalized_id(candidate.attribute("for") or "") == identifier
        and candidate.has_text
        for candidate in document.elements
    ):
        return True
    return any(
        ancestor.tag == "label" and ancestor.has_text for ancestor in _ancestors(element, document)
    )


def _finding(rule_id: str, element: Element) -> Finding:
    rule = RULE_BY_ID[rule_id]
    return Finding(
        rule_id=rule_id,
        severity=rule.severity,
        element_index=element.index,
        element_tag=element.tag,
        line=element.line,
        column=element.column,
    )


def _document_findings(document: Document) -> list[Finding]:
    findings: list[Finding] = []
    html = next((element for element in document.elements if element.tag == "html"), None)
    anchor = html or (document.elements[0] if document.elements else None)
    if anchor is None:
        raise AuditError("document has no elements")
    if html is None or not _nonempty_attribute(html, "lang"):
        findings.append(_finding("AA001", anchor))

    titles = [
        element for element in document.elements if element.tag == "title" and element.has_text
    ]
    if len(titles) != 1:
        findings.append(_finding("AA002", html or anchor))

    mains = [
        element
        for element in document.elements
        if element.tag == "main" or (element.attribute("role") or "").strip().casefold() == "main"
    ]
    if len(mains) != 1:
        findings.append(_finding("AA003", html or anchor))
    return findings


def _heading_findings(document: Document) -> list[Finding]:
    findings: list[Finding] = []
    html = next((element for element in document.elements if element.tag == "html"), None)
    anchor = html or document.elements[0]
    headings = [
        element
        for element in document.elements
        if len(element.tag) == 2 and element.tag[0] == "h" and element.tag[1].isdigit()
    ]
    if not any(element.tag == "h1" for element in headings):
        findings.append(_finding("AA004", anchor))
    previous_level: int | None = None
    for heading in headings:
        level = int(heading.tag[1])
        if previous_level is not None and level > previous_level + 1:
            findings.append(_finding("AA004", heading))
        previous_level = level
    return findings


def _image_findings(element: Element, document: Document) -> list[Finding]:
    if element.tag != "img":
        return []
    decorative = (element.attribute("role") or "").strip().casefold() in {
        "none",
        "presentation",
    }
    if not decorative and not _hidden(element, document) and not element.has_attribute("alt"):
        return [_finding("AA005", element)]
    return []


def _form_and_control_findings(
    element: Element,
    document: Document,
    unique_ids: set[str],
) -> list[Finding]:
    findings: list[Finding] = []
    input_type = (element.attribute("type") or "text").strip().casefold()
    is_labelled_form = element.tag in {"select", "textarea"} or (
        element.tag == "input" and input_type not in FORM_INPUT_TYPES_WITHOUT_LABEL
    )
    if is_labelled_form and not _form_labelled(element, document, unique_ids):
        findings.append(_finding("AA006", element))
    is_button = element.tag == "button" or (
        element.tag == "input" and input_type in {"button", "submit", "reset", "image"}
    )
    if is_button:
        has_value = element.tag == "input" and _nonempty_attribute(element, "value")
        if not has_value and not _name_signal(element, document, unique_ids):
            findings.append(_finding("AA007", element))
    return findings


def _link_focus_and_table_findings(
    element: Element,
    document: Document,
    unique_ids: set[str],
) -> list[Finding]:
    findings: list[Finding] = []
    if element.tag == "a" and element.has_attribute("href"):
        descendant_alt = any(
            candidate.tag == "img"
            and not _hidden(candidate, document)
            and _nonempty_attribute(candidate, "alt")
            for candidate in _descendants(element, document)
        )
        if not descendant_alt and not _name_signal(element, document, unique_ids):
            findings.append(_finding("AA008", element))
    tabindex = element.attribute("tabindex")
    if tabindex is not None:
        try:
            positive = int(tabindex.strip()) > 0
        except ValueError:
            positive = False
        if positive:
            findings.append(_finding("AA011", element))
    if element.tag == "table":
        caption = any(
            candidate.tag == "caption" and candidate.has_text
            for candidate in _descendants(element, document)
        )
        explicitly_named = _nonempty_attribute(element, "aria-label") or _valid_idrefs(
            element,
            "aria-labelledby",
            unique_ids,
        )
        if not caption and not explicitly_named:
            findings.append(_finding("AA012", element))
    return findings


def _element_findings(document: Document, unique_ids: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    for element in document.elements:
        findings.extend(_image_findings(element, document))
        findings.extend(_form_and_control_findings(element, document, unique_ids))
        findings.extend(_link_focus_and_table_findings(element, document, unique_ids))
    return findings


def _duplicate_id_findings(document: Document) -> tuple[list[Finding], set[str]]:
    findings: list[Finding] = []
    ids: dict[str, list[Element]] = {}
    for element in document.elements:
        identifier = _normalized_id(element.attribute("id") or "")
        if identifier:
            ids.setdefault(identifier, []).append(element)
    for duplicates in ids.values():
        if len(duplicates) > 1:
            findings.extend(_finding("AA009", element) for element in duplicates)
    return findings, {identifier for identifier, elements in ids.items() if len(elements) == 1}


def _aria_reference_findings(document: Document, unique_ids: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    for element in document.elements:
        for attribute in ARIA_IDREF_ATTRIBUTES:
            raw = element.attribute(attribute)
            if raw is None:
                continue
            references = tuple(_normalized_id(value) for value in raw.split())
            if not references or any(reference not in unique_ids for reference in references):
                findings.append(_finding("AA010", element))
                break
    return findings


def audit(document: Document) -> tuple[Finding, ...]:
    """Run deterministic static rules over one parsed document."""
    if not document.elements:
        raise AuditError("document has no elements")
    duplicate_findings, unique_ids = _duplicate_id_findings(document)
    findings = [
        *_document_findings(document),
        *_heading_findings(document),
        *_element_findings(document, unique_ids),
        *duplicate_findings,
        *_aria_reference_findings(document, unique_ids),
    ]

    ordered = sorted(
        set(findings),
        key=lambda item: (
            item.rule_id,
            item.line,
            item.column,
            item.element_index,
            item.element_tag,
        ),
    )
    if len(ordered) > MAX_FINDINGS:
        raise AuditError("finding limit exceeded")
    return tuple(ordered)


def _canonical(value: object) -> bytes:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"{encoded}\n".encode()


def create_report(source: bytes) -> bytes:
    """Create a canonical, privacy-minimized report envelope."""
    document = parse_html(source)
    findings = audit(document)
    severity_counts = Counter(finding.severity.value for finding in findings)
    rule_counts = Counter(finding.rule_id for finding in findings)
    payload = {
        "document": {
            "element_count": len(document.elements),
            "source_bytes": document.source_bytes,
            "source_sha256": document.source_sha256,
        },
        "findings": [
            {
                "column": finding.column,
                "element_index": finding.element_index,
                "element_tag": finding.element_tag,
                "line": finding.line,
                "rule_id": finding.rule_id,
                "severity": finding.severity.value,
            }
            for finding in findings
        ],
        "limitations": list(LIMITATIONS),
        "rules": [
            {
                "limitation": rule.limitation,
                "rule_id": rule.rule_id,
                "severity": rule.severity.value,
                "title": rule.title,
                "wcag_relationship": rule.wcag_relationship,
            }
            for rule in RULES
        ],
        "schema_version": SCHEMA_VERSION,
        "summary": {
            "error_count": severity_counts["error"],
            "finding_count": len(findings),
            "rule_counts": {key: rule_counts[key] for key in sorted(rule_counts)},
            "truncated": False,
            "warning_count": severity_counts["warning"],
        },
        "tool_version": TOOL_VERSION,
    }
    payload_bytes = _canonical(payload)
    envelope = {
        "payload": payload,
        "schema_version": SCHEMA_VERSION,
        "sha256": hashlib.sha256(payload_bytes).hexdigest(),
    }
    return _canonical(envelope)


def verify_report(source: bytes, report: bytes) -> None:
    """Reparse, rerun, and require a byte-identical report."""
    if report != create_report(source):
        raise AuditError("report does not match independent audit")

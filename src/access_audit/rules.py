"""Stable static-rule registry."""

from typing import Final

from access_audit.models import Rule, Severity

RULES: Final = (
    Rule(
        "AA001",
        Severity.ERROR,
        "Document language",
        "WCAG 3.1.1 relationship",
        "Static presence check cannot validate whether the declared language is correct.",
    ),
    Rule(
        "AA002",
        Severity.ERROR,
        "Document title",
        "WCAG 2.4.2 relationship",
        "Static text presence cannot validate whether the title describes the page.",
    ),
    Rule(
        "AA003",
        Severity.ERROR,
        "Main landmark",
        "WCAG 1.3.1 relationship",
        "Static markup cannot validate the complete landmark experience.",
    ),
    Rule(
        "AA004",
        Severity.WARNING,
        "Heading structure",
        "WCAG 1.3.1 and 2.4.6 relationship",
        "Heading level order is a heuristic and does not judge wording or visual hierarchy.",
    ),
    Rule(
        "AA005",
        Severity.ERROR,
        "Image alternative",
        "WCAG 1.1.1 relationship",
        "Attribute presence cannot judge whether alternative text is useful.",
    ),
    Rule(
        "AA006",
        Severity.ERROR,
        "Form label",
        "WCAG 1.3.1 and 3.3.2 relationship",
        "Static association cannot validate spoken output or instruction quality.",
    ),
    Rule(
        "AA007",
        Severity.ERROR,
        "Control accessible name signal",
        "WCAG 4.1.2 relationship",
        "This bounded approximation is not the browser accessible-name algorithm.",
    ),
    Rule(
        "AA008",
        Severity.ERROR,
        "Link accessible name signal",
        "WCAG 2.4.4 and 4.1.2 relationship",
        "Static text presence cannot judge purpose or surrounding context.",
    ),
    Rule(
        "AA009",
        Severity.ERROR,
        "Unique normalized IDs",
        "WCAG 4.1.1 historical relationship",
        "Unique IDs do not establish valid ARIA or usable interaction.",
    ),
    Rule(
        "AA010",
        Severity.ERROR,
        "ARIA reference target",
        "WCAG 1.3.1 and 4.1.2 relationship",
        "Target existence does not establish correct ARIA semantics.",
    ),
    Rule(
        "AA011",
        Severity.WARNING,
        "Positive tabindex",
        "WCAG 2.4.3 relationship",
        "Source attributes cannot simulate the complete focus order.",
    ),
    Rule(
        "AA012",
        Severity.WARNING,
        "Table name or caption",
        "WCAG 1.3.1 relationship",
        "A caption signal does not prove correct headers or table semantics.",
    ),
)

RULE_BY_ID: Final = {rule.rule_id: rule for rule in RULES}

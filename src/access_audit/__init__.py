"""Public API for Access Audit."""

from access_audit.engine import AuditError, create_report, verify_report
from access_audit.models import Finding, Rule, Severity
from access_audit.parser import ParseError, parse_html
from access_audit.review import (
    ReviewError,
    apply_suppressions,
    compare_reports,
    generate_explorer,
    verify_comparison,
    verify_review,
)
from access_audit.rules import RULES

__version__ = "1.0.0"

__all__ = [
    "RULES",
    "AuditError",
    "Finding",
    "ParseError",
    "ReviewError",
    "Rule",
    "Severity",
    "__version__",
    "apply_suppressions",
    "compare_reports",
    "create_report",
    "generate_explorer",
    "parse_html",
    "verify_comparison",
    "verify_report",
    "verify_review",
]

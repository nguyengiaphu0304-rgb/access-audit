"""Public API for Access Audit."""

from access_audit.engine import AuditError, create_report, verify_report
from access_audit.models import Finding, Rule, Severity
from access_audit.parser import ParseError, parse_html
from access_audit.rules import RULES

__version__ = "0.2.0"

__all__ = [
    "RULES",
    "AuditError",
    "Finding",
    "ParseError",
    "Rule",
    "Severity",
    "__version__",
    "create_report",
    "parse_html",
    "verify_report",
]

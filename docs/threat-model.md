# Threat model

## Protected properties

- Invalid UTF-8, NUL bytes, duplicate attributes, unsupported declarations,
  malformed nesting, and resource-limit violations fail closed.
- Unicode attribute values are NFC-normalized before ID and reference checks.
- Missing, duplicate, and normalization-colliding references cannot silently
  become valid.
- Finding order cannot depend on hash iteration, locale, file path, or time.
- Stored report counts cannot replace independent parsing and rule execution.
- Reports and operational summaries do not copy page content or identifiers.
- A zero-finding report cannot be presented by the tool as WCAG conformance.

## Untrusted input

All HTML bytes and previously generated report bytes are untrusted. HTML is
never executed, rendered, fetched, written into logs, or inserted into generated
markup.

## Resource limits

- source: 1 MiB;
- elements: 10,000;
- nesting depth: 64;
- attributes per element: 64;
- attribute value: 4,096 Unicode code points;
- findings: 10,000.

## Residual risks

Python's `HTMLParser` is not a browser parser. Strict closing-tag requirements
reject some technically recoverable HTML. Static source can differ completely
from the JavaScript-rendered DOM. The bounded name-signal approximation is not
the browser accessible-name algorithm. CSS, contrast, focus order, keyboard
interaction, zoom/reflow, media, shadow DOM, iframes, live regions, timing,
screen readers, cognitive load, language accuracy, and real user outcomes are
not tested.

SHA-256 does not authenticate the source or publisher. Reports retain structural
locations and tags, which can still reveal page shape.

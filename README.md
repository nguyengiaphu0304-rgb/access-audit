# Access Audit

Access Audit is a deterministic, local-first accessibility preflight engine for
saved HTML. It catches a focused set of structural problems before browser and
assistive-technology testing, emits privacy-minimized evidence, and can
independently reproduce every report.

It is not a WCAG conformance checker, certification tool, browser, or substitute
for axe, keyboard testing, screen readers, zoom/reflow, contrast review, or
testing with disabled people.

## What v0.1 checks

- document language and non-empty title;
- exactly one main landmark and an `h1`;
- skipped heading levels;
- image alternative attributes;
- form labels and control/link accessible-name signals;
- duplicate NFC-normalized IDs and missing ARIA ID references;
- positive `tabindex`;
- table captions or explicit accessible-name signals.

Reports include only rule IDs, severity, element tag, source location, stable
element index, aggregate counts, source SHA-256, and declared limitations. They
never copy page text, attribute values, paths, timestamps, host IDs, or exception
messages.

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
access-audit fixtures/failing.html --output demo-output/report.json
python -m pytest
```

The CLI exits `0` when no static finding exists, `1` when findings exist, and
`2` for invalid input or tool failure. A zero exit code still does not establish
accessibility or WCAG conformance.

Both checked fixtures are original CC0 synthetic data. Their finding counts are
regression evidence, not measurements from a public or private website.

## Verification

```bash
ruff check .
ruff format --check .
mypy src scripts
pytest
python scripts/demo.py --output demo-output/report.json
python scripts/demo.py --output demo-output/report-second.json
cmp demo-output/report.json demo-output/report-second.json
python -m build
python -m pip check
python -m pip_audit --skip-editable
```

## Design documentation

- [Architecture](docs/architecture.md)
- [Rule contract](docs/rule-contract.md)
- [Evidence and privacy contract](docs/evidence-contract.md)
- [Threat model](docs/threat-model.md)
- [ADR-001](docs/adr/001-static-preflight-boundary.md)
- [Roadmap](docs/roadmap.md)
- [Interview guide](docs/interview-guide.md)

## Current limitations

The parser sees source HTML, not a JavaScript-rendered accessibility tree.
Computed CSS, hidden-state semantics beyond explicit HTML/ARIA signals, contrast,
focus order, names computed from every ARIA mechanism, shadow DOM, iframes,
custom elements, media alternatives, and live browser behavior remain out of
scope. Rules intentionally prefer explicit “needs review” findings over claims
that an experience passes.

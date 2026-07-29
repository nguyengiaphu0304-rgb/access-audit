# Access Audit

Access Audit is a deterministic, local-first accessibility preflight engine for
saved HTML. It catches a focused set of structural problems before browser and
assistive-technology testing, emits privacy-minimized evidence, and can
independently reproduce every report.

It is not a WCAG conformance checker, certification tool, browser, or substitute
for axe, keyboard testing, screen readers, zoom/reflow, contrast review, or
testing with disabled people.

## What v1.0 checks

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

An optional development-only Chromium harness adds separate evidence for
axe-core findings, expected keyboard order, visible focus, 320 CSS-pixel reflow,
reduced motion and network isolation on an original synthetic fixture. A
digest-only manifest binds browser and static artifacts without treating either
as WCAG conformance.

The v0.3 review workflow adds immutable baseline comparison, expiring
report-bound suppressions and a responsive semantic finding explorer.
Suppressions never remove findings or hide new and severity-increased
regressions.

The source, tests, deterministic demo, wheel and canonical source archive are
prepared as a `v1.0.0` release candidate. The project is not yet published:
the required NVDA/Firefox and VoiceOver/Safari sessions remain explicitly
unperformed. See the [publication checklist](docs/releases/v1.0.0-checklist.md).

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
access-audit fixtures/failing.html --output demo-output/report.json
python -m pytest
python scripts/review_demo.py --output-directory demo-output/review
python scripts/release_demo.py --output-directory demo-output/release
npm ci
npx playwright install chromium
npm test
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
python scripts/package_release.py --dist dist --output release
python -m pip check
python -m pip_audit --skip-editable
npm audit --audit-level=high
```

## Design documentation

- [Architecture](docs/architecture.md)
- [Rule contract](docs/rule-contract.md)
- [Evidence and privacy contract](docs/evidence-contract.md)
- [Browser evidence contract](docs/browser-evidence-contract.md)
- [Review workflow contract](docs/review-contract.md)
- [Threat model](docs/threat-model.md)
- [ADR-001](docs/adr/001-static-preflight-boundary.md)
- [ADR-002](docs/adr/002-separate-browser-evidence.md)
- [ADR-003](docs/adr/003-auditable-review-state.md)
- [ADR-004](docs/adr/004-canonical-release-evidence.md)
- [Roadmap](docs/roadmap.md)
- [Interview guide](docs/interview-guide.md)
- [v1.0.0 release notes](docs/releases/v1.0.0.md)
- [v1.0.0 publication checklist](docs/releases/v1.0.0-checklist.md)
- [Support matrix](docs/releases/support-matrix.md)
- [Residual risks](docs/releases/residual-risks.md)

## Current limitations

The static parser still sees source HTML, not a browser accessibility tree. The
browser harness covers one synthetic Chromium fixture, not arbitrary pages.
Contrast review, full accessible-name computation, shadow DOM, iframes, custom
elements, media alternatives, screen readers, platform/browser diversity and
disabled-user testing remain out of scope. Rules intentionally prefer explicit
“needs review” findings over claims that an experience passes.

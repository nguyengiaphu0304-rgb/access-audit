# ADR-002: Keep browser evidence separate from static evidence

## Status

Accepted.

## Decision

Run a locked Chromium and axe-core harness only against original local synthetic
fixtures. Emit a browser-specific artifact and bind it to the static report with
a small combined manifest. Do not add browser dependencies to the Python runtime
or reinterpret either artifact as WCAG conformance.

## Consequences

Browser behavior, focus, reflow and motion become reproducible CI evidence while
the deterministic Python engine remains dependency-free. The evidence is still
limited to Chromium, one fixture and automated assertions; manual assistive
technology and user testing remain release gates.

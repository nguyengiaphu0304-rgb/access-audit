# ADR-001: Start with a deterministic static preflight boundary

## Status

Accepted for v0.1.

## Context

Browser automation and accessibility libraries can provide broader coverage but
also add rendering, dependency, network, and platform variability. An empty
portfolio repository first needs a trustworthy core whose claims are narrow and
testable.

## Decision

Build a dependency-free static HTML preflight engine. Parse bounded source into
an immutable text-minimized model, run a fixed registry of high-signal rules,
and independently reproduce canonical reports.

Every rule states its limitation. Output and CLI language explicitly deny WCAG
conformance or certification claims.

## Consequences

The core is portable, private, deterministic, and easy to interview about. It
will miss rendered-DOM and computed-style failures, and its strict parser rejects
some browser-recoverable markup. A later browser milestone must supplement this
engine rather than silently expand the meaning of existing static rules.

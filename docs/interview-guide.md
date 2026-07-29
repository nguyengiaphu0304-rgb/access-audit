# Interview guide

## Why not start with a full browser scanner?

The first engineering risk is dishonest evidence, not rule count. A small
deterministic core makes input limits, privacy, ordering, replay, and claim
boundaries executable before rendering complexity is introduced.

## Why discard text but keep `has_text`?

Several static checks need to distinguish an empty element from one with a text
signal. Storing only a boolean across each ancestor supports that narrow check
without copying page content into memory models or reports.

## Why strict HTML nesting?

Browsers recover malformed markup differently through a complex parsing
algorithm. v0.1 fails closed rather than pretending its standard-library parser
reconstructed the same DOM. Browser parsing is a separate roadmap boundary.

## Why report source locations and element indexes?

They make findings actionable and stable without including selectors, IDs,
names, labels, or page text. The trade-off is that page structure can still be
sensitive and reports need access control.

## Why include WCAG relationships instead of success-criterion claims?

Each rule is only one static signal. For example, `alt` presence says nothing
about quality, and a label association says nothing about spoken output. Calling
these relationships keeps the educational context without overstating coverage.

## What would change in a browser milestone?

The static report remains immutable. A separate browser evidence schema would
record browser/tool versions, rendered source lineage, axe results, keyboard and
reflow checks, budgets, and limitations. Combining evidence must never reinterpret
a v0.1 zero-finding report as conformance.

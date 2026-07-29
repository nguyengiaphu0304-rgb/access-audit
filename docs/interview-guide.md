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

## Why is browser evidence a separate artifact?

The static report remains immutable. The browser schema records locked tool
versions, source lineage, minimized axe results, keyboard, focus, reflow, motion,
security outcomes and limitations. A digest-only manifest binds the two without
pretending they have equivalent semantics. The no-network harness protects an
original synthetic fixture; it is not a safe renderer for hostile pages.

## Why can suppressions not change baseline results?

A suppression records a temporary review decision, not a change in evidence.
Computing regressions first ensures a new or severity-increased finding remains
visible even when a team has accepted or deferred it. Report-hash binding and
expiry prevent stale policy from silently following changed source.

## Why canonicalize the source archive?

Raw tar and gzip containers can carry build timestamps, owner fields and entry
ordering that change without source changes. The release verifier validates the
raw archive, then rebuilds a sorted archive with fixed metadata and rejects
unsafe member types or paths. This makes checksum drift actionable without
claiming cryptographic publisher identity.

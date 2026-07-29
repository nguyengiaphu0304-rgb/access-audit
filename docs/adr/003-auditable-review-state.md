# ADR-003: Review state cannot rewrite evidence

## Status

Accepted.

## Decision

Keep static reports immutable. Store suppressions as expiring, source-bound
review decisions and produce a separate summary. Compute baseline regressions
before considering suppression state. Generate the explorer from minimized
report fields with fixed local assets.

## Consequences

Teams can manage known findings without hiding their existence or turning
regressions into passes. Source changes invalidate old suppressions. Review
ownership is pseudonymous metadata rather than authentication, and expiry still
requires human governance.

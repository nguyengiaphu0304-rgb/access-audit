# ADR-004: canonical release evidence

## Decision

Build the wheel and source distribution twice under a fixed source epoch. Validate
both raw archives, then rebuild the sdist with sorted members, fixed timestamps,
numeric zero ownership, empty owner names and deterministic gzip metadata.

The release demo is offline, uses only original CC0 fixtures and records hashes,
sizes, counts and named checks. It does not record page text or claim manual
assistive-technology results.

## Why

Container metadata can cause checksum drift without a source change. Canonical
archives make drift reviewable, while strict member validation prevents the
canonicalizer from laundering traversal paths, links or unexpected build output.

## Consequences

The canonical sdist differs byte-for-byte from Hatchling's raw sdist. SHA-256
detects accidental change but does not authenticate the publisher. Signing and
trusted provenance remain future work.

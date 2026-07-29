# Review workflow contract

Suppressions are explicit, bounded review decisions, not deleted findings. Each
artifact is bound to the exact report SHA-256 and an explicit `as_of` date. Every
entry requires a normalized ID, pseudonymous owner, allowlisted rationale,
finding identity, creation date and expiry no more than 366 days later.

Invalid, expired, duplicated, over-budget, unknown-field, lineage-mismatched or
missing-target entries fail closed. The original report remains byte-identical;
the review summary lists minimized suppression metadata separately.

Baseline comparison operates only on canonical reports. Identity is the stable
rule ID, element index and element tag. New and severity-increased findings are
always regressions, regardless of suppression state. Resolved, unchanged and
severity-decreased findings remain visible.

The explorer contains only minimized finding fields already present in the
report. It does not include source hashes, page text, selectors, IDs, labels,
URLs or filesystem paths.

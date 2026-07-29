# Browser evidence contract

Browser evidence is a separate, versioned observation of one original synthetic
fixture. It never upgrades a static result to a conformance claim.

The harness binds the fixture, stylesheet, harness, static report, Playwright,
and axe-core versions by SHA-256 or locked version. It records only aggregate
axe rule IDs, impacts and counts; fixed synthetic keyboard tokens; boolean
security, reflow and motion outcomes; and a focus-outline measurement. It does
not retain DOM snippets, selectors, page text, URLs, paths, timestamps, host
identifiers, screenshots, raw console output or exception messages.

All content is served from an ephemeral IPv4 loopback socket through an exact
path allowlist. CSP denies connections and Playwright aborts every request whose
origin differs from that socket. This reduces accidental egress during the
fixture run; it is not a browser sandbox and does not make untrusted pages safe.

The combined manifest binds the static and browser artifacts without merging
their schemas or meanings. Verification rejects unknown top-level fields,
digest drift, oversize artifacts and privacy sentinels.

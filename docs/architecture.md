# Architecture

Access Audit v0.1 has five explicit boundaries:

1. `parser.py` decodes bounded UTF-8, rejects ambiguous markup, normalizes
   attribute values to NFC, and creates immutable elements with source locations.
   It retains only whether an element has non-whitespace descendant text, never
   the text itself.
2. `rules.py` is the stable metadata registry. Each rule has an ID, severity,
   title, WCAG relationship, and limitation.
3. `engine.audit` evaluates the immutable document without network, filesystem,
   browser, locale, or clock state.
4. `create_report` emits canonical JSON with source lineage and minimized
   findings. `verify_report` reparses and reruns the entire audit rather than
   trusting stored counts.
5. `cli.py` maps findings and invalid input to documented exit codes and writes
   only an aggregate structured operational event to stderr.

The core has no runtime dependency, network client, browser, database, plugin
loader, configuration file, telemetry backend, or hidden global mutable state.

## Data flow

```text
bounded HTML bytes
        |
 strict UTF-8 + structural parser
        |
 immutable text-minimized document
        |
 deterministic static rules
        |
 canonical privacy-minimized report
        |
 independent full replay
```

This architecture makes static evidence reproducible. It intentionally cannot
observe the rendered accessibility tree or user experience.

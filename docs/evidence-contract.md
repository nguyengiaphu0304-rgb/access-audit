# Evidence and privacy contract

The report envelope uses schema `access-audit/report-v1` and contains:

- source byte count and SHA-256;
- parser element count;
- stable tool and schema versions;
- deterministic rule metadata and declared limitations;
- aggregate error, warning, finding, and per-rule counts;
- sorted privacy-minimized findings;
- SHA-256 of the canonical payload.

Reports never include:

- HTML text or comments;
- attribute values, including IDs, labels, URLs, alternative text, or ARIA
  references;
- input paths, timestamps, process/host identifiers, environment variables, or
  exception text.

The CLI emits only counts and a fixed event name. A failure emits a fixed reason
code. Source files and reports still require appropriate access control:
SHA-256 lineage is not anonymity, encryption, or publisher authentication.

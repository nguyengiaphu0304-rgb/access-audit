# Rule contract

Rules are deterministic preflight heuristics, not pass/fail WCAG techniques.
Every finding includes only rule ID, severity, element tag, source line/column,
and stable element index.

| Rule | Static check | Severity | Relationship |
| --- | --- | --- | --- |
| AA001 | `<html>` has a non-empty `lang` | error | WCAG 3.1.1 |
| AA002 | exactly one non-empty `<title>` | error | WCAG 2.4.2 |
| AA003 | exactly one main landmark | error | WCAG 1.3.1 |
| AA004 | an `h1` exists and levels do not skip upward | warning | WCAG 1.3.1, 2.4.6 |
| AA005 | non-decorative visible `<img>` has `alt` | error | WCAG 1.1.1 |
| AA006 | common form inputs have an explicit label signal | error | WCAG 1.3.1, 3.3.2 |
| AA007 | button-like controls have a name signal | error | WCAG 4.1.2 |
| AA008 | links with `href` have a name signal | error | WCAG 2.4.4, 4.1.2 |
| AA009 | non-empty NFC-normalized IDs are unique | error | WCAG 4.1.1 historical relationship |
| AA010 | supported ARIA IDREF attributes target existing IDs | error | WCAG 1.3.1, 4.1.2 |
| AA011 | positive `tabindex` is flagged for review | warning | WCAG 2.4.3 |
| AA012 | tables have a caption or explicit name signal | warning | WCAG 1.3.1 |

Attribute presence does not establish quality. In particular, Access Audit does
not judge whether `lang`, alternative text, labels, link purpose, headings,
captions, roles, or ARIA usage are semantically correct.

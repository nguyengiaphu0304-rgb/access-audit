# Residual risks

- Static parsing is not a browser accessibility tree or full accessible-name
  computation.
- Chromium evidence covers one synthetic page and cannot establish behavior on
  arbitrary JavaScript, shadow DOM, iframe or hostile content.
- Automated axe, keyboard, focus, motion and reflow checks are incomplete and do
  not establish WCAG conformance.
- NVDA/Firefox, VoiceOver/Safari and disabled-user sessions are not yet performed.
- Suppression owners are pseudonymous; expiry and source binding do not prove
  authorization.
- SHA-256 detects drift but does not authenticate artifacts or publishers.
- The project has no sandbox for untrusted active pages, signing, telemetry,
  remote retention, production incident response or disaster-recovery evidence.

The release remains a candidate until the manual accessibility and publication
checklists pass.

# Support and recovery matrix

| Boundary | Verified | Not verified |
| --- | --- | --- |
| Python core | CPython 3.11-3.13 on Ubuntu CI | Windows, macOS, PyPy |
| Browser evidence | Locked Chromium on Ubuntu, loopback synthetic fixture | Firefox, Safari, arbitrary or hostile pages |
| Assistive technology | None | NVDA, VoiceOver, JAWS, TalkBack |
| Package recovery | Offline wheel reinstall; canonical sdist inspection | Signed provenance, registry compromise recovery |
| Data recovery | Inputs are immutable local files; artifacts regenerate deterministically | Remote retention, backup service, multi-host coordination |

Failure recovery is regeneration from the exact source commit and fixtures. A
checksum mismatch fails the release gate; it is never silently accepted.

# Local Release Audit

This file records checks executed against the source used for the SynapDrive-AI v1.0.0 handoff. It is not a hardware, clinical, or human-BCI certification.

- Release: `1.0.0`
- Original isolated-build audit timestamp (UTC): `2026-08-26T17:12:37+00:00`
- Original isolated-build Python: `3.13.5`
- Windows verification Python: `3.13.2`
- Pytest: **138 passed, 0 failed, 0 skipped**
- Package-wide branch coverage: **69.699%** (`3052` statements, `608` branches), measured in the isolated build audit
- Canonical pipeline coverage: **97.2%**, measured in the same isolated coverage run
- Release validator: **24/24 checks passed**
- Ruff on Windows: **All checks passed**
- Pyright on Windows: **0 errors, 0 warnings, 0 informations**
- Python compileall: passed in the isolated build audit
- Offline wheel build: passed
- Wheel installed into an isolated target directory: passed
- Discovered installed runtime modules: **88**, import failures: **0**
- Canonical pipeline executed from isolated wheel install: passed
- Static source audit: 0 syntax, line-length, trailing-whitespace, tab, bare-except, ambiguous-name, or unused-import findings under the repository audit rules

## Static-analysis verification

Ruff and Pyright could not be obtained inside the original isolated build environment because outbound package acquisition was unavailable there.

They were subsequently installed from the repository's declared development requirements and executed against the final v1.0.0 working tree on Windows 11 with Python 3.13.2.

Final Windows results:

- `python -m ruff check .` → **All checks passed**
- `python -m pyright` → **0 errors, 0 warnings, 0 informations**
- `python -m pytest -q` → **138 passed**
- `python -m scripts.run_v1_validation` → **passed: true, 24/24 checks passed**

GitHub CI remains configured to independently run the repository's quality gates on its declared Python matrix.

## Evidence boundary

`RELEASE_VALIDATION.json` uses deterministic synthetic verification data for software-path checks. Its benchmark metrics are not human EEG performance, clinical validation, hardware safety evidence, or proof of physical actuation.

No claim in this release should be interpreted as evidence of medical efficacy, clinical validation, physical BCI safety, or validated human neural-decoding performance.
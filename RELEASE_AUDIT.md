# Local release verification: 2.0.0

Verified on Linux x86_64, Python 3.12.14. The runtime contains
new executable implementations; it is no longer the original design-only package.

| Check | Observed result |
| --- | --- |
| Pytest | 225 passed; zero failed, errored or skipped |
| Ruff | Passed |
| Pyright | Zero errors, zero warnings |
| Statement coverage | 73.32% |
| Branch coverage | 57.04% |
| Combined statement/branch coverage | 70.21% |
| Independent fault fixtures | 120 cases passed, including clean acceptance controls |
| Declared 1D recoverable states | 933 stopped inside the envelope; zero failures |
| Concurrency | 800 successful cycles, eight threads; complete valid ledger |
| Build | Source distribution and wheel built successfully |
| Installed-wheel checks | Demo, EEG reproduction, command recording and rejection-feedback replay passed outside checkout |
| Original data | All 24 source EDF hashes matched the official manifest |
| Remote GitHub Actions | Unverified |

Coverage excludes the test source. The existing suite was extended with audit regression,
state/replay/permit tests and real-data inference. One third-party AnyIO plugin emitted
a deprecation warning. All recorded-data predictions and artifact identities reproduced
from the installed wheel.

The original design is not fully complete. Recorded EEG performance remains inadequate
for a dependable-control claim; 3 of 7 admitted actions were wrong. See `RESULTS.md` and
`docs/REQUIREMENT_STATUS.json`. Passing these software checks does not establish clinical
benefit, hardware safety, OS isolation, or remote CI status.

Reproduce with `python -m pytest -q`, `python -m ruff check .`, `python -m pyright`,
`python -m scripts.validate_release`, and `python -m synapdrive_ai.v2 eeg`.

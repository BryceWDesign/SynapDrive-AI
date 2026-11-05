> Historical pre-implementation design snapshot. Its planned/not-run statements
> describe the earlier package. See [implemented v2 scope](../../V2_IMPLEMENTED.md)
> and [current requirement status](../../REQUIREMENT_STATUS.json) for this release.

# Design verification record

**Date: 2 November 2026. Scope: R0 design package. Runtime remains v1.0.0.**

| Check | Observed result | Scope |
| --- | --- | --- |
| Baseline file integrity | 137 unchanged, seven recorded publication edits, one regenerated manifest | Original hashes retained in `baseline.json`; runtime logic unchanged |
| Existing tests | 138 passed | Existing v1 tests; one environment-plugin deprecation warning; no v2 acceptance cases executed |
| Ruff | Passed | Whole package |
| Pyright | Zero errors/warnings | Original runtime and new design utilities |
| Design consistency | Passed | 27 sources, 15 problems, 10 planned modules, 40 linked requirements/cases, 10 experiments |
| Deliberately broken design/integrity controls | All nine detected | Seven specification controls and two baseline-digest controls |
| Bounded admission model | 2,256 states and 5,960 transitions explored; no modeled violation | Atomic abstract protocol; one permit and explicit finite bounds |
| Removed admission guards | All seven produced counterexamples | Demonstrates sensitivity to action, capability, world, expiry, use, preparation and veto guards |
| Strict full-release check | Refused as expected, exit code 2 | Proposed implementations/evidence and six parameter decisions remain incomplete |
| Document links/fences and JSON/Python syntax | Passed | Artifact consistency |
| Remote GitHub Actions | Not verified | No remote run claimed |

The model check is not proof of production code, scheduler, network, decoder or physical safety. Runtime acceptance cases are all marked not run; experiments are all planned. The original archive contained a stale validation-file checksum. Local release records and `RELEASE_MANIFEST.sha256` are regenerated for this package. The manifest covers every packaged file except itself and does not assert scientific validity. Maintenance changes affect documentation, two runtime docstrings and one test name/message; runtime logic is unchanged. Original runtime defects remain documented and unresolved.

Machine-readable reports: `design-validation.json`, `admission-model-results.json`, `strict-release-result.json`, and `STATUS.json`.

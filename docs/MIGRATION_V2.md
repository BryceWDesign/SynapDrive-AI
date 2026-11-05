# Migration from v1

Replace repository source with this release while preserving your existing `.git`
directory. Recreate/install the environment with `pip install -e ".[dev,eeg]"`.
Do not commit private keys, local journals, or personal EEG recordings.

Behavior changes:

- Packets require nonempty `intent` and `source`, finite numeric confidence and
  valid JSON. Numeric strings, booleans as measurements and malformed distributions
  are rejected before action. Neural packets require quality, drift and qualification
  identity; caller-provided identity fields are not external authentication.
- Command text must match one supported command exactly. Negated, compound and
  incidental command phrases are rejected.
- Uncertainty supplied by a packet can only increase the independently derived gate.
- Successful execution without explicit acceptance creates unconfirmed memory.
  Use `pipeline.apply_feedback(cycle_id, accepted, lifecycle)` for delayed feedback.
- `TaskStep` confidence must be in [0,1]. `freeze` pauses the plan; `defer` skips one
  independent step. `requires` refers to earlier successful steps. `complete` retains
  legacy continuation behavior but never overrides a blocked action.
- `SimplexController` requires a current `runtime` to use its advanced callback.
  It reassesses before issuing an action-bound permit. Without it, only fallback runs.
- Replay v2 includes a complete supported capsule. The CLI refuses legacy records
  lacking decision context instead of claiming faithful replay.
- `QualifiedDecoderAdapter` remains a legacy local trial-split research bridge;
  it no longer refits after evaluation. Prefer `EEGDecoder` and the fixed grouped
  experiment for exact identity, calibration/audit separation and recorded-data use.
- `StressCampaign` requires explicit expected outcomes for arbitrary fault scenarios;
  only named clean/flatline fixtures have a built-in expectation. Expectations are
  independent of the detector score, and always-abstain fails clean controls.

For durable dispatch use `SynapDrivePipeline(journal_path="run.sqlite")`. On restart,
`pipeline.dispatch.journal.unresolved()` lists prepared/unknown operations. Reconcile
only after an independent outcome check. Do not clear the journal to force a retry.
`pipeline.emergency_stop()` remains available when a run budget or journal fails;
`pipeline.resume()` refuses unresolved outcomes.

Existing v1 tests were preserved. Fixtures were updated for required packet provenance,
valid thresholds, v2 replay schema and the unconfirmed-memory distinction. Audit
regressions, recorded-data inference and new behavior are tested separately.

## Module paths

Signal-processing helpers are under `synapdrive_ai.processing`. Deterministic planning
is provided by `core.planning.deterministic_planner.DeterministicPlanner`. Update imports
that used the previous helper paths; the unused general-intelligence aliases are removed.

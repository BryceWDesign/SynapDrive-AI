# Updating an existing checkout

Keep your existing `.git` directory and remote configuration. Replace the project
source with the contents of the `SynapDrive-AI` directory in this archive.

If you copy files over an existing checkout, remove these retired paths:

- `scripts/validate_v2_design.py`
- `scripts/check_v2_admission_model.py`
- `synapdrive_ai/agi/` (replaced by `synapdrive_ai/processing/`)
- `core/planning/agi_planner.py` (replaced by `deterministic_planner.py`)
- `V2_UPDATE_DESIGN.md` and `docs/v2/` (moved under `docs/history/`)

The two design-check scripts are retained as text under
`docs/history/preimplementation`. The current validator is
`python -m scripts.validate_release`; `scripts.run_v1_validation` is a compatibility
alias for that command.

Install with `python -m pip install -e ".[dev,eeg]"`, then run the commands in README.
Review `git status` before committing so local data, journals, keys and unrelated
changes are not accidentally included. This archive does not contain Git history or
claim that a remote GitHub Actions run has already passed.

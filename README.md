# SynapDrive-AI 2.0.0

Executable research software for recorded-EEG decoding, governed simulated actions,
local access tasks, and reproducible failure analysis. Apache-2.0 code; the bundled
EEG-derived data have separate attribution terms in `synapdrive_ai/assets/DATA_LICENSE.txt`.

This release implements working software beyond the earlier v2 design package.
It does **not** complete the entire research roadmap. The measured EEG results below
are insufficient to claim dependable assistive neural control.

## Run it

Python 3.11–3.13. From the repository directory, on Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,eeg]"
python -m synapdrive_ai.v2 demo
python -m synapdrive_ai.v2 eeg --out results/eeg-reproduced
python -m pytest -q
python -m scripts.validate_release
```

On Linux/macOS, use `python3 -m venv .venv` and `source .venv/bin/activate`, then
run the same Python commands. Scientific dependencies are needed for EEG evaluation;
`pip install -e .` is sufficient for the ordinary simulation and local-task demo.
The processed recorded-EEG epochs are included, so evaluation needs no data download.
An internet connection is required for the initial dependency installation.

`demo` exercises rejected commands, execution, rejected-feedback replay, actual
simulated braking, exact-output approval, and supervised adaptation rollback.
`eeg` trains the recorded-signal models, calibrates on a separate run, evaluates a
held-out run, writes portable models/reports, and sends qualified predictions through
the canonical pipeline. Repeating the experiment reproduces the same evidence;
it is not a new independent study or permission to tune against its audit labels.

## Implemented in this release

- Finite, typed, bounded packet validation before any action; independently derived
  uncertainty cannot be lowered by an input packet.
- Exact command grammar, exact stop capability identifiers, and an independent
  trusted operator stop API that does not wait for journal writes.
- Action-bound, expiring, single-use permits checked at the executor boundary;
  current world/policy/capability binding and SQLite prepared/outcome records.
- Interrupted-dispatch reconciliation: unresolved outcomes block new ordinary
  actions and are never automatically retried.
- Per-channel signal exclusions, time-ordered fresh stream windows, exact
  acquisition identities, and duplicate/replayed-window rejection.
- A real trained CSP + shrinkage-LDA EEG decoder, separate temperature calibration,
  no refit on audit data, numeric-only NPZ artifacts, artifact mutation/expiry checks,
  and locked audit/fit overlap checks.
- Local access tasks: qualified-input transitions, distinct-evidence sequential
  confirmation, user-owned preferences, original draft/suggestion separation,
  exact-content single-use approval, privacy lock, export consent and encrypted content.
- Decoder-update evaluation tied to exact trained candidates, consumed audit trial
  identities, evaluator-owned metrics, promotion checks, and dependent rollback.
- Versioned replay capsules containing policy, capabilities, action models, initial
  state and feedback; built-in plant state is replayed and divergence fails explicitly.
- Unconfirmed versus confirmed versus contradicted memory; delayed rejection retracts
  associated history and can invalidate dependent model updates.
- Signed run checkpoints that verify run identity, count and final ledger head.
- An independent 1D plant, state-dependent braking, recovery-envelope monitoring,
  labeled fault oracles, and bounded run/permit budgets.

The direct Python API is a **trusted simulation API**. It is not a security sandbox
against arbitrary code running under the same account. The local task output is an
in-memory workspace, not a live email, operating-system input or physical endpoint.

## Recorded EEG results

Dataset: PhysioNet EEG Motor Movement/Imagery Dataset v1.0.0, subjects S001–S008.
Runs 04/08/12 contain left/right fist imagery and intervening rest. The split is fixed:
R04 training, R08 temperature calibration, R12 evaluation. One nonoverlapping
0.5–3.5 second epoch per annotation; nine named channels; three classes.

| Participant | Held-out balanced accuracy | Local decoder gates | Simulated actions admitted | Incorrect admitted actions |
| --- | ---: | --- | ---: | ---: |
| S001 | 62.98% | Fail | 0 | 0 |
| S002 | 52.58% | Fail | 0 | 0 |
| S003 | 41.03% | Fail | 0 | 0 |
| S004 | 61.31% | Pass | 7 | 3 |
| S005 | 42.26% | Fail | 0 | 0 |
| S006 | 37.50% | Fail | 0 | 0 |
| S007 | 58.69% | Pass | 0 | 0 |
| S008 | 39.80% | Fail | 0 | 0 |

Mean balanced accuracy: **49.52%**; participant-cluster bootstrap 95% interval:
**42.92–56.32%**. Two models pass the declared local numerical gates, but only one
produces actions after the complete runtime gates. Across 240 evaluation epochs,
seven actions were admitted: four correct and three incorrect. There were no
admitted rest epochs in this small experiment. Abstaining on 233 epochs does not
establish useful access, and local qualification is not a reliability certification.

These are within-person, held-out-run results, not cross-person or cross-session
validation, live closed-loop use, or evidence of benefit for people with disabilities.
The spectral filtering uses the complete three-second epoch; this is windowed
research inference, not a measured low-latency streaming neural interface.

All participant results, label-permutation controls, predictions, error counts,
abstention reasons and artifact identities are in [results/eeg/recorded-eeg.json](results/eeg/recorded-eeg.json).
No failed participant was removed. All 24 downloaded EDF sources were checked against
the dataset's official SHA-256 manifest; provenance is in [results/EEG_SOURCES.json](results/EEG_SOURCES.json).

## Verification

```text
python -m ruff check .
python -m pyright
python -m pytest -q --cov=synapdrive_ai --cov=core --cov-branch
python -m scripts.validate_release
python -m synapdrive_ai --text "move left" --no-delay
python -m synapdrive_ai --text "move left" --reject-feedback --record runs.jsonl --no-delay
python -m synapdrive_ai --replay runs.jsonl
```

The independent release validator exercises 120 labeled fault cases, 933 recoverable
plant scenarios and 800 cycles across eight threads. Its complete results are in
[results/software-validation.json](results/software-validation.json). These are
software/simulation checks, not physiological or physical safety evidence.
GitHub Actions is configured for Python 3.11, 3.12 and 3.13. Remote CI is **unverified**
until the workflow actually runs on the uploaded repository.

## Documentation

- [Implemented scope and audit resolution](docs/V2_IMPLEMENTED.md)
- [Results and remaining gaps](RESULTS.md)
- [Current architecture](docs/ARCHITECTURE.md)
- [Migration from v1](docs/MIGRATION_V2.md)
- [Data attribution and reproduction](docs/RECORDED_EEG.md)
- [Original design snapshot](docs/history/PREIMPLEMENTATION_DESIGN.md), retained as historical context

## Boundaries

No medical-device, clinical, autonomous-authority, cybersecurity-certification or
safe physical-control claim is made. Intended-user/caregiver studies, hardware
validation, OS-enforced worker isolation, broader decoder comparisons, physiological
co-adaptation studies and longitudinal deployment remain incomplete. The original
40-requirement design remains broader than the implemented release; its complete
status mapping is in `docs/REQUIREMENT_STATUS.json`.

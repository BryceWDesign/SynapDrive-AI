# SynapDrive-AI

SynapDrive-AI is a **simulation-first BCI safety and control scaffold**.

It is built around one practical question:

> If a system thinks the user intended an action, what should happen **before** anything is allowed to move?

This repo answers that with a runnable pipeline:

**intent → context adjustment → safety gate → simulated actuation → evaluation**

It runs **without hardware**, supports **record/replay**, includes a **local dashboard**, and now also includes **offline EEG-style analysis tools** for session review and threshold tuning.

## What this repo is

- A **runnable reference implementation** for safe intent handling
- A **simulation environment** for testing control logic without devices
- A **safety middleware layer** between decoded intent and downstream action
- A **small neuroscience tooling layer** for offline EEG-style analysis and task sequencing

## What this repo is not

- Not a medical device
- Not a clinical decoder
- Not proof of real-world BCI control performance
- Not a claim that text prompts or synthetic signals equal real neural intent decoding

That boundary matters.

---

## Current working surface

The repaired repo now supports these paths cleanly:

### 1) Canonical command path
Run a text command or simulated signal through the full pipeline.

### 2) Safety-first execution
Low-confidence or prohibited intents are blocked before actuation.

### 3) Reproducible record/replay
Sessions can be written to JSONL and replayed deterministically.

### 4) Local dashboard
A Flask dashboard exposes the pipeline and latest telemetry.

### 5) Offline EEG-style analysis
Analyze EDF, BDF, CSV, or NPY data using simple band-power logic, then run those epochs through the same safety pipeline.

### 6) Sequential task planning
Execute multi-step plans with per-step minimum confidence and fallback behavior.

---

## Core pipeline

```text
text / simulated signal / EEG-derived epoch
                ↓
          intent packet
                ↓
     cognitive optimizer
     (memory + visual context)
                ↓
           safety gate
   (confidence + prohibited intent checks)
                ↓
       simulated actuation
                ↓
          meta evaluation
```

Default safety behavior is conservative:

- **Minimum confidence threshold:** `0.45`
- **Hard block list:** unsafe phrases such as disabling brakes, overriding security, triggering launch, and similar prohibited actions

---

## Quickstart

### Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
```

For development and tests:

```bash
pip install -r requirements-dev.txt
```

---

## Run the main CLI

### Text path

```bash
python -m synapdrive_ai --text "move left" --image road --no-delay
python -m synapdrive_ai --text "stop" --image hazard --no-delay
```

### Simulated signal path

```bash
python -m synapdrive_ai --signal walk --count 3 --interval 1 --no-delay
python -m synapdrive_ai --signal stop --no-delay
```

### Record and replay

```bash
python -m synapdrive_ai --text "move left" --image road --record runs.jsonl --no-delay
python -m synapdrive_ai --replay runs.jsonl
```

---

## Dashboard

Run the local dashboard:

```bash
python -m synapdrive_ai.interface.web_dashboard
```

Then open:

```text
http://127.0.0.1:5055
```

What the dashboard gives you:

- Text command execution
- Simulated signal execution
- Latest telemetry log from the action router

You can also use the console script installed by `pip install .`:

```bash
synapdrive-dashboard
```

---

## Neuroscience tools

The repo now includes an offline neuro-analysis layer under `synapdrive_ai/neuro/`.

### Demo with synthetic EEG-like data

```bash
python -m synapdrive_ai.neuro.cli demo
```

This runs a synthetic session with a motor-style burst and prints:

- Relative band power
- Engagement ratio
- Intent class
- Confidence
- Epoch-by-epoch pipeline status

### Analyze a file

```bash
python -m synapdrive_ai.neuro.cli analyze session.edf --channel C3 --out results/
```

### List channels in a file

```bash
python -m synapdrive_ai.neuro.cli analyze session.edf --channels
```

### Sweep confidence thresholds

```bash
python -m synapdrive_ai.neuro.cli threshold session.edf --min-conf 0.4 0.5 0.6 0.7
```

### Run a sequential task plan

```bash
python -m synapdrive_ai.neuro.cli plan --list
python -m synapdrive_ai.neuro.cli plan --task reach_grasp
```

---

## Supported EEG-style file formats

The lightweight loader supports:

- `.edf`
- `.bdf`
- `.csv`
- `.npy`

Notes:

- CSV time columns are auto-detected when possible
- NPY can be 1-D or 2-D
- The loader is intentionally lightweight and does **not** try to replace full research toolchains

---

## Neuro-analysis logic

The offline analyzer uses a simple band-power approach:

- **Delta:** 0.5–4 Hz
- **Theta:** 4–8 Hz
- **Alpha:** 8–13 Hz
- **Beta:** 13–30 Hz
- **Gamma:** 30–80 Hz

It derives:

- **Engagement ratio**
- **Cognitive ratio**
- **Intent class:** `motor`, `cognitive`, or `unclear`
- **Signal confidence**

Those epochs are then run through the same SynapDrive safety pipeline so you can inspect:

- pass/block rate
- confidence distribution
- evaluation scores
- exported JSONL / CSV results

This is useful as a **prototype analysis layer**, not a substitute for validated neuroscience tooling.

---

## Sequential task planning

Single commands are easy to demo. Real control problems are not.

`synapdrive_ai/neuro/task_planner.py` adds a simple sequential execution model with:

- per-step labels
- per-step minimum confidence
- fallback policies:
  - `freeze`
  - `abort`
  - `complete`

That lets you model the real failure question:

> What should happen when step 3 of a multi-step action becomes uncertain?

---

## Optional integrations

The repo still keeps optional hardware-facing adapters separate from the default install.

### BrainFlow

```bash
pip install -r requirements-brainflow.txt
python -m synapdrive_ai --brainflow --bf-board-id 0 --bf-seconds 2 --no-delay
```

### LSL / pylsl

```bash
pip install -r requirements-lsl.txt
python -m synapdrive_ai --lsl --lsl-type EEG --lsl-seconds 2 --no-delay
```

These are optional and do not change the default simulation-first workflow.

---

## Tests

Run the test suite:

```bash
pytest -q
```

The repaired repo includes tests for:

- canonical pipeline execution
- blocked/allowed intent behavior
- action log contract
- public `run_intent_packet()` path
- band-power analysis
- EEG array loading
- session analysis outputs
- task-plan execution behavior

---

## Repository layout

```text
synapdrive_ai/
├── pipeline.py                  # canonical pipeline wiring
├── bci/                         # signal simulation + intent generation
├── agi/                         # reasoning, optimization, evaluation
├── safety/                      # confidence gate + prohibited intent blocking
├── action/                      # routing / execution surface
├── control/                     # simulated actuation engine
├── replay/                      # JSONL record/replay
├── interface/                   # Flask dashboard
├── neuro/                       # offline EEG analysis + task planning
└── tests/                       # regression and contract tests
```

---

## Why this repo is useful now

Before repair, the public repo surface was out of sync with the code path people were likely trying to run.

Now it is back in a credible lane:

- the canonical pipeline contract is restored
- tests target the public runtime surface
- install/package behavior is cleaned up
- the dashboard path is aligned with the working pipeline
- the repo has a real upgrade path beyond a toy command demo

That is the correct direction for this project.

---

## Practical next upgrades

If this continues, the highest-value next steps are:

1. **Dashboard upgrade**
   - session summary cards
   - pass/block counters
   - threshold controls
   - neuro-analysis upload flow

2. **Replay inspection**
   - compare two runs side by side
   - diff threshold behavior
   - export summaries directly from the UI

3. **Signal realism**
   - artifact injection
   - multi-channel analysis
   - confidence decay over time
   - stronger mapping between band features and task classes

4. **Safer sequence control**
   - rollback behavior
   - explicit operator confirmation steps
   - risk-tiered step policies

---

## License

Apache-2.0

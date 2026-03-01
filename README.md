# SynapDrive-AI

SynapDrive-AI is a **simulation-first** reference pipeline for **intent → context → safety gate → actuation**, built to be runnable **without hardware**.

**No medical/clinical claims.** Optional integrations (BrainFlow / LSL) are supported, but not installed by default.

## Why it exists
A clean, reproducible scaffold for teams that need:
- **Safe-by-default gating** (block unknown/low-confidence intents)
- **Stable telemetry contracts** (dashboards/tests don’t break on schema drift)
- **Record/replay (JSONL)** for reproducible validation and regression checks

## What you can do
- Run an end-to-end loop from text or simulated signals
- Record runs to JSONL and replay deterministically
- Use a local Flask dashboard to trigger actions and inspect telemetry
- Plug in optional BrainFlow or LSL (pylsl) intent sources

## Quickstart

### Install
~~~bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
~~~

### Run (text intent)
~~~bash
python -m synapdrive_ai --text "move left" --image road --no-delay
python -m synapdrive_ai --text "stop" --image hazard --no-delay
~~~

### Run (simulated signal label)
~~~bash
python -m synapdrive_ai --signal walk --count 3 --interval 1 --no-delay
~~~

### Test
~~~bash
pip install -r requirements-dev.txt
pytest -q
~~~

## Record & replay (reproducible)
~~~bash
python -m synapdrive_ai --text "move left" --image road --record runs.jsonl --no-delay
python -m synapdrive_ai --replay runs.jsonl
~~~

## Dashboard (Flask)
~~~bash
python -m synapdrive_ai.interface.web_dashboard
~~~
Open: http://127.0.0.1:5055

## Optional integrations (not installed by default)

### BrainFlow
~~~bash
pip install -r requirements-brainflow.txt
python -m synapdrive_ai --brainflow --bf-board-id 0 --bf-seconds 2 --no-delay
~~~

### LSL / pylsl
~~~bash
pip install -r requirements-lsl.txt
python -m synapdrive_ai --lsl --lsl-type EEG --lsl-seconds 2 --no-delay
~~~

## Key files
- `synapdrive_ai/pipeline.py` — canonical wiring (intent → optimize → safety → route → evaluate)
- `synapdrive_ai/safety/safety_guard.py` — conservative gating rules
- `synapdrive_ai/control/actuation_engine.py` — simulated actuation + telemetry schema
- `synapdrive_ai/replay/recording.py` — JSONL record/replay
- `synapdrive_ai/interface/web_dashboard.py` — Flask UI + API
- `synapdrive_ai/tests/` — contract tests + dashboard API tests

## License
Apache-2.0 (see `LICENSE`)

# SynapDrive-AI

**SynapDrive-AI** is a **simulation-first** reference implementation of an **intent → context → safety gate → actuation** pipeline inspired by autonomy + BCI workflows.

This repo makes **no medical/clinical claims**. It’s designed to be runnable without hardware, while still supporting **optional** real-world input pathways (BrainFlow / LSL).

---

## What it does

- End-to-end loop: **intent → optimizer (memory + vision context) → safety gate → actuation → evaluation**
- **Safe-by-default:** unknown / low-confidence intents are blocked
- **Telemetry contract:** stable log schema for dashboards/tests
- **Reproducibility:** record/replay (JSONL)
- **Quality gates:** tests + CI + lint + type-check + coverage
- **Dashboard:** local Flask UI for quick inspection

---

## Architecture (canonical pipeline)

```mermaid
flowchart LR
    A[Input: decoded text / simulated signal / BrainFlow / LSL] --> B[Intent packet]
    B --> C[Context optimizer: memory + vision]
    C --> D{SafetyGate}
    D -- safe --> E[DecisionRouter]
    D -- blocked --> X[Blocked response]
    E --> F[ActuationEngine (simulated)]
    F --> G[EpisodicMemory]
    F --> H[MetaEvaluator]
    G --> C

Single source of truth wiring: synapdrive_ai/pipeline.py

Quickstart
Install
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
Run (decoded intent text)
python -m synapdrive_ai --text "move left" --image road --no-delay
python -m synapdrive_ai --text "stop" --image hazard --no-delay
Run (simulated signal label)
python -m synapdrive_ai --signal walk --count 3 --interval 1 --no-delay
python -m synapdrive_ai --signal stop --no-delay
Tests
pip install -r requirements-dev.txt
pytest -q
Record & replay (reproducible runs)

Record a run to JSONL:

python -m synapdrive_ai --text "move left" --image road --record runs.jsonl --no-delay
python -m synapdrive_ai --signal walk --count 3 --record runs.jsonl --no-delay

Replay later (deterministic, no-delay):

python -m synapdrive_ai --replay runs.jsonl
Dashboard (Flask)

Run:

python -m synapdrive_ai.interface.web_dashboard

Open:

http://127.0.0.1:5055

Optional integrations (not installed by default)
BrainFlow (optional)

Install:

pip install -r requirements-brainflow.txt

Run (defaults to BrainFlow Synthetic board, id=0):

python -m synapdrive_ai --brainflow --bf-board-id 0 --bf-seconds 2 --no-delay
LSL / pylsl (optional)

Install:

pip install -r requirements-lsl.txt

Run (recommend specifying stream type or name):

python -m synapdrive_ai --lsl --lsl-type EEG --lsl-seconds 2 --no-delay
# or
python -m synapdrive_ai --lsl --lsl-name "MyEEGStream" --lsl-seconds 2 --no-delay
Repo map

synapdrive_ai/pipeline.py — canonical wiring (supports deterministic --no-delay)

synapdrive_ai/bci/intent_generator.py — conservative text → intent packet

synapdrive_ai/bci/signal_simulator.py — synthetic EEG-like signals

synapdrive_ai/agi/core_reasoning.py — RMS-based confidence from signal energy

synapdrive_ai/agi/cognitive_optimizer.py — memory + vision context injection

synapdrive_ai/safety/safety_guard.py — safety gating

synapdrive_ai/action/decision_router.py — normalized result packets

synapdrive_ai/control/actuation_engine.py — simulated actuation + telemetry schema

synapdrive_ai/replay/recording.py — JSONL record/replay utilities

synapdrive_ai/interface/web_dashboard.py — Flask dashboard

synapdrive_ai/tests/ — contract tests (pipeline shape, telemetry keys, dashboard API)

examples/ — reviewer quickcheck + golden runs generator

docs/ — architecture + safety model writeups

Reviewer validation pack

examples/REVIEWER_QUICKCHECK.md (2–5 minute checklist)

examples/generate_golden_runs.py → examples/golden_runs.jsonl

Generate & replay:

python examples/generate_golden_runs.py --out examples/golden_runs.jsonl
python -m synapdrive_ai --replay examples/golden_runs.jsonl
Safety stance (explicit)

Unknown or low-confidence intents are blocked

Stable response shapes (no crashing on drift)

Telemetry schema is a contract (UI/tests depend on it)

Non-goals:

clinical diagnosis

medical-device claims

real-world safety certification for actuation

License

Apache-2.0 (see LICENSE)

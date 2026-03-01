# SynapDrive-AI

**SynapDrive-AI** is a **simulation-first** prototype of an **intent → safety → actuation** control pipeline inspired by BCI/autonomy workflows.

This repo **does not** claim medical/clinical functionality. It is intentionally built to be runnable on any machine without hardware:
- **Text pathway** = “decoded intent” (what a BCI decoder *could* output)
- **Signal pathway** = simulated EEG-like waveforms + label-driven reasoning

---

## What you can do with it (today)

- Run a full end-to-end loop: **intent → context → safety gate → actuation → evaluation**
- Verify safety gating blocks low-confidence actions
- View stable telemetry logs (intended for dashboards/tests)
- Extend it with real adapters later (robotics, vehicles, BCI devices)

---

## Architecture (canonical pipeline)

```mermaid
flowchart LR
  A[Input: decoded text OR simulated signal] --> B[Intent decode / reasoning]
  B --> C[Optimizer: memory + vision context]
  C --> D[SafetyGuard]
  D -->|safe| E[DecisionRouter]
  D -->|blocked| X[Blocked result]
  E --> F[ActuationEngine (simulated)]
  F --> G[EpisodicMemory]
  F --> H[MetaEvaluator]
  G --> C


Single source of truth wiring: synapdrive_ai/pipeline.py

Quickstart
1) Install
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

2) Run one cycle (decoded intent text)
python -m synapdrive_ai --text "move left" --image road
python -m synapdrive_ai --text "stop" --image hazard

3) Run one cycle (simulated signal label)
python -m synapdrive_ai --signal walk --count 3 --interval 1
python -m synapdrive_ai --signal stop

4) Run tests
pytest -q

Repo map (what matters)

synapdrive_ai/pipeline.py
Canonical end-to-end pipeline.

synapdrive_ai/bci/signal_simulator.py
Generates EEG-like synthetic waveforms.

synapdrive_ai/agi/core_reasoning.py
Label + waveform → structured intent packet (uses RMS energy for confidence).

synapdrive_ai/agi/cognitive_optimizer.py
Injects memory + vision context into intent.

synapdrive_ai/safety/safety_guard.py
Blocks low-confidence or suspicious actions.

synapdrive_ai/action/decision_router.py
Normalizes results and routes to actuation.

synapdrive_ai/control/actuation_engine.py
Simulated actuator + telemetry log schema.

synapdrive_ai/tests/
Contract tests enforcing stable output + telemetry.

Safety stance

This project enforces a conservative safety default:

Unknown / low-confidence intents are blocked

Telemetry schema is treated as a contract (dashboard/tests depend on it)

Roadmap (credible next steps)

Add optional integration adapters (not enabled by default):

BrainFlow input stream (device or replay)

MNE-based feature extraction for offline datasets

LSL (Lab Streaming Layer) bridge for research setups

Add real actuator adapters:

ROS2 topic publisher

MAVLink command emitter

Game/Sim environment interface

License

Apache-2.0 (see LICENSE)

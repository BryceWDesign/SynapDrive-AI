# Architecture (SynapDrive-AI)

## Purpose
SynapDrive-AI is a **simulation-first** reference implementation of an intent-to-action pipeline:
input → decode/intent → context optimization → safety gate → actuation → evaluation → memory.

## Canonical wiring
The single source of truth is:
- `synapdrive_ai/pipeline.py`

## Data contracts
### Intent packet (minimum)
- `intent: str`
- `confidence: float (0..1)`
- `source: str`
- `memory_context: list`

### Result packet (normalized)
Produced by `DecisionRouter.route()`:
- `status: "success" | "failed"`
- `intent: str`
- `confidence: float`
- `duration: float`
- `raw_status: str`

### Telemetry log entry (contract)
Produced by `ActuationEngine`:
- `timestamp`
- `intent`
- `confidence`
- `status`
- `duration`
- `source`
- `memory`
- `memory_context`

## Extensibility
Integrations are intentionally optional:
- `synapdrive_ai/integrations/brainflow_adapter.py` (BrainFlow)
- `synapdrive_ai/integrations/lsl_adapter.py` (pylsl / LSL)

They both output an intent packet and then call the canonical pipeline.

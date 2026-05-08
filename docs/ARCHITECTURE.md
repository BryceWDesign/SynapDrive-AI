# Architecture (SynapDrive-AI)

## Purpose
SynapDrive-AI is a **simulation-first** reference implementation of an intent-to-action pipeline:
input → decode/intent → context optimization → safety gate → actuation → evaluation → assurance receipt → memory.

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

### Assurance receipt (contract)
Produced by `AssuranceMonitor` for every pipeline cycle:
- `schema: "synapdrive.assurance.v1"`
- `receipt_id`
- `cycle_index`
- `intent`
- `confidence`
- `safety_allowed`
- `safety_reason`
- `result_status`
- `evaluation_score`
- `passed`
- `issues`

### Assurance health report (contract)
Produced by `SynapDrivePipeline.get_assurance_report()`:
- `schema: "synapdrive.assurance.health.v1"`
- `total_cycles`
- `passed_receipts`
- `failed_receipts`
- `blocked_cycles`
- `executed_cycles`
- `average_confidence`
- `average_evaluation_score`
- `latest_receipt_id`

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

## Runtime assurance
The assurance layer is intentionally observational. It does not execute actions,
approve unsafe inputs, or certify hardware behavior. Its job is to catch internal
contract drift, especially cases where a blocked intent somehow reaches actuation
or an allowed cycle returns a blocked result.

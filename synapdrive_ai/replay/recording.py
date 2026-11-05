from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, Optional


def _utc_epoch_s() -> float:
    return time.time()


@dataclass(frozen=True)
class ReplayRecord:
    """
    A single JSONL record of a pipeline cycle.

    We store:
      - raw input (text/label/integration)
      - the *input intent_packet* (pre-optimizer)
      - optional image_label
      - a light output summary (status + key fields)
    """

    schema: str
    created_utc_epoch_s: float
    mode: str
    raw_input: Dict[str, Any]
    image_label: Optional[str]
    intent_packet: Dict[str, Any]
    output_summary: Dict[str, Any]
    capsule: Dict[str, Any] | None = None


class JsonlRecorder:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: ReplayRecord) -> None:
        payload = {
            "schema": record.schema,
            "created_utc_epoch_s": record.created_utc_epoch_s,
            "mode": record.mode,
            "raw_input": record.raw_input,
            "image_label": record.image_label,
            "intent_packet": record.intent_packet,
            "output_summary": record.output_summary,
            "capsule": record.capsule,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False, allow_nan=False) + "\n")


def make_record(
    *,
    mode: str,
    raw_input: Dict[str, Any],
    image_label: Optional[str],
    intent_packet: Dict[str, Any],
    pipeline_output: Dict[str, Any],
) -> ReplayRecord:
    # Keep summary small & stable (don’t store timestamps/durations that are inherently variable)
    result = pipeline_output.get("result", {}) or {}
    intent = pipeline_output.get("intent", {}) or {}

    assurance = pipeline_output.get("assurance", {}) or {}
    summary = {
        "status": pipeline_output.get("status"),
        "intent": intent.get("intent"),
        "confidence": intent.get("confidence"),
        "result_status": result.get("status"),
        "result_intent": result.get("intent"),
        "assurance_passed": assurance.get("passed"),
        "assurance_receipt_id": assurance.get("receipt_id"),
    }

    return ReplayRecord(
        schema="synapdrive.replay.v2",
        created_utc_epoch_s=_utc_epoch_s(),
        mode=mode,
        raw_input=raw_input,
        image_label=image_label,
        intent_packet=intent_packet,
        output_summary=summary,
        capsule=pipeline_output.get("replay_context"),
    )


def iter_jsonl(path: str | Path) -> Iterator[Dict[str, Any]]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def replay_capsule(capsule: Dict[str, Any]) -> Dict[str, Any]:
    """Restore the decision context and fail on unexplained behavioral divergence."""
    from synapdrive_ai.cognition.world_model import ActionModel, WorldModel
    from synapdrive_ai.governance.permission import PermissionGate
    from synapdrive_ai.governance.policy import RuntimePolicy
    from synapdrive_ai.pipeline import SynapDrivePipeline
    from synapdrive_ai.runtime.governed_runtime import GovernedRuntime

    if capsule.get("schema") != "synapdrive.capsule.v2":
        raise ValueError("unsupported or incomplete run capsule")
    if not capsule.get("replay_supported", True):
        raise ValueError("custom endpoint/fallback cannot be reconstructed by this replay schema")
    caps = capsule["capabilities"]
    gate = PermissionGate(caps["allow"], caps["deny"])
    gate._revoked, gate.version = caps["revoked"], caps["version"]
    world = WorldModel(capsule["world_state"])
    world.register_many(ActionModel(**a) for a in capsule["actions"])
    runtime = GovernedRuntime(RuntimePolicy(**capsule["policy"]), gate, world)
    pipe = SynapDrivePipeline(False, runtime)
    if capsule.get("lexical_guard"):
        pipe.guard.min_confidence_threshold = capsule["lexical_guard"]["min_confidence"]
        pipe.guard.risk_keywords = list(capsule["lexical_guard"]["risk_keywords"])
    if capsule.get("simulation_state") is not None:
        from synapdrive_ai.simulation import Plant, PlantEndpoint

        plant = Plant(**capsule["simulation_state"])
        pipe.router = PlantEndpoint(plant)
        pipe.fallback_controller = plant.fallback
    if capsule["stopped"]:
        pipe.dispatch.veto()
    if capsule["unresolved"]:
        pipe.dispatch.journal.prepare("replayed-unresolved", {})
    out = pipe.run_intent_packet(capsule["packet"], capsule["image_label"], capsule["feedback"])
    if out["replay_context"]["expected"] != capsule["expected"]:
        raise ValueError("replay divergence")
    return out

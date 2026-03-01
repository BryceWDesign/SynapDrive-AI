from __future__ import annotations

from typing import Any, Dict

from synapdrive_ai.control.actuation_engine import ActuationEngine


class DecisionRouter:
    """
    Routes optimized, safety-approved intent packets to an execution backend.

    simulate_delay=False is used for replay/tests (reproducible, no sleep).
    """

    def __init__(self, simulate_delay: bool = True) -> None:
        self.actuator = ActuationEngine(simulate_delay=simulate_delay)

    def route(self, intent_packet: Dict[str, Any]) -> Dict[str, Any]:
        result = self.actuator.execute_intent(intent_packet)

        status_raw = (result or {}).get("status", "failed")
        status = "success" if status_raw in {"executed", "success"} else "failed"

        return {
            "status": status,
            "intent": result.get("intent", intent_packet.get("intent", "unknown")),
            "confidence": float(result.get("confidence", intent_packet.get("confidence", 0.0))),
            "duration": float(result.get("duration", 0.0)),
            "raw_status": status_raw,
        }

    def get_action_log(self):
        return self.actuator.get_action_log()

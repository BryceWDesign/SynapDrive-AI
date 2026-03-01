# synapdrive_ai/action/decision_router.py

from __future__ import annotations

from typing import Dict, Any

from synapdrive_ai.control.actuation_engine import ActuationEngine


class DecisionRouter:
    """
    Routes optimized, safety-approved intent packets to an execution backend.

    Today this is a simulated actuation layer (ActuationEngine).
    Tomorrow this can be swapped for robotics/vehicle/autonomy adapters.
    """

    def __init__(self) -> None:
        self.actuator = ActuationEngine()

    def route(self, intent_packet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an intent packet via the actuator and normalize output for downstream modules.

        Ensures returned structure includes:
          - status ("success" | "failed")
          - duration
          - intent
          - confidence
        """
        result = self.actuator.execute_intent(intent_packet)

        # Normalize status to what MetaEvaluator expects ("success")
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
        """Expose underlying action log for dashboards/tests."""
        return self.actuator.get_action_log()

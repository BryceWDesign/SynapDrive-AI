"""
Legacy executor bridge for the top-level core intent-router example.

The package under synapdrive_ai is the canonical runtime. This bridge keeps the
older core example importable and deterministic instead of leaving a broken module
reference behind.
"""

from __future__ import annotations

from typing import Dict, List


class ExecutorBridge:
    """Small deterministic executor used by legacy core examples."""

    def __init__(self) -> None:
        self.execution_log: List[Dict[str, object]] = []

    def execute(self, intent_type: str, params: Dict[str, object]) -> str:
        normalized_intent = (intent_type or "unknown").strip().lower()
        normalized_params = dict(params or {})

        if normalized_intent == "move":
            direction = str(normalized_params.get("direction", "unknown"))
            message = f"Executed simulated move: {direction}"
        elif normalized_intent == "stop":
            message = "Executed simulated stop: all motion halted"
        elif normalized_intent == "pick_up":
            message = "Executed simulated pick-up"
        elif normalized_intent == "drop":
            message = "Executed simulated drop"
        else:
            message = f"No direct executor route for intent: {normalized_intent}"

        self.execution_log.append(
            {
                "intent": normalized_intent,
                "params": normalized_params,
                "message": message,
            }
        )
        return message

    def get_execution_log(self) -> List[Dict[str, object]]:
        return list(self.execution_log)

"""Legacy intent router retained for backward compatibility."""

from __future__ import annotations

from typing import Dict, Optional

from core.execution.executor_bridge import ExecutorBridge
from core.planning.agi_planner import DeterministicPlanner


class IntentRouter:
    """Route parsed legacy intents to deterministic simulation or plan templates."""

    def __init__(self, use_realtime: bool = False):
        # ``use_realtime`` is historical naming. The executor is still simulation-only.
        self.use_realtime = bool(use_realtime)
        self.planner = DeterministicPlanner()
        self.executor = ExecutorBridge()

    def route(self, intent: Dict) -> Optional[str]:
        if not intent or "intent" not in intent:
            return "Invalid intent format"

        intent_type = str(intent["intent"])
        params = dict(intent.get("params", {}))
        if self.use_realtime or intent_type in {"move", "stop", "pick_up", "drop"}:
            return self.executor.execute(intent_type, params)
        return self.planner.plan(intent_type, params)

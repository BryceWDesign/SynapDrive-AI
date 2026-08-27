from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from synapdrive_ai.runtime.contracts import PreActionDecision


@dataclass(frozen=True)
class SimplexExecution:
    controller: str
    result: Dict[str, Any]


class SimplexController:
    """Routes to advanced control only after the runtime monitor admits the action."""

    def __init__(
        self,
        advanced_controller: Callable[[Dict[str, Any]], Dict[str, Any]],
        safe_controller: Callable[[str], Dict[str, Any]],
    ) -> None:
        self.advanced_controller = advanced_controller
        self.safe_controller = safe_controller

    def execute(self, packet: Dict[str, Any], decision: PreActionDecision) -> SimplexExecution:
        if decision.allowed:
            return SimplexExecution("advanced", self.advanced_controller(packet))
        return SimplexExecution("reversionary", self.safe_controller(decision.fallback_action))

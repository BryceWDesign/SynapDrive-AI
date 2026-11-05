from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from synapdrive_ai.runtime.contracts import PreActionDecision
from synapdrive_ai.runtime.dispatch import DispatchGate
from synapdrive_ai.runtime.governed_runtime import GovernedRuntime


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
        runtime: GovernedRuntime | None = None,
    ) -> None:
        self.runtime = runtime
        self.dispatch = DispatchGate()
        self.advanced_controller = advanced_controller
        self.safe_controller = safe_controller

    def execute(self, packet: Dict[str, Any], decision: PreActionDecision) -> SimplexExecution:
        if (
            self.runtime is not None
            and decision.allowed
            and packet.get("intent") == decision.action
        ):
            current = self.runtime.assess(packet)
            if current.allowed:
                gate = self.runtime.permissions
                caps = {
                    "version": gate.version,
                    "allow": gate.allow_patterns,
                    "deny": gate.deny_patterns,
                    "revoked": gate._revoked,
                }
                policy = self.runtime.policy.to_dict()
                state = self.runtime.world_model.state
                permit = self.dispatch.issue(packet, state, policy, caps)
                result = self.dispatch.execute(
                    permit, packet, state, policy, caps, self.advanced_controller
                )
                return SimplexExecution("advanced", result)
        return SimplexExecution("reversionary", self.safe_controller(decision.fallback_action))

"""Legacy deterministic planning compatibility surface.

The historical module name is retained for import compatibility. No AGI, learned model,
or predictive planner is implemented here. Plans are deterministic templates over parsed,
caller-declared intents.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class PlanStep:
    action: str
    parameters: Dict[str, str]


class DeterministicPlanner:
    """Create explicit, inspectable plan templates for legacy high-level intents."""

    def __init__(self) -> None:
        self.reasoning_memory: List[Dict[str, object]] = []

    def plan(self, intent: str, params: Dict) -> str:
        normalized = (intent or "unknown").strip().lower()
        normalized_params = {str(k): str(v) for k, v in dict(params or {}).items()}
        self.reasoning_memory.append({"intent": normalized, "params": normalized_params})

        if normalized == "navigate":
            destination = normalized_params.get("location")
            if not destination:
                return "Plan rejected: navigate requires a declared location"
            steps = [
                PlanStep("verify_destination", {"location": destination}),
                PlanStep("request_path_provider", {"location": destination}),
                PlanStep("hold_until_path_validated", {}),
            ]
            return self._serialize(steps)
        if normalized == "analyze":
            target = normalized_params.get("target")
            if not target:
                return "Plan rejected: analyze requires a declared target"
            return self._serialize(
                [
                    PlanStep("select_available_observation", {"target": target}),
                    PlanStep("compute_declared_metrics", {"target": target}),
                    PlanStep("record_evidence", {"target": target}),
                ]
            )
        if normalized == "assist":
            subject = normalized_params.get("subject")
            if not subject:
                return "Plan rejected: assist requires a declared subject"
            return self._serialize(
                [
                    PlanStep("request_operator_instruction", {"subject": subject}),
                    PlanStep("await_authorized_action", {"subject": subject}),
                ]
            )
        return f"Unknown intent: {normalized}"

    @staticmethod
    def _serialize(steps: List[PlanStep]) -> str:
        body = "; ".join(
            f"{step.action}({','.join(f'{k}={v}' for k, v in sorted(step.parameters.items()))})"
            for step in steps
        )
        return f"Plan: {body}"


class AGIPlanner(DeterministicPlanner):
    """Deprecated compatibility name for :class:`DeterministicPlanner`."""

from __future__ import annotations

from typing import Any, Mapping

from synapdrive_ai.cognition.world_model import WorldModel, default_simulation_world_model
from synapdrive_ai.governance.permission import PermissionGate
from synapdrive_ai.governance.policy import RuntimePolicy
from synapdrive_ai.neuro.uncertainty import estimate_uncertainty, packet_distribution
from synapdrive_ai.runtime.contracts import PreActionDecision, RuntimeAssessment


class GovernedRuntime:
    """Fail-closed pre-action arbiter for provenance, uncertainty, quality and risk."""

    def __init__(
        self,
        policy: RuntimePolicy | None = None,
        permission_gate: PermissionGate | None = None,
        world_model: WorldModel | None = None,
    ) -> None:
        self.policy = policy or RuntimePolicy()
        self.permissions = permission_gate or PermissionGate()
        self.world_model = world_model or default_simulation_world_model()

    def assess(self, packet: Mapping[str, Any]) -> PreActionDecision:
        action = str(packet.get("intent") or "unknown")
        confidence = max(0.0, min(1.0, float(packet.get("confidence", 0.0))))
        requested_min_confidence = max(
            self.policy.min_confidence,
            max(0.0, float(packet.get("required_confidence", 0.0))),
        )
        uncertainty = packet.get("uncertainty")
        if uncertainty is None:
            uncertainty = estimate_uncertainty(packet_distribution(packet)).combined
        uncertainty = max(0.0, min(1.0, float(uncertainty)))
        quality = max(0.0, min(1.0, float(packet.get("signal_quality", 1.0))))
        drift_score = max(0.0, float(packet.get("drift_score", 0.0)))
        permission = self.permissions.evaluate(action)
        prediction = self.world_model.predict(action)
        predicted_risk = max(float(packet.get("predicted_risk", 0.0)), prediction.predicted_risk)

        issues: list[str] = []
        if bool(packet.get("analysis_only", False)):
            issues.append("analysis-only-inference")
        if action == "unknown":
            issues.append("unknown-intent")
        if confidence < requested_min_confidence:
            issues.append("confidence-below-policy")
        if uncertainty > self.policy.max_uncertainty:
            issues.append("uncertainty-above-policy")
        if quality < self.policy.min_signal_quality:
            issues.append("signal-quality-below-policy")
        if predicted_risk > self.policy.max_predicted_risk:
            issues.append("predicted-risk-above-policy")
        if drift_score > self.policy.max_drift_score:
            issues.append("decoder-drift-above-policy")
        if not permission.allowed:
            issues.append("permission-denied")
        if not prediction.feasible:
            issues.append("world-model-precondition-failed")

        # Stable ordering with no duplicate issue labels keeps replay evidence deterministic.
        issues = list(dict.fromkeys(issues))
        assessment = RuntimeAssessment(
            round(confidence, 6),
            round(requested_min_confidence, 6),
            round(uncertainty, 6),
            round(quality, 6),
            round(predicted_risk, 6),
            permission.allowed,
            round(drift_score, 6),
            tuple(issues),
        )
        allowed = not issues
        reason = "runtime policy passed" if allowed else "; ".join(issues)
        return PreActionDecision(
            action,
            allowed,
            reason,
            self.policy.safe_fallback_action,
            assessment,
        )

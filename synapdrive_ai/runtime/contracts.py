from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class RuntimeAssessment:
    confidence: float
    required_confidence: float
    uncertainty: float
    signal_quality: float
    predicted_risk: float
    permission_allowed: bool
    drift_score: float = 0.0
    issues: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def admissible(self) -> bool:
        return not self.issues

    def to_dict(self) -> Dict[str, Any]:
        return {
            "confidence": self.confidence,
            "required_confidence": self.required_confidence,
            "uncertainty": self.uncertainty,
            "signal_quality": self.signal_quality,
            "predicted_risk": self.predicted_risk,
            "permission_allowed": self.permission_allowed,
            "drift_score": self.drift_score,
            "admissible": self.admissible,
            "issues": list(self.issues),
        }


@dataclass(frozen=True)
class PreActionDecision:
    action: str
    allowed: bool
    reason: str
    fallback_action: str
    assessment: RuntimeAssessment

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "allowed": self.allowed,
            "reason": self.reason,
            "fallback_action": self.fallback_action,
            "assessment": self.assessment.to_dict(),
        }


@dataclass(frozen=True)
class RealityVerdict:
    aligned: bool
    outcome: str
    reason: str
    prediction_error: float
    user_error_probability: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "aligned": self.aligned,
            "outcome": self.outcome,
            "reason": self.reason,
            "prediction_error": self.prediction_error,
            "user_error_probability": self.user_error_probability,
        }

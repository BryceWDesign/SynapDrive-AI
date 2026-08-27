from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class RuntimePolicy:
    """Fail-closed limits for the simulation runtime.

    These are software policy limits, not medical or hardware safety limits.
    """

    min_confidence: float = 0.45
    max_uncertainty: float = 0.70
    min_signal_quality: float = 0.60
    max_predicted_risk: float = 0.70
    max_drift_score: float = 6.0
    errp_contradiction_threshold: float = 0.70
    safe_fallback_action: str = "hold_position"

    def __post_init__(self) -> None:
        bounded = (
            ("min_confidence", self.min_confidence),
            ("max_uncertainty", self.max_uncertainty),
            ("min_signal_quality", self.min_signal_quality),
            ("max_predicted_risk", self.max_predicted_risk),
            ("errp_contradiction_threshold", self.errp_contradiction_threshold),
        )
        for name, value in bounded:
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        if self.max_drift_score <= 0:
            raise ValueError("max_drift_score must be > 0")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, path: str | Path) -> "RuntimePolicy":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("policy JSON must contain an object")
        return cls(**payload)

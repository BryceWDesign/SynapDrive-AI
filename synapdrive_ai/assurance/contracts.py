from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional, Tuple

ASSURANCE_SCHEMA = "synapdrive.assurance.v1"


def utc_epoch_s() -> float:
    return time.time()


def normalize_confidence(value: Any) -> float:
    """Normalize confidence into the closed interval [0.0, 1.0]."""
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, confidence))


def normalize_score(value: Any) -> float:
    """Normalize evaluation scores while preserving scores above 1.0."""
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, score)


def stable_receipt_id(payload: Dict[str, Any]) -> str:
    """
    Build a deterministic short receipt id from stable cycle fields.

    Timestamps are intentionally excluded by callers so replayed cycles can be compared.
    """
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class AssuranceReceipt:
    """
    Reviewable evidence for one SynapDrive control cycle.

    A receipt does not certify real-world safety. It records whether the simulated pipeline
    kept its own invariants: decoded intent, safety decision, actuation result, and
    evaluation all agree on one normalized outcome.
    """

    receipt_id: str
    cycle_index: int
    created_utc_epoch_s: float
    intent: str
    confidence: float
    source: str
    image_label: Optional[str]
    safety_allowed: bool
    safety_reason: str
    result_status: str
    evaluation_score: float
    issues: Tuple[str, ...] = field(default_factory=tuple)
    schema: str = ASSURANCE_SCHEMA

    @property
    def passed(self) -> bool:
        return not self.issues

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": self.schema,
            "receipt_id": self.receipt_id,
            "cycle_index": self.cycle_index,
            "created_utc_epoch_s": self.created_utc_epoch_s,
            "intent": self.intent,
            "confidence": self.confidence,
            "source": self.source,
            "image_label": self.image_label,
            "safety_allowed": self.safety_allowed,
            "safety_reason": self.safety_reason,
            "result_status": self.result_status,
            "evaluation_score": self.evaluation_score,
            "passed": self.passed,
            "issues": list(self.issues),
        }


def build_receipt(
    *,
    cycle_index: int,
    intent_packet: Dict[str, Any],
    image_label: Optional[str],
    safety_allowed: bool,
    safety_reason: str,
    result_status: str,
    evaluation_score: Any,
    issues: Iterable[str],
) -> AssuranceReceipt:
    intent = str(intent_packet.get("intent") or "unknown")
    confidence = normalize_confidence(intent_packet.get("confidence", 0.0))
    source = str(intent_packet.get("source") or "unknown")
    normalized_score = normalize_score(evaluation_score)
    issue_tuple = tuple(dict.fromkeys(str(issue) for issue in issues if issue))

    stable_payload = {
        "cycle_index": cycle_index,
        "intent": intent,
        "confidence": confidence,
        "source": source,
        "image_label": image_label,
        "safety_allowed": bool(safety_allowed),
        "safety_reason": safety_reason,
        "result_status": result_status,
        "evaluation_score": normalized_score,
        "issues": list(issue_tuple),
    }

    return AssuranceReceipt(
        receipt_id=stable_receipt_id(stable_payload),
        cycle_index=cycle_index,
        created_utc_epoch_s=utc_epoch_s(),
        intent=intent,
        confidence=confidence,
        source=source,
        image_label=image_label,
        safety_allowed=bool(safety_allowed),
        safety_reason=str(safety_reason or ""),
        result_status=str(result_status or "unknown"),
        evaluation_score=normalized_score,
        issues=issue_tuple,
    )

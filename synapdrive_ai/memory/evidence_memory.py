from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Literal

MemoryState = Literal["validated", "quarantined"]


@dataclass(frozen=True)
class EvidenceMemoryRecord:
    timestamp: float
    cycle_id: str
    intent: str
    confidence: float
    outcome: str
    state: MemoryState
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EvidenceMemory:
    """Outcome-bound memory that refuses to reinforce contradicted cycles."""

    def __init__(self) -> None:
        self._records: List[EvidenceMemoryRecord] = []

    def record(
        self,
        *,
        cycle_id: str,
        intent: str,
        confidence: float,
        outcome: str,
        aligned: bool,
        reason: str,
    ) -> EvidenceMemoryRecord:
        record = EvidenceMemoryRecord(
            timestamp=time.time(),
            cycle_id=cycle_id,
            intent=intent,
            confidence=max(0.0, min(1.0, float(confidence))),
            outcome=outcome,
            state="validated" if aligned else "quarantined",
            reason=reason,
        )
        self._records.append(record)
        return record

    def validated_for_intent(self, intent: str) -> List[EvidenceMemoryRecord]:
        return [r for r in self._records if r.intent == intent and r.state == "validated"]

    def quarantined(self) -> List[EvidenceMemoryRecord]:
        return [r for r in self._records if r.state == "quarantined"]

    def all(self) -> List[EvidenceMemoryRecord]:
        return list(self._records)

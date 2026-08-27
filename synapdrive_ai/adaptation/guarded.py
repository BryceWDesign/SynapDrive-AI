from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class AdaptationDecision:
    promoted: bool
    old_threshold: float
    candidate_threshold: float
    old_utility: float
    candidate_utility: float
    old_unsafe_accepts: int
    candidate_unsafe_accepts: int
    reason: str


class GuardedThresholdAdapter:
    def __init__(self, threshold: float = 0.45) -> None:
        self.threshold = float(threshold)

    @staticmethod
    def _numeric_field(row: Mapping[str, object], key: str) -> float:
        value = row.get(key)
        if isinstance(value, (int, float, str)):
            return float(value)
        raise TypeError(f"{key} must be numeric")

    @staticmethod
    def _score(records: Iterable[Mapping[str, object]], threshold: float) -> tuple[float, int]:
        tp = tn = fp = fn = 0
        for row in records:
            conf = GuardedThresholdAdapter._numeric_field(row, "confidence")
            safe = bool(row["safe"])
            accepted = conf >= threshold
            if accepted and safe:
                tp += 1
            elif not accepted and not safe:
                tn += 1
            elif accepted and not safe:
                fp += 1
            else:
                fn += 1
        total = tp + tn + fp + fn
        utility = (tp + tn - 3 * fp - 0.5 * fn) / max(total, 1)
        return utility, fp

    def evaluate_candidate(
        self,
        candidate_threshold: float,
        validation_records: Iterable[Mapping[str, object]],
    ) -> AdaptationDecision:
        rows = list(validation_records)
        if not rows:
            raise ValueError("validation_records must not be empty")
        candidate_threshold = max(0.0, min(1.0, float(candidate_threshold)))
        old_utility, old_unsafe = self._score(rows, self.threshold)
        new_utility, new_unsafe = self._score(rows, candidate_threshold)
        promoted = new_unsafe <= old_unsafe and new_utility > old_utility
        reason = (
            "candidate improves held-out utility without increasing unsafe accepts"
            if promoted
            else "candidate rejected: no safe held-out improvement"
        )
        old = self.threshold
        if promoted:
            self.threshold = candidate_threshold
        return AdaptationDecision(
            promoted,
            old,
            candidate_threshold,
            round(old_utility, 6),
            round(new_utility, 6),
            old_unsafe,
            new_unsafe,
            reason,
        )

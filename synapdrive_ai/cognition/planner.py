from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Tuple

from synapdrive_ai.cognition.world_model import Prediction, WorldModel


@dataclass(frozen=True)
class CandidateAction:
    action: str
    intent_alignment: float
    confidence: float


@dataclass(frozen=True)
class RankedCandidate:
    action: str
    utility: float
    goal_score: float
    predicted_risk: float
    reversible: bool
    feasible: bool


@dataclass(frozen=True)
class PlanChoice:
    selected: RankedCandidate | None
    ranked: Tuple[RankedCandidate, ...]


class CounterfactualPlanner:
    """Ranks candidate actions against explicit predicted state and a caller goal function."""

    def __init__(self, world_model: WorldModel) -> None:
        self.world_model = world_model

    def rank(
        self,
        candidates: Iterable[CandidateAction],
        goal: Callable[[Dict[str, object]], float],
    ) -> PlanChoice:
        ranked = []
        for candidate in candidates:
            prediction: Prediction = self.world_model.predict(candidate.action)
            goal_score = (
                float(max(0.0, min(1.0, goal(prediction.after))))
                if prediction.feasible
                else 0.0
            )
            utility = (
                0.35 * max(0.0, min(1.0, candidate.intent_alignment))
                + 0.25 * max(0.0, min(1.0, candidate.confidence))
                + 0.30 * goal_score
                + 0.05 * (1.0 if prediction.reversible else 0.0)
                - 0.35 * prediction.predicted_risk
            )
            ranked.append(
                RankedCandidate(
                    candidate.action,
                    round(utility, 6),
                    round(goal_score, 6),
                    prediction.predicted_risk,
                    prediction.reversible,
                    prediction.feasible,
                )
            )
        ranked.sort(key=lambda item: item.utility, reverse=True)
        selected = next((item for item in ranked if item.feasible), None)
        return PlanChoice(selected, tuple(ranked))

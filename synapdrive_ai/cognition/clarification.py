"""Bounded proposal of common reversible progress across caller-supplied goals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from synapdrive_ai.cognition.world_model import WorldModel


@dataclass(frozen=True)
class ProgressProposal:
    kind: str
    action: str | None
    retained_goals: tuple[str, ...]
    reason: str


def propose_progress(
    world: WorldModel,
    goals: dict[str, Callable],
    candidates: list[str],
    *,
    max_risk=0.20,
    assisted=False,
):
    if not goals or len(goals) > 8 or len(candidates) > 32:
        raise ValueError("goals or candidates exceed bounded planning budget")
    retained = tuple(goals)
    if not assisted:
        return ProgressProposal("clarify", None, retained, "manual mode requires clarification")
    common = []
    for action in candidates:
        prediction = world.predict(action)
        if (
            not prediction.feasible
            or not prediction.reversible
            or prediction.predicted_risk > max_risk
        ):
            continue
        scores = [goal(prediction.after) for goal in goals.values()]
        if all(isinstance(score, (int, float)) and 0 < score <= 1 for score in scores):
            common.append((min(scores), action))
    if not common:
        return ProgressProposal(
            "clarify", None, retained, "no reversible progress supports every goal"
        )
    action = max(common)[1]
    return ProgressProposal(
        "propose",
        action,
        retained,
        "common progress proposal; execution still requires canonical admission",
    )

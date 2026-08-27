from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Tuple

from synapdrive_ai.cognition.planner import CandidateAction, CounterfactualPlanner, RankedCandidate


@dataclass(frozen=True)
class SharedAutonomyProposal:
    user_intent: str
    selected_action: str | None
    preserved_user_goal: bool
    ranked: Tuple[RankedCandidate, ...]


class SharedAutonomyArbiter:
    """Selects among bounded actions without silently rewriting the user's intent.

    Machine candidates must be explicitly supplied by the caller and scored against the same
    goal function. The user's requested action is always represented as a candidate.
    """

    def __init__(self, planner: CounterfactualPlanner) -> None:
        self.planner = planner

    def propose(
        self,
        *,
        user_intent: str,
        user_confidence: float,
        machine_candidates: Iterable[CandidateAction],
        goal: Callable[[Dict[str, object]], float],
    ) -> SharedAutonomyProposal:
        candidates = [CandidateAction(user_intent, 1.0, user_confidence)]
        candidates.extend(machine_candidates)
        choice = self.planner.rank(candidates, goal)
        selected = choice.selected.action if choice.selected else None
        # Goal preservation means selection came from the bounded candidate set under the same
        # goal evaluator. It does not mean the action equals the user's low-level command.
        return SharedAutonomyProposal(
            user_intent=user_intent,
            selected_action=selected,
            preserved_user_goal=selected is not None,
            ranked=choice.ranked,
        )

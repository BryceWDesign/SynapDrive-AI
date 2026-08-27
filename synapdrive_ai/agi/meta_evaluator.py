from __future__ import annotations

import statistics


class MetaEvaluator:
    """Small deterministic diagnostic score for simulation traces.

    The score is not a measure of intelligence, BCI accuracy, or real-world safety. It is
    retained as a compact regression signal for the historical pipeline surface.
    """

    def __init__(self) -> None:
        self.scores: list[float] = []

    def evaluate(self, intent_packet, result_packet):
        score = 0.0
        if result_packet["status"] == "success":
            score += 1.0
        if float(intent_packet.get("confidence", 0.0)) > 0.8:
            score += 0.5
        if intent_packet.get("memory_context"):
            score += 0.2

        self.scores.append(score)
        return {
            "score": round(score, 2),
            "score_semantics": "simulation-regression-diagnostic",
            "total_actions": len(self.scores),
            "avg_score": round(statistics.mean(self.scores), 2),
        }

    def reset(self) -> None:
        self.scores.clear()

# synapdrive_ai/agi/meta_evaluator.py

import statistics

class MetaEvaluator:
    """
    Scores AGI behavior post-hoc to drive long-term system reliability,
    model tuning, and intelligent self-reflection.
    """

    def __init__(self):
        self.scores = []

    def evaluate(self, intent_packet, result_packet):
        """
        Scores a completed AGI action and appends to the score log.

        Returns:
            dict: Evaluation summary
        """
        score = 0.0
        if result_packet["status"] == "success":
            score += 1.0
        if intent_packet["confidence"] > 0.8:
            score += 0.5
        if "memory_context" in intent_packet and intent_packet["memory_context"]:
            score += 0.2
        if "visual_certainty" in intent_packet and intent_packet["visual_certainty"] > 0.8:
            score += 0.2

        self.scores.append(score)

        return {
            "score": round(score, 2),
            "total_actions": len(self.scores),
            "avg_score": round(statistics.mean(self.scores), 2)
        }

    def reset(self):
        self.scores.clear()

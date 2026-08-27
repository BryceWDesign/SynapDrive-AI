from __future__ import annotations


class FeedbackLearner:
    """Deprecated compatibility logger for historical feedback calls.

    Earlier versions modified intent priorities from execution confidence alone. That is
    not evidence that an adaptation is beneficial, so automatic mutation is disabled.
    Use ``synapdrive_ai.adaptation.GuardedThresholdAdapter`` with held-out labeled records
    for the supported adaptation path.
    """

    def __init__(self, reasoner) -> None:
        self.reasoner = reasoner
        self.feedback_log: list[dict[str, object]] = []

    def apply_feedback(self, intent_packet, result) -> None:
        record = {
            "intent": result.get("intent"),
            "source": intent_packet.get("source"),
            "confidence": float(result.get("confidence", 0.0)),
            "promoted": False,
            "reason": "legacy confidence-only adaptation disabled; use held-out guarded adaptation",
        }
        self.feedback_log.append(record)

    def get_feedback_history(self):
        return list(self.feedback_log)

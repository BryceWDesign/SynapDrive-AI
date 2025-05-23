# synapdrive_ai/agi/feedback_learning.py

class FeedbackLearner:
    """
    Adaptive learner that adjusts AGI intent priorities based on outcomes.

    It simulates reward-based reinforcement by analyzing intent results and
    feeding back into the reasoning system to increase or decrease priority weights.
    """

    def __init__(self, reasoner):
        self.reasoner = reasoner
        self.feedback_log = []

    def apply_feedback(self, intent_packet, result):
        """
        Adjusts internal weights in AGICoreReasoner based on execution results.

        Args:
            intent_packet (dict): The original intent.
            result (dict): {
                'status': 'executed',
                'intent': str,
                'confidence': float,
                'duration': float
            }
        """
        intent = result.get("intent")
        confidence = result.get("confidence", 0.0)
        label = intent_packet.get("source")

        if label not in self.reasoner.intent_weights:
            return

        old_priority = self.reasoner.intent_weights[label]["priority"]

        # Reward if confidence > 0.8, punish if < 0.5
        if confidence > 0.8:
            adjustment = 0.05
        elif confidence < 0.5:
            adjustment = -0.05
        else:
            adjustment = 0.0

        new_priority = min(max(old_priority + adjustment, 0.0), 1.0)
        self.reasoner.intent_weights[label]["priority"] = new_priority

        feedback_record = {
            "intent": intent,
            "source": label,
            "old_priority": old_priority,
            "new_priority": new_priority,
            "confidence": confidence,
            "timestamp": result.get("duration")
        }
        self.feedback_log.append(feedback_record)

    def get_feedback_history(self):
        """Returns a history of all feedback adjustments."""
        return self.feedback_log

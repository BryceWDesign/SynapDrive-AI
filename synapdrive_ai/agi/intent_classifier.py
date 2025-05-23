# synapdrive_ai/agi/intent_classifier.py

import random

class IntentClassifier:
    """
    Lightweight classifier that maps brain signal labels to high-level intent categories.
    Currently rule-based, but supports plug-in of ML models in future.
    """

    def __init__(self):
        self.rules = {
            "think_move": "move_forward",
            "think_stop": "halt",
            "think_turn": "rotate_right",
            "think_grab": "activate_claw"
        }

    def classify(self, signal_data):
        """
        Classify raw signal input into an intent packet.

        Args:
            signal_data (dict): {
                'label': str,
                'signal_strength': float,
                'raw': any
            }

        Returns:
            dict: {
                'intent': str,
                'confidence': float,
                'source': str,
                'memory_context': []
            }
        """
        label = signal_data.get("label")
        intent = self.rules.get(label, "unknown")
        confidence = round(random.uniform(0.6, 0.99), 2) if intent != "unknown" else 0.3

        return {
            "intent": intent,
            "confidence": confidence,
            "source": label,
            "memory_context": []
        }

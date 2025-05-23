# synapdrive_ai/agi/core_reasoning.py

from collections import deque
import numpy as np

class AGICoreReasoner:
    """
    Core cognitive engine that interprets brain signals and emits structured action plans.

    It maintains a short-term memory of recent thought patterns and uses basic
    symbolic inference + transformer-inspired attention weighting for decisions.

    Output: structured intent packets (dicts) that downstream control layers can act on.
    """

    def __init__(self, memory_length=5):
        self.memory = deque(maxlen=memory_length)
        self.intent_weights = {
            "left_arm": {"motor": "move_left_arm", "priority": 0.8},
            "right_arm": {"motor": "move_right_arm", "priority": 0.8},
            "walk": {"motor": "initiate_walk", "priority": 0.9},
            "stop": {"motor": "halt_all_motion", "priority": 1.0},
            "calculate": {"cognitive": "initiate_computation", "priority": 0.7},
            "recall": {"cognitive": "retrieve_memory", "priority": 0.6},
            "explore": {"cognitive": "expand_context", "priority": 0.85}
        }

    def receive_signal(self, label, signal_data):
        """Store signal and trigger reasoning logic."""
        self.memory.append((label, signal_data))
        return self.reason(label, signal_data)

    def reason(self, label, signal_data):
        """Reason over the current label and signal using internal logic."""
        if label not in self.intent_weights:
            return {"intent": "unknown", "confidence": 0.0}
        
        context_signal = np.mean(signal_data)
        intent_data = self.intent_weights[label]
        priority = intent_data["priority"]

        # Confidence modulated by signal intensity and priority
        confidence = min(1.0, max(0.1, np.abs(context_signal) * priority))

        return {
            "intent": intent_data.get("motor") or intent_data.get("cognitive"),
            "source": label,
            "confidence": confidence,
            "memory_context": list(self.memory)
        }

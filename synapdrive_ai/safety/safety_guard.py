# synapdrive_ai/safety/safety_guard.py

class SafetyGuard:
    """
    Ensures cognitive decisions remain within safe, logical, and ethical bounds.
    Rejects unsafe or anomalous intent packets.
    """

    def __init__(self):
        self.blocked_intents = []
        self.risk_keywords = [
            "shutdown all systems", "override security", "disable brakes",
            "release payload", "trigger launch", "eject", "kill process"
        ]
        self.min_confidence_threshold = 0.45

    def evaluate_safety(self, intent_packet):
        """
        Checks if an intent packet is safe to execute.

        Returns:
            tuple (bool, str): (is_safe, reason)
        """
        text = intent_packet.get("intent", "").lower()
        conf = intent_packet.get("confidence", 0.0)

        for risk in self.risk_keywords:
            if risk in text:
                self.blocked_intents.append(intent_packet)
                return (False, f"Intent contains prohibited action: '{risk}'")

        if conf < self.min_confidence_threshold:
            self.blocked_intents.append(intent_packet)
            return (False, f"Intent confidence too low: {conf}")

        return (True, "Intent is safe")

    def get_blocked_log(self):
        return self.blocked_intents

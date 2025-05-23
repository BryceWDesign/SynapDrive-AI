# synapdrive_ai/cloud/cloud_stub.py

import json
import random
from synapdrive_ai.core.logger import SynapLogger

class CloudControlStub:
    """
    Simulates remote cloud communication with external systems like
    Tesla, SpaceX, or Hyperloop infrastructure.
    """

    def __init__(self):
        self.logger = SynapLogger()
        self.transmitted_packets = []

    def transmit_intent(self, intent_packet):
        """
        Pretends to send the intent to a secure remote infrastructure control API.

        Args:
            intent_packet (dict): {
                'intent': str,
                'confidence': float,
                'source': str,
                'memory_context': []
            }
        """
        payload = {
            "system": self.route_system(intent_packet["intent"]),
            "intent": intent_packet["intent"],
            "confidence": intent_packet["confidence"],
            "metadata": {
                "source": intent_packet["source"],
                "timestamp": random.randint(1000000, 9999999)
            }
        }

        self.transmitted_packets.append(payload)
        self.logger.info(f"Transmitted intent to simulated cloud system: {json.dumps(payload)}")

    def route_system(self, intent):
        """
        Simple mapping of intent types to infrastructure targets.
        """
        if "move" in intent or "rotate" in intent:
            return "TeslaAutonomySystem"
        elif "launch" in intent or "sequence" in intent:
            return "SpaceXCommandCore"
        elif "tube" in intent or "velocity" in intent:
            return "HyperloopOps"
        return "GenericCloudController"

    def get_transmissions(self):
        return self.transmitted_packets

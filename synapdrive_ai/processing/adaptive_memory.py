import time
from collections import Counter, deque


class EpisodicMemory:
    """
    Store recent intent records in a bounded queue and report frequency counts.

    Episodic structure:
        {
            'timestamp': float,
            'intent': str,
            'source': str,
            'confidence': float
        }
    """

    def __init__(self, max_memory=100):
        self.memory_bank = deque(maxlen=max_memory)

    def store_event(self, intent_packet):
        """Store an intent record."""
        episode = {
            "timestamp": time.time(),
            "intent": intent_packet.get("intent"),
            "source": intent_packet.get("source"),
            "confidence": intent_packet.get("confidence", 0.0),
        }
        self.memory_bank.append(episode)

    def get_recent_memory(self, n=5):
        """Return the last n episodes."""
        return list(self.memory_bank)[-n:]

    def get_intent_frequencies(self):
        """Return a frequency count of all observed intents."""
        intents = [ep["intent"] for ep in self.memory_bank if ep["intent"]]
        return Counter(intents)

    def get_high_confidence_events(self, threshold=0.8):
        """Return events with confidence above a threshold."""
        return [ep for ep in self.memory_bank if ep["confidence"] >= threshold]

    def forget_oldest(self):
        """Manually forget the oldest memory."""
        if self.memory_bank:
            self.memory_bank.popleft()

    def clear_memory(self):
        """Erase all episodic memory."""
        self.memory_bank.clear()

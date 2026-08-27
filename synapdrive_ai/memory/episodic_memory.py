import time


class EpisodicMemory:
    """Backward-compatible episodic store with outcome-aware recall."""

    def __init__(self):
        self.episodes = []

    def record_episode(self, intent_packet, result_packet):
        episode = {
            "timestamp": time.time(),
            "intent": intent_packet["intent"],
            "confidence": intent_packet["confidence"],
            "source": intent_packet["source"],
            "result": result_packet["status"],
            "duration": result_packet["duration"],
        }
        self.episodes.append(episode)

    def retrieve_recent(self, count=5):
        return self.episodes[-count:]

    def find_by_intent(self, intent_keyword):
        return [ep for ep in self.episodes if intent_keyword in ep["intent"]]

    def find_successful_by_intent(self, intent_keyword):
        return [
            ep
            for ep in self.episodes
            if intent_keyword in ep["intent"] and ep.get("result") in {"success", "executed"}
        ]

    def clear_memory(self):
        self.episodes.clear()

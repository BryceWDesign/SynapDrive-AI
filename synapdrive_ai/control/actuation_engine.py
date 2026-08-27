from __future__ import annotations

import time
from typing import Any, Dict, List


class ActuationEngine:
    """
    Simulated actuation engine that records admitted intent packets as simulated actions.

    Determinism support:
      - simulate_delay=True  -> sleeps to emulate actuation time
      - simulate_delay=False -> no sleep (best for tests/replay)
    """

    def __init__(self, simulate_delay: bool = True) -> None:
        self.simulate_delay = bool(simulate_delay)
        self.action_log: List[Dict[str, Any]] = []

    def execute_intent(self, intent_packet: Dict[str, Any]) -> Dict[str, Any]:
        intent = (intent_packet or {}).get("intent")
        source = (intent_packet or {}).get("source", "unknown")
        confidence = float((intent_packet or {}).get("confidence", 0.0))
        memory_context = (intent_packet or {}).get("memory_context", [])
        memory = (intent_packet or {}).get("memory", memory_context)

        confidence = max(0.0, min(1.0, confidence))

        if not intent:
            result = {
                "timestamp": time.time(),
                "status": "ignored",
                "reason": "no intent",
                "intent": "null",
                "confidence": 0.0,
                "duration": 0.0,
                "source": source,
                "memory": memory,
                "memory_context": memory_context,
            }
            self._log_action(result)
            return result

        execution_time = round(max(0.0, 1.0 - confidence), 2)
        if self.simulate_delay and execution_time > 0:
            time.sleep(execution_time)

        result = {
            "timestamp": time.time(),
            "status": "executed",
            "intent": intent,
            "confidence": confidence,
            "duration": execution_time,
            "source": source,
            "memory": memory,
            "memory_context": memory_context,
        }
        self._log_action(result)
        return result

    def _log_action(self, entry: Dict[str, Any]) -> None:
        normalized = {
            "timestamp": entry.get("timestamp", time.time()),
            "intent": entry.get("intent", "unknown"),
            "confidence": float(entry.get("confidence", 0.0)),
            "status": entry.get("status", "unknown"),
            "duration": float(entry.get("duration", 0.0)),
            "source": entry.get("source", "unknown"),
            "memory": entry.get("memory", entry.get("memory_context", [])),
            "memory_context": entry.get("memory_context", []),
        }
        for k, v in entry.items():
            if k not in normalized:
                normalized[k] = v
        self.action_log.append(normalized)

    def get_action_log(self) -> List[Dict[str, Any]]:
        return self.action_log

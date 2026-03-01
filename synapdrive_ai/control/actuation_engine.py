# synapdrive_ai/control/actuation_engine.py

from __future__ import annotations

import time
from typing import Any, Dict, List


class ActuationEngine:
    """
    Simulated actuation engine that converts intent packets into mock physical actions.

    IMPORTANT:
    The action_log schema is treated like telemetry and is consumed by:
      - synapdrive_ai/interface/dashboard.py
      - synapdrive_ai/cloud/cloud_stub.py (via dashboard transmit)
      - any future UI / tests

    Each log entry is normalized to include:
      timestamp, intent, confidence, status, duration, source, memory, memory_context
    """

    def __init__(self) -> None:
        self.action_log: List[Dict[str, Any]] = []

    def execute_intent(self, intent_packet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a simulated action based on an intent packet.

        Expected intent_packet shape (best-effort; we default safely if missing):
            {
                "intent": str,
                "source": str,
                "confidence": float,
                "memory_context": list
            }
        """
        intent = (intent_packet or {}).get("intent")
        source = (intent_packet or {}).get("source", "unknown")
        confidence = float((intent_packet or {}).get("confidence", 0.0))
        memory_context = (intent_packet or {}).get("memory_context", [])
        # Dashboard prints "memory" specifically, so we keep both keys
        memory = (intent_packet or {}).get("memory", memory_context)

        # Normalize confidence to [0, 1]
        if confidence < 0.0:
            confidence = 0.0
        if confidence > 1.0:
            confidence = 1.0

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

        # Simulate execution delay (faster when confidence is higher)
        execution_time = round(max(0.0, 1.0 - confidence), 2)
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
        """
        Append a telemetry-safe entry. This is our single source of truth for the log schema.
        """
        # Ensure required keys exist even if caller forgot them
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
        # Keep any extra keys (like "reason") without breaking dashboards
        for k, v in entry.items():
            if k not in normalized:
                normalized[k] = v

        self.action_log.append(normalized)

    def get_action_log(self) -> List[Dict[str, Any]]:
        return self.action_log

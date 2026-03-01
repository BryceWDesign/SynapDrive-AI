# synapdrive_ai/bci/intent_generator.py

from __future__ import annotations

from typing import Dict, Any

from synapdrive_ai.intent.intent_parser import IntentParser


def generate_intent(simulated_input: str) -> Dict[str, Any]:
    """
    Simulation-first intent extraction.

    Accepts:
      - freeform text ("move left", "stop", "switch mode to manual")
      - simple labels (anything else)

    Returns a structured intent packet compatible with the existing stack:
      {
        "intent": str,
        "confidence": float,
        "source": str,
        "raw_text": str,
        "params": dict,
        "memory_context": list
      }
    """
    raw = (simulated_input or "").strip()
    parser = IntentParser()

    parsed = parser.parse(raw)

    # Conservative default for unknown inputs
    intent = "unknown"
    confidence = 0.40
    params: Dict[str, str] = {}

    if parsed is not None:
        params = dict(parsed.params)

        # Map parsed intents into a simple actuator-command namespace
        if parsed.intent == "move":
            intent = f"move_{params.get('direction', 'unknown')}"
        elif parsed.intent == "turn":
            intent = f"turn_{params.get('direction', 'unknown')}"
        elif parsed.intent == "stop":
            # Align with existing AGI mapping name when possible
            intent = "halt_all_motion"
        elif parsed.intent == "pick_up":
            intent = "pick_up"
        elif parsed.intent == "drop":
            intent = "drop"
        elif parsed.intent == "switch_mode":
            intent = f"switch_mode_{params.get('mode', 'unknown')}"
        else:
            intent = parsed.intent

        confidence = 0.80

    return {
        "intent": intent,
        "confidence": float(confidence),
        "source": "text_input",
        "raw_text": raw,
        "params": params,
        "memory_context": [],
    }

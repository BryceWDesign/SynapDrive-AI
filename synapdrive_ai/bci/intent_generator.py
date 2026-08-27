from __future__ import annotations

from typing import Any, Dict

from synapdrive_ai.intent.intent_parser import IntentParser


def generate_intent(command_text: str) -> Dict[str, Any]:
    """Parse a caller-declared text command into the simulation action namespace.

    This path does not infer a user's intent from physiology. A recognized grammar match
    receives confidence 1.0 because the mapping itself is deterministic; the packet marks
    that semantic explicitly. Unknown text fails closed with zero confidence.
    """

    raw = (command_text or "").strip()
    parser = IntentParser()
    parsed = parser.parse(raw)

    intent = "unknown"
    confidence = 0.0
    params: Dict[str, str] = {}

    if parsed is not None:
        params = dict(parsed.params)
        if parsed.intent == "move":
            intent = f"move_{params.get('direction', 'unknown')}"
        elif parsed.intent == "turn":
            intent = f"turn_{params.get('direction', 'unknown')}"
        elif parsed.intent == "stop":
            intent = "halt_all_motion"
        elif parsed.intent == "pick_up":
            intent = "pick_up"
        elif parsed.intent == "drop":
            intent = "drop"
        elif parsed.intent == "switch_mode":
            intent = f"switch_mode_{params.get('mode', 'unknown')}"
        else:
            intent = parsed.intent
        confidence = 1.0

    return {
        "intent": intent,
        "confidence": confidence,
        "source": "text_input",
        "raw_text": raw,
        "params": params,
        "memory_context": [],
        "inference_authority": "declared-command",
        "confidence_semantics": (
            "deterministic-parser-match" if parsed is not None else "no-parser-match"
        ),
        "neural_decode_performed": False,
    }

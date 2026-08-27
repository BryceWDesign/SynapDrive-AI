from __future__ import annotations

from typing import Mapping


class IntentClassifier:
    """Compatibility label mapper for explicitly declared synthetic labels.

    This class does not decode physiology. Historical versions derived confidence from
    signal RMS, which falsely converted amplitude into semantic certainty. The compatibility
    path now treats a recognized caller-supplied label as injected ground truth for software
    tests and marks that provenance explicitly.
    """

    def __init__(self):
        self.rules = {
            "think_move": "move_forward",
            "think_stop": "halt",
            "think_turn": "rotate_right",
            "think_grab": "activate_claw",
        }

def classify(self, signal_data: Mapping[str, object] | None) -> dict[str, object]:
    signal_data = signal_data or {}
    raw_label = signal_data.get("label")
    label = raw_label if isinstance(raw_label, str) else None
    intent = self.rules.get(label or "", "unknown")
    recognized = intent != "unknown"

    return {
        "intent": intent,
        "confidence": 1.0 if recognized else 0.0,
        "source": f"declared-synthetic-label/{label or 'unknown'}",
        "memory_context": [],
        "inference_authority": "synthetic-ground-truth" if recognized else "none",
        "confidence_semantics": (
            "synthetic-ground-truth-label" if recognized else "unrecognized-label"
        ),
        "neural_decode_performed": False,
        "analysis_only": not recognized,
    }

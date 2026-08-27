from __future__ import annotations

from collections import deque
from typing import Any

import numpy as np


class LabeledSignalMapper:
    """Map an explicitly supplied synthetic label into the simulation action namespace.

    This is not a neural decoder. The caller already supplies the class label. The
    ``confidence`` field is therefore a ground-truth fixture value used only to exercise
    downstream governance. Raw waveform magnitude never changes it.
    """

    def __init__(self, memory_length: int = 5) -> None:
        self.memory = deque(maxlen=memory_length)
        self.intent_weights = {
            "left_arm": {"motor": "move_left_arm", "priority": 1.0},
            "right_arm": {"motor": "move_right_arm", "priority": 1.0},
            "walk": {"motor": "initiate_walk", "priority": 1.0},
            "stop": {"motor": "halt_all_motion", "priority": 1.0},
            "calculate": {"cognitive": "initiate_computation", "priority": 1.0},
            "recall": {"cognitive": "retrieve_memory", "priority": 1.0},
            "explore": {"cognitive": "expand_context", "priority": 1.0},
        }

    def receive_signal(self, label: str, signal_data: Any):
        summary = self._signal_summary(label, signal_data)
        self.memory.append(summary)
        return self.reason(label, signal_data)

    def reason(self, label: str, signal_data: Any):
        del signal_data  # The waveform is intentionally not treated as decoder evidence.
        if label not in self.intent_weights:
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "source": f"synthetic_label/{label}",
                "memory_context": list(self.memory),
                "neural_decode_performed": False,
                "confidence_semantics": "no-decoder",
                "inference_authority": "synthetic-ground-truth",
            }

        intent_data = self.intent_weights[label]
        return {
            "intent": intent_data.get("motor") or intent_data.get("cognitive"),
            "source": f"synthetic_label/{label}",
            "confidence": 1.0,
            "memory_context": list(self.memory),
            "neural_decode_performed": False,
            "confidence_semantics": "synthetic-ground-truth-label",
            "inference_authority": "synthetic-ground-truth",
        }

    @staticmethod
    def _signal_summary(label: str, signal_data: Any) -> dict[str, Any]:
        try:
            arr = np.asarray(signal_data, dtype=float).ravel()
            rms = float(np.sqrt(np.mean(np.square(arr)))) if arr.size else 0.0
            n_samples = int(arr.size)
        except Exception:
            rms = 0.0
            n_samples = 0
        return {"label": label, "n_samples": n_samples, "rms": round(rms, 6)}


class AGICoreReasoner(LabeledSignalMapper):
    """Deprecated compatibility name for :class:`LabeledSignalMapper`.

    No AGI capability is claimed or implemented by this class.
    """

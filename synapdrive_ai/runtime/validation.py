"""Strict, bounded packet contracts at the trusted simulation API boundary."""

from __future__ import annotations

import json
import math
from typing import Any, Mapping


def finite(value: Any, name: str, lower: float = 0, upper: float = 1) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}: expected a number")
    number = float(value)
    if not math.isfinite(number) or not lower <= number <= upper:
        raise ValueError(f"{name}: out of range or non-finite")
    return number


def validate_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(packet, dict):
        raise ValueError("packet must be an object")
    try:
        encoded = json.dumps(packet, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError("packet must contain finite JSON data") from error
    if len(encoded.encode()) > 65536:
        raise ValueError("packet exceeds 64 KiB budget")
    out = json.loads(encoded)
    for name in ("intent", "source"):
        if not isinstance(out.get(name), str) or not out[name].strip():
            raise ValueError(f"{name} is required")
    finite(out.get("confidence"), "confidence")
    for name in ("uncertainty", "signal_quality", "predicted_risk", "required_confidence"):
        if name in out:
            finite(out[name], name)
    if "drift_score" in out:
        finite(out["drift_score"], "drift_score", 0, 1e6)
    for name in ("analysis_only", "neural_decode_performed"):
        if name in out and not isinstance(out[name], bool):
            raise ValueError(f"{name} must be boolean")
    if "probabilities" in out:
        probs = out["probabilities"]
        if not isinstance(probs, dict) or not probs:
            raise ValueError("probabilities must be a nonempty object")
        values = [finite(v, "probability") for v in probs.values()]
        if abs(sum(values) - 1) > 1e-6:
            raise ValueError("probabilities must sum to one")
        if probs.get(out["intent"], 0) + 1e-9 < max(values):
            raise ValueError("action disagrees with decoded distribution")
    if out.get("neural_decode_performed") and not out.get("analysis_only"):
        for name in ("signal_quality", "drift_score", "qualification_id"):
            if name not in out:
                raise ValueError(f"decoded action requires {name}")
    return out

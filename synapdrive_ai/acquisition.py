"""Fresh, ordered stream-window admission for a qualified research decoder.

Timestamps must be in the caller's trusted monotonic clock domain. This detects
staleness/gaps under that contract; it cannot authenticate a dishonest sensor.
"""

from __future__ import annotations

import time

import numpy as np

from synapdrive_ai.decoding import EEGDecoder
from synapdrive_ai.runtime.dispatch import digest


class StreamDecoder:
    def __init__(self, model: EEGDecoder, *, max_age=0.5, gap_factor=1.5, clock=time.monotonic):
        if not 0 < max_age <= 5 or not 1 < gap_factor <= 3:
            raise ValueError("invalid freshness or gap policy")
        self.model, self.max_age, self.gap_factor = model, max_age, gap_factor
        self.clock = clock
        self.last_end: float | None = None

    def packet(self, samples, timestamps, metadata, action_map):
        def reject(reason):
            return {
                "intent": "unknown",
                "source": "stream-admission",
                "confidence": 0.0,
                "analysis_only": True,
                "abstention_reason": reason,
            }

        timestamps = np.asarray(timestamps, dtype=float)
        if (
            timestamps.ndim != 1
            or len(timestamps) != self.model.identity.samples
            or not np.isfinite(timestamps).all()
        ):
            return reject("timestamp shape or finite-data mismatch")
        intervals = np.diff(timestamps)
        expected = 1 / self.model.identity.sampling_rate
        if (
            np.any(intervals <= 0)
            or np.any(intervals > expected * self.gap_factor)
            or np.any(intervals < expected / self.gap_factor)
        ):
            return reject("sample gap, reordering or clock-rate mismatch")
        age = self.clock() - float(timestamps[-1])
        if age < 0 or age > self.max_age:
            return reject("stale or future window")
        if self.last_end is not None and timestamps[0] <= self.last_end:
            return reject("overlapping or replayed window")
        self.last_end = float(timestamps[-1])
        packet = self.model.packet(samples, metadata, action_map)
        packet["evidence_id"] = digest(
            {"timestamps": timestamps.tolist(), "artifact": self.model.artifact_id()}
        )
        return packet

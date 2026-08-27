from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np


@dataclass(frozen=True)
class FaultResult:
    signal: np.ndarray
    metadata: Dict[str, float | int | str]


class FaultInjector:
    """Deterministic scientific fault injection for EEG-style arrays."""

    def __init__(self, seed: int = 0) -> None:
        self.rng = np.random.default_rng(seed)

    def gaussian_noise(self, signal: np.ndarray, sigma: float) -> FaultResult:
        x = np.asarray(signal, dtype=float)
        out = x + self.rng.normal(0.0, float(sigma), size=x.shape)
        return FaultResult(out, {"fault": "gaussian_noise", "sigma": float(sigma)})

    def dropout(self, signal: np.ndarray, fraction: float) -> FaultResult:
        x = np.asarray(signal, dtype=float).copy()
        fraction = max(0.0, min(1.0, float(fraction)))
        n = x.shape[-1]
        width = int(round(n * fraction))
        if width > 0:
            start = int(self.rng.integers(0, max(1, n - width + 1)))
            x[..., start : start + width] = 0.0
        else:
            start = 0
        return FaultResult(
            x,
            {
                "fault": "dropout",
                "fraction": fraction,
                "start": start,
                "width": width,
            },
        )

    def clip(self, signal: np.ndarray, quantile: float = 0.90) -> FaultResult:
        x = np.asarray(signal, dtype=float).copy()
        q = max(0.5, min(0.999, float(quantile)))
        limit = float(np.quantile(np.abs(x), q))
        if limit > 0:
            x = np.clip(x, -limit, limit)
        return FaultResult(x, {"fault": "clip", "quantile": q, "limit": limit})

    def line_noise(
        self,
        signal: np.ndarray,
        sampling_rate: float,
        frequency: float = 60.0,
        amplitude: float = 1.0,
    ) -> FaultResult:
        x = np.asarray(signal, dtype=float)
        t = np.arange(x.shape[-1], dtype=float) / float(sampling_rate)
        noise = float(amplitude) * np.sin(2 * np.pi * float(frequency) * t)
        out = x + noise
        return FaultResult(
            out,
            {
                "fault": "line_noise",
                "frequency": float(frequency),
                "amplitude": float(amplitude),
            },
        )

    def channel_swap(self, signal: np.ndarray, a: int, b: int) -> FaultResult:
        x = np.asarray(signal, dtype=float).copy()
        if x.ndim != 2:
            raise ValueError("channel_swap requires shape (channels, samples)")
        if a == b or not (0 <= a < x.shape[0]) or not (0 <= b < x.shape[0]):
            raise ValueError("invalid channel indices")
        x[[a, b]] = x[[b, a]]
        return FaultResult(x, {"fault": "channel_swap", "a": a, "b": b})

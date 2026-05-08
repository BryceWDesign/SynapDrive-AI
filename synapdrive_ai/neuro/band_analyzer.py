from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np

BANDS: Dict[str, Tuple[float, float]] = {
    "delta": (0.5, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
    "gamma": (30.0, 80.0),
}


@dataclass
class BandPowerResult:
    """Per-band absolute and relative power, plus derived confidence."""

    absolute: Dict[str, float]
    relative: Dict[str, float]
    total_power: float
    engagement_ratio: float
    cognitive_ratio: float
    confidence: float
    intent_class: str


class BandPowerAnalyzer:
    """
    Computes EEG band power from a 1-D signal array using Welch's method.

    Args:
        sampling_rate: Hz. Must match the actual acquisition rate of the signal.
        nperseg: Welch segment length. Defaults to min(256, len(signal)).
    """

    def __init__(self, sampling_rate: float = 256.0, nperseg: Optional[int] = None) -> None:
        self.sampling_rate = float(sampling_rate)
        self._nperseg = nperseg

    def analyze(self, signal: np.ndarray) -> BandPowerResult:
        signal = np.asarray(signal, dtype=float).ravel()
        if len(signal) < 4:
            return self._zero_result()

        freqs, psd = self._welch(signal)

        absolute: Dict[str, float] = {}
        _integrate = getattr(np, "trapezoid", None) or getattr(np, "trapz")
        for band, (lo, hi) in BANDS.items():
            mask = (freqs >= lo) & (freqs < hi)
            absolute[band] = float(_integrate(psd[mask], freqs[mask])) if mask.any() else 0.0

        total = sum(absolute.values()) or 1e-9
        relative = {b: v / total for b, v in absolute.items()}

        engagement = (absolute["beta"] + absolute["gamma"]) / max(
            absolute["alpha"] + absolute["theta"], 1e-9
        )
        cognitive = (absolute["theta"] + absolute["gamma"]) / max(absolute["alpha"], 1e-9)

        intent_class, confidence = self._classify(engagement, cognitive, relative)

        return BandPowerResult(
            absolute=absolute,
            relative=relative,
            total_power=total,
            engagement_ratio=round(engagement, 4),
            cognitive_ratio=round(cognitive, 4),
            confidence=round(float(np.clip(confidence, 0.0, 1.0)), 3),
            intent_class=intent_class,
        )

    def _welch(self, signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        n = len(signal)
        nperseg = self._nperseg or min(256, n)
        nperseg = min(nperseg, n)
        step = nperseg // 2 or 1

        window = np.hanning(nperseg)
        win_power = np.sum(window**2)

        segments = []
        start = 0
        while start + nperseg <= n:
            seg = signal[start : start + nperseg] * window
            segments.append(np.abs(np.fft.rfft(seg)) ** 2 / (self.sampling_rate * win_power))
            start += step

        if not segments:
            psd = np.abs(np.fft.rfft(signal)) ** 2 / (self.sampling_rate * len(signal))
        else:
            psd = np.mean(segments, axis=0)

        freqs = np.fft.rfftfreq(nperseg, d=1.0 / self.sampling_rate)
        return freqs, psd

    def _classify(
        self,
        engagement: float,
        cognitive: float,
        relative: Dict[str, float],
    ) -> Tuple[str, float]:
        alpha_dom = relative.get("alpha", 0.0) > 0.40

        if alpha_dom:
            confidence = max(0.10, 0.5 - relative["alpha"])
            return "unclear", confidence

        if engagement >= cognitive:
            confidence = float(np.clip(engagement / (engagement + 1.5), 0.1, 1.0))
            return "motor", confidence

        confidence = float(np.clip(cognitive / (cognitive + 2.0), 0.1, 1.0))
        return "cognitive", confidence

    def _zero_result(self) -> BandPowerResult:
        zero_bands = {b: 0.0 for b in BANDS}
        return BandPowerResult(
            absolute=zero_bands,
            relative=zero_bands,
            total_power=0.0,
            engagement_ratio=0.0,
            cognitive_ratio=0.0,
            confidence=0.0,
            intent_class="unclear",
        )

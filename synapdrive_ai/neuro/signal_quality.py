from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

import numpy as np


@dataclass(frozen=True)
class SignalQualityReport:
    score: float
    state: str
    finite_fraction: float
    flatline_fraction: float
    clipping_fraction: float
    dropout_fraction: float
    line_noise_ratio: float
    issues: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, float | str | list[str]]:
        return {
            "score": self.score,
            "state": self.state,
            "finite_fraction": self.finite_fraction,
            "flatline_fraction": self.flatline_fraction,
            "clipping_fraction": self.clipping_fraction,
            "dropout_fraction": self.dropout_fraction,
            "line_noise_ratio": self.line_noise_ratio,
            "issues": list(self.issues),
        }


class SignalQualityAnalyzer:
    """Deterministic quality checks for one or more EEG-style channels.

    The score is an engineering heuristic for gating analysis. It is not a clinical
    signal-quality index and is deliberately exposed as separate component metrics.
    """

    def __init__(self, sampling_rate: float, line_frequency: float = 60.0) -> None:
        if sampling_rate <= 0:
            raise ValueError("sampling_rate must be positive")
        self.sampling_rate = float(sampling_rate)
        self.line_frequency = float(line_frequency)

    def analyze(self, signal: np.ndarray) -> SignalQualityReport:
        x = np.asarray(signal, dtype=float)
        if x.ndim == 1:
            x = x[None, :]
        if x.size == 0 or x.shape[1] < 4:
            return SignalQualityReport(
                0.0,
                "invalid",
                0.0,
                1.0,
                0.0,
                1.0,
                0.0,
                ("insufficient-samples",),
            )

        finite = np.isfinite(x)
        finite_fraction = float(np.mean(finite))
        safe = np.where(finite, x, 0.0)
        centered = safe - np.mean(safe, axis=1, keepdims=True)
        scale = np.std(centered, axis=1, keepdims=True)

        # Flatline is assessed from near-zero first differences relative to channel scale.
        diffs = np.abs(np.diff(safe, axis=1))
        eps = np.maximum(scale[:, :1] * 1e-5, 1e-12)
        flatline_fraction = float(np.mean(diffs <= eps))

        # Dropout catches exact-zero runs, a common stream failure representation.
        dropout_fraction = float(np.mean(np.isclose(safe, 0.0, atol=1e-12)))

        # Clipping catches excessive samples pinned at the observed extrema.
        clipping_parts = []
        for ch in safe:
            lo, hi = float(np.min(ch)), float(np.max(ch))
            if np.isclose(lo, hi):
                clipping_parts.append(1.0)
            else:
                clipping_parts.append(float(np.mean(np.isclose(ch, lo) | np.isclose(ch, hi))))
        clipping_fraction = float(np.mean(clipping_parts))

        line_noise_ratio = self._line_noise_ratio(centered)

        issues: list[str] = []
        if finite_fraction < 0.999:
            issues.append("non-finite-samples")
        if flatline_fraction > 0.20:
            issues.append("flatline")
        if dropout_fraction > 0.20:
            issues.append("dropout")
        if clipping_fraction > 0.08:
            issues.append("clipping")
        if line_noise_ratio > 0.35:
            issues.append("line-noise")

        penalty = (
            0.45 * (1.0 - finite_fraction)
            + 0.25 * min(1.0, flatline_fraction / 0.30)
            + 0.15 * min(1.0, dropout_fraction / 0.30)
            + 0.10 * min(1.0, clipping_fraction / 0.12)
            + 0.05 * min(1.0, line_noise_ratio / 0.50)
        )
        score = float(np.clip(1.0 - penalty, 0.0, 1.0))
        if score >= 0.80:
            state = "good"
        elif score >= 0.55:
            state = "degraded"
        elif score >= 0.35:
            state = "unreliable"
        else:
            state = "invalid"
        return SignalQualityReport(
            round(score, 6),
            state,
            round(finite_fraction, 6),
            round(flatline_fraction, 6),
            round(clipping_fraction, 6),
            round(dropout_fraction, 6),
            round(line_noise_ratio, 6),
            tuple(issues),
        )

    def _line_noise_ratio(self, centered: np.ndarray) -> float:
        n = centered.shape[1]
        if n < 8:
            return 0.0
        freqs = np.fft.rfftfreq(n, d=1.0 / self.sampling_rate)
        power = np.mean(np.abs(np.fft.rfft(centered, axis=1)) ** 2, axis=0)
        total = float(np.sum(power[(freqs >= 1.0) & (freqs <= min(100.0, self.sampling_rate / 2))]))
        if total <= 1e-18:
            return 0.0
        width = max(0.75, self.sampling_rate / n * 2.0)
        mask = np.abs(freqs - self.line_frequency) <= width
        return float(np.clip(np.sum(power[mask]) / total, 0.0, 1.0))

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class UncertaintyEstimate:
    entropy: float
    margin_uncertainty: float
    disagreement: float
    combined: float
    top_label: str
    top_probability: float

    def to_dict(self) -> Dict[str, float | str]:
        return {
            "entropy": self.entropy,
            "margin_uncertainty": self.margin_uncertainty,
            "disagreement": self.disagreement,
            "combined": self.combined,
            "top_label": self.top_label,
            "top_probability": self.top_probability,
        }


def _numeric_value(value: object, *, field: str) -> float:
    if isinstance(value, (int, float, str)):
        return float(value)
    raise TypeError(f"{field} must be numeric")


def normalize_distribution(values: Mapping[str, float]) -> Dict[str, float]:
    clean = {str(k): max(0.0, float(v)) for k, v in values.items()}
    total = sum(clean.values())
    if total <= 0:
        if not clean:
            return {"unknown": 1.0}
        uniform = 1.0 / len(clean)
        return {k: uniform for k in clean}
    return {k: v / total for k, v in clean.items()}


def packet_distribution(packet: Mapping[str, object]) -> Dict[str, float]:
    provided = packet.get("probabilities")
    if isinstance(provided, Mapping) and provided:
        parsed = {
            str(k): _numeric_value(v, field=f"probabilities[{k!r}]")
            for k, v in provided.items()
        }
        return normalize_distribution(parsed)

    intent = str(packet.get("intent") or "unknown")
    confidence = max(
        0.0,
        min(
            1.0,
            _numeric_value(
                packet.get("confidence", 0.0),
                field="confidence",
            ),
        ),
    )

    if intent == "unknown":
        return {
            "unknown": max(confidence, 0.5),
            "other": 1.0 - max(confidence, 0.5),
        }

    return normalize_distribution(
        {
            intent: confidence,
            "unknown": 1.0 - confidence,
        }
    )


def estimate_uncertainty(
    probabilities: Mapping[str, float],
    ensemble_probabilities: Sequence[Mapping[str, float]] | None = None,
) -> UncertaintyEstimate:
    probs = normalize_distribution(probabilities)
    labels = sorted(probs)
    arr = np.array([probs[k] for k in labels], dtype=float)

    if len(arr) <= 1:
        entropy = 0.0
        margin_u = 0.0
    else:
        raw_entropy = -float(
            np.sum(arr * np.log(np.clip(arr, 1e-12, 1.0)))
        )
        entropy = raw_entropy / math.log(len(arr))
        sorted_probs = np.sort(arr)[::-1]
        margin_u = 1.0 - float(
            sorted_probs[0] - sorted_probs[1]
        )

    disagreement = 0.0
    if ensemble_probabilities and len(ensemble_probabilities) > 1:
        union = sorted(
            {
                k
                for member in ensemble_probabilities
                for k in member
            }
        )
        matrix = np.array(
            [
                [
                    normalize_distribution(member).get(k, 0.0)
                    for k in union
                ]
                for member in ensemble_probabilities
            ],
            dtype=float,
        )
        disagreement = float(
            np.clip(
                np.mean(np.std(matrix, axis=0)) * 2.0,
                0.0,
                1.0,
            )
        )

    combined = float(
        np.clip(
            0.55 * entropy
            + 0.30 * margin_u
            + 0.15 * disagreement,
            0.0,
            1.0,
        )
    )

    top_label = max(
        probs.items(),
        key=lambda item: item[1],
    )[0]

    return UncertaintyEstimate(
        entropy=round(entropy, 6),
        margin_uncertainty=round(margin_u, 6),
        disagreement=round(disagreement, 6),
        combined=round(combined, 6),
        top_label=top_label,
        top_probability=round(probs[top_label], 6),
    )


class ReliabilityCalibrator:
    """Histogram reliability calibrator with deterministic binning.

    Fit using model confidence and binary correctness. Transform maps raw
    confidence to observed empirical accuracy in its bin. No model claims
    are made before fit().
    """

    def __init__(self, n_bins: int = 10) -> None:
        if n_bins < 2:
            raise ValueError("n_bins must be >= 2")
        self.n_bins = int(n_bins)
        self._rates: np.ndarray | None = None
        self._counts: np.ndarray | None = None

    @property
    def fitted(self) -> bool:
        return self._rates is not None

    def fit(
        self,
        confidence: Iterable[float],
        correct: Iterable[bool],
    ) -> "ReliabilityCalibrator":
        conf = np.clip(
            np.asarray(list(confidence), dtype=float),
            0.0,
            1.0,
        )
        ok = np.asarray(list(correct), dtype=float)

        if conf.size == 0 or conf.size != ok.size:
            raise ValueError(
                "confidence and correct must be non-empty and equal length"
            )

        indices = np.minimum(
            (conf * self.n_bins).astype(int),
            self.n_bins - 1,
        )

        rates = np.zeros(self.n_bins, dtype=float)
        counts = np.zeros(self.n_bins, dtype=int)
        global_rate = float(np.mean(ok))

        for idx in range(self.n_bins):
            mask = indices == idx
            counts[idx] = int(np.sum(mask))
            rates[idx] = (
                float(np.mean(ok[mask]))
                if counts[idx]
                else global_rate
            )

        self._rates = rates
        self._counts = counts
        return self

    def transform(self, confidence: float) -> float:
        if self._rates is None:
            raise RuntimeError("calibrator has not been fit")

        value = float(
            np.clip(
                confidence,
                0.0,
                1.0,
            )
        )
        idx = min(
            int(value * self.n_bins),
            self.n_bins - 1,
        )

        return float(
            np.clip(
                self._rates[idx],
                0.0,
                1.0,
            )
        )
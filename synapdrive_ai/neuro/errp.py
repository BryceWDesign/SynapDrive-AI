from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np


@dataclass(frozen=True)
class ErrPFeatures:
    early_mean: float
    negative_peak: float
    late_mean: float
    positive_peak: float

    def as_array(self) -> np.ndarray:
        return np.array(
            [
                self.early_mean,
                self.negative_peak,
                self.late_mean,
                self.positive_peak,
            ],
            dtype=float,
        )


class ErrPFeatureExtractor:
    """Extracts event-related potential features from an event-locked epoch.

    Windows are relative to event onset. This is a generic feature extractor, not a
    validated ErrP detector. Classification requires user-supplied labeled calibration.
    """

    def __init__(self, sampling_rate: float, event_index: int = 0) -> None:
        self.sampling_rate = float(sampling_rate)
        self.event_index = int(event_index)

    def extract(self, epoch: Sequence[float] | np.ndarray) -> ErrPFeatures:
        x = np.asarray(epoch, dtype=float)
        if x.ndim != 1:
            raise ValueError("epoch must be one-dimensional")
        if len(x) < max(4, self.event_index + int(0.60 * self.sampling_rate)):
            raise ValueError("epoch is too short for configured ErrP windows")
        early = self._window(x, 0.10, 0.25)
        negative = self._window(x, 0.20, 0.35)
        late = self._window(x, 0.35, 0.60)
        return ErrPFeatures(
            early_mean=float(np.mean(early)),
            negative_peak=float(np.min(negative)),
            late_mean=float(np.mean(late)),
            positive_peak=float(np.max(late)),
        )

    def _window(self, x: np.ndarray, start_s: float, end_s: float) -> np.ndarray:
        start = self.event_index + int(start_s * self.sampling_rate)
        end = self.event_index + int(end_s * self.sampling_rate)
        return x[start:max(start + 1, end)]


class ErrPLDAClassifier:
    """Small, inspectable LDA classifier trained only on supplied labeled epochs."""

    def __init__(self, regularization: float = 1e-5) -> None:
        self.regularization = float(regularization)
        self.w_: np.ndarray | None = None
        self.b_: float | None = None

    @property
    def fitted(self) -> bool:
        return self.w_ is not None and self.b_ is not None

    def fit(
        self,
        features: Iterable[Iterable[float]],
        labels: Iterable[int],
    ) -> "ErrPLDAClassifier":
        x = np.asarray(list(features), dtype=float)
        y = np.asarray(list(labels), dtype=int)
        if x.ndim != 2 or len(x) != len(y) or len(x) < 4:
            raise ValueError("features and labels must contain at least four aligned samples")
        if set(np.unique(y)) != {0, 1}:
            raise ValueError("labels must contain both classes 0 and 1")
        x0, x1 = x[y == 0], x[y == 1]
        m0, m1 = np.mean(x0, axis=0), np.mean(x1, axis=0)
        c0 = np.cov(x0, rowvar=False) if len(x0) > 1 else np.eye(x.shape[1])
        c1 = np.cov(x1, rowvar=False) if len(x1) > 1 else np.eye(x.shape[1])
        numerator = (
            (len(x0) - 1) * np.atleast_2d(c0)
            + (len(x1) - 1) * np.atleast_2d(c1)
        )
        cov = numerator / max(len(x) - 2, 1)
        cov = cov + np.eye(x.shape[1]) * self.regularization
        inv = np.linalg.pinv(cov)
        self.w_ = inv @ (m1 - m0)
        p0, p1 = len(x0) / len(x), len(x1) / len(x)
        self.b_ = float(-0.5 * (m1 + m0) @ self.w_ + np.log(max(p1, 1e-12) / max(p0, 1e-12)))
        return self

    def predict_proba(self, feature: Iterable[float]) -> float:
        if not self.fitted:
            raise RuntimeError("classifier has not been fit")
        x = np.asarray(list(feature), dtype=float)
        assert self.w_ is not None and self.b_ is not None
        z = float(np.clip(x @ self.w_ + self.b_, -60, 60))
        return float(1.0 / (1.0 + np.exp(-z)))

    def predict(self, feature: Iterable[float], threshold: float = 0.5) -> int:
        return int(self.predict_proba(feature) >= threshold)

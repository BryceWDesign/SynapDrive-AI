from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class DriftResult:
    score: float
    drifted: bool
    threshold: float


class FeatureDriftMonitor:
    """Mahalanobis-distance drift monitor for decoder feature vectors."""

    def __init__(self, quantile: float = 0.99, regularization: float = 1e-6) -> None:
        if not 0.5 < quantile < 1.0:
            raise ValueError("quantile must be between 0.5 and 1.0")
        self.quantile = quantile
        self.regularization = regularization
        self.mean_: np.ndarray | None = None
        self.inv_cov_: np.ndarray | None = None
        self.threshold_: float | None = None

    def fit(self, features: Iterable[Iterable[float]]) -> "FeatureDriftMonitor":
        x = np.asarray(list(features), dtype=float)
        if x.ndim != 2 or len(x) < 3:
            raise ValueError("need at least three feature vectors")
        self.mean_ = np.mean(x, axis=0)
        cov = np.cov(x, rowvar=False)
        if np.ndim(cov) == 0:
            cov = np.array([[float(cov)]])
        cov = np.atleast_2d(cov) + np.eye(x.shape[1]) * self.regularization
        self.inv_cov_ = np.linalg.pinv(cov)
        scores = np.array([self._score(row) for row in x])
        self.threshold_ = max(float(np.quantile(scores, self.quantile)), 1e-9)
        return self

    def evaluate(self, feature: Iterable[float]) -> DriftResult:
        if self.mean_ is None or self.inv_cov_ is None or self.threshold_ is None:
            raise RuntimeError("drift monitor has not been fit")
        score = self._score(np.asarray(list(feature), dtype=float))
        return DriftResult(round(score, 6), score > self.threshold_, round(self.threshold_, 6))

    def _score(self, row: np.ndarray) -> float:
        assert self.mean_ is not None and self.inv_cov_ is not None
        delta = row - self.mean_
        return float(np.sqrt(max(0.0, delta @ self.inv_cov_ @ delta)))

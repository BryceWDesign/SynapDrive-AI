from __future__ import annotations

from typing import Dict, List, Protocol, Sequence

import numpy as np


class Decoder(Protocol):
    classes_: np.ndarray

    def fit(
        self,
        epochs: np.ndarray,
        labels: np.ndarray,
        sampling_rate: float,
    ) -> "Decoder": ...

    def predict_proba(
        self,
        epochs: np.ndarray,
        sampling_rate: float,
    ) -> np.ndarray: ...


def _softmax(scores: np.ndarray) -> np.ndarray:
    z = scores - np.max(scores, axis=1, keepdims=True)
    exp = np.exp(np.clip(z, -60, 60))
    return exp / np.sum(exp, axis=1, keepdims=True)


class SpectralCentroidDecoder:
    """Inspectable frequency-band feature decoder using nearest class centroids."""

    bands = ((4.0, 8.0), (8.0, 13.0), (13.0, 30.0), (30.0, 45.0))

    def __init__(self) -> None:
        self.classes_: np.ndarray = np.array([])
        self.centroids_: Dict[object, np.ndarray] = {}
        self.scale_: np.ndarray | None = None

    def _features(self, epochs: np.ndarray, sampling_rate: float) -> np.ndarray:
        x = np.asarray(epochs, dtype=float)
        if x.ndim != 3:
            raise ValueError("epochs must be 3-D")
        n = x.shape[-1]
        freqs = np.fft.rfftfreq(n, d=1.0 / sampling_rate)
        centered = x - np.mean(x, axis=-1, keepdims=True)
        power = np.abs(np.fft.rfft(centered, axis=-1)) ** 2
        total_mask = (freqs >= 1.0) & (
            freqs <= min(45.0, sampling_rate / 2)
        )
        total = np.sum(power[..., total_mask], axis=-1) + 1e-12
        feats: List[np.ndarray] = []
        for lo, hi in self.bands:
            mask = (freqs >= lo) & (freqs < hi)
            band = np.sum(power[..., mask], axis=-1) / total
            feats.append(band)
        return np.concatenate(feats, axis=1)

    def fit(
        self,
        epochs: np.ndarray,
        labels: np.ndarray,
        sampling_rate: float,
    ) -> "SpectralCentroidDecoder":
        y = np.asarray(labels)
        f = self._features(epochs, sampling_rate)
        self.classes_ = np.unique(y)
        if len(self.classes_) < 2:
            raise ValueError("at least two classes are required")
        self.scale_ = np.std(f, axis=0) + 1e-6
        z = f / self.scale_
        self.centroids_ = {
            cls: np.mean(z[y == cls], axis=0) for cls in self.classes_
        }
        return self

    def predict_proba(
        self,
        epochs: np.ndarray,
        sampling_rate: float,
    ) -> np.ndarray:
        if self.scale_ is None or not self.centroids_:
            raise RuntimeError("decoder has not been fit")
        f = self._features(epochs, sampling_rate) / self.scale_
        distances = np.stack(
            [
                np.sum((f - self.centroids_[cls]) ** 2, axis=1)
                for cls in self.classes_
            ],
            axis=1,
        )
        return _softmax(-distances)


class RiemannianCentroidDecoder:
    """Log-Euclidean covariance decoder for multichannel EEG epochs.

    This is a compact research baseline, not a claim of equivalence with specialist
    Riemannian BCI libraries.
    """

    def __init__(self, regularization: float = 1e-4) -> None:
        self.regularization = float(regularization)
        self.classes_: np.ndarray = np.array([])
        self.centroids_: Dict[object, np.ndarray] = {}
        self.scale_: np.ndarray | None = None

    def _features(self, epochs: np.ndarray, sampling_rate: float) -> np.ndarray:
        del sampling_rate
        x = np.asarray(epochs, dtype=float)
        if x.ndim != 3:
            raise ValueError("epochs must be 3-D")
        features = []
        for epoch in x:
            centered = epoch - np.mean(epoch, axis=1, keepdims=True)
            cov = centered @ centered.T / max(epoch.shape[1] - 1, 1)
            trace = float(np.trace(cov))
            scale = trace / max(cov.shape[0], 1) if trace > 0 else 1.0
            cov = cov + np.eye(cov.shape[0]) * self.regularization * scale
            vals, vecs = np.linalg.eigh(cov)
            log_cov = (
                vecs * np.log(np.clip(vals, 1e-12, None))
            ) @ vecs.T
            idx = np.triu_indices(log_cov.shape[0])
            feat = log_cov[idx].copy()
            offdiag = idx[0] != idx[1]
            feat[offdiag] *= np.sqrt(2.0)
            features.append(feat)
        return np.asarray(features)

    def fit(
        self,
        epochs: np.ndarray,
        labels: np.ndarray,
        sampling_rate: float,
    ) -> "RiemannianCentroidDecoder":
        y = np.asarray(labels)
        f = self._features(epochs, sampling_rate)
        self.classes_ = np.unique(y)
        if len(self.classes_) < 2:
            raise ValueError("at least two classes are required")
        self.scale_ = np.std(f, axis=0) + 1e-6
        z = f / self.scale_
        self.centroids_ = {
            cls: np.mean(z[y == cls], axis=0) for cls in self.classes_
        }
        return self

    def predict_proba(
        self,
        epochs: np.ndarray,
        sampling_rate: float,
    ) -> np.ndarray:
        if self.scale_ is None or not self.centroids_:
            raise RuntimeError("decoder has not been fit")
        f = self._features(epochs, sampling_rate) / self.scale_
        distances = np.stack(
            [
                np.sum((f - self.centroids_[cls]) ** 2, axis=1)
                for cls in self.classes_
            ],
            axis=1,
        )
        return _softmax(-distances)


class EnsembleDecoder:
    """Probability-averaging ensemble for decoders sharing the same class set."""

    def __init__(self, decoders: Sequence[Decoder]) -> None:
        if not decoders:
            raise ValueError("decoders must not be empty")
        self.decoders = list(decoders)
        self.classes_: np.ndarray = np.array([])

    def fit(
        self,
        epochs: np.ndarray,
        labels: np.ndarray,
        sampling_rate: float,
    ) -> "EnsembleDecoder":
        for decoder in self.decoders:
            decoder.fit(epochs, labels, sampling_rate)
        self.classes_ = np.asarray(self.decoders[0].classes_)
        for decoder in self.decoders[1:]:
            if not np.array_equal(self.classes_, decoder.classes_):
                raise ValueError("ensemble decoders disagree on class ordering")
        return self

    def predict_proba(
        self,
        epochs: np.ndarray,
        sampling_rate: float,
    ) -> np.ndarray:
        arrays = [
            decoder.predict_proba(epochs, sampling_rate)
            for decoder in self.decoders
        ]
        return np.mean(np.stack(arrays, axis=0), axis=0)

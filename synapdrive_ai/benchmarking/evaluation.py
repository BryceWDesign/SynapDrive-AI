from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict

import numpy as np

from synapdrive_ai.benchmarking.dataset import EpochDataset
from synapdrive_ai.benchmarking.decoders import Decoder


@dataclass(frozen=True)
class BenchmarkReport:
    decoder: str
    n_samples: int
    n_train: int
    n_test: int
    accuracy: float
    balanced_accuracy: float
    brier_score: float
    ece: float
    coverage: float
    selective_accuracy: float
    abstain_threshold: float
    classes: list[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _split_indices(
    labels: np.ndarray,
    test_fraction: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    if not 0.05 <= test_fraction <= 0.5:
        raise ValueError("test_fraction must be between 0.05 and 0.5")
    rng = np.random.default_rng(seed)
    train, test = [], []
    for cls in np.unique(labels):
        idx = np.flatnonzero(labels == cls)
        if len(idx) < 2:
            raise ValueError("each class needs at least two samples")
        idx = idx.copy()
        rng.shuffle(idx)
        n_test = max(1, int(round(len(idx) * test_fraction)))
        n_test = min(n_test, len(idx) - 1)
        test.extend(idx[:n_test])
        train.extend(idx[n_test:])
    return np.array(sorted(train)), np.array(sorted(test))


def expected_calibration_error(
    confidence: np.ndarray,
    correct: np.ndarray,
    bins: int = 10,
) -> float:
    edges = np.linspace(0, 1, bins + 1)
    total = len(confidence)
    value = 0.0
    for i in range(bins):
        upper = (
            confidence < edges[i + 1]
            if i < bins - 1
            else confidence <= edges[i + 1]
        )
        mask = (confidence >= edges[i]) & upper
        count = int(np.sum(mask))
        if count:
            mean_conf = float(np.mean(confidence[mask]))
            mean_correct = float(np.mean(correct[mask]))
            value += count / total * abs(mean_conf - mean_correct)
    return float(value)


def evaluate_decoder(
    decoder: Decoder,
    dataset: EpochDataset,
    *,
    test_fraction: float = 0.25,
    seed: int = 7,
    abstain_threshold: float = 0.55,
) -> BenchmarkReport:
    y = np.asarray(dataset.labels)
    train_idx, test_idx = _split_indices(y, test_fraction, seed)
    decoder.fit(
        dataset.epochs[train_idx],
        y[train_idx],
        dataset.sampling_rate,
    )
    probs = decoder.predict_proba(
        dataset.epochs[test_idx],
        dataset.sampling_rate,
    )
    classes = np.asarray(decoder.classes_)
    pred = classes[np.argmax(probs, axis=1)]
    truth = y[test_idx]
    correct = pred == truth
    confidence = np.max(probs, axis=1)
    accuracy = float(np.mean(correct))
    per_class = []
    for cls in classes:
        mask = truth == cls
        if np.any(mask):
            per_class.append(float(np.mean(correct[mask])))
    balanced = float(np.mean(per_class)) if per_class else 0.0
    onehot = np.zeros_like(probs)
    class_to_idx = {cls: i for i, cls in enumerate(classes)}
    for row, cls in enumerate(truth):
        onehot[row, class_to_idx[cls]] = 1.0
    brier = float(np.mean(np.sum((probs - onehot) ** 2, axis=1)))
    ece = expected_calibration_error(confidence, correct.astype(float))
    accepted = confidence >= abstain_threshold
    coverage = float(np.mean(accepted))
    selective_accuracy = (
        float(np.mean(correct[accepted])) if np.any(accepted) else 0.0
    )
    return BenchmarkReport(
        decoder=type(decoder).__name__,
        n_samples=len(y),
        n_train=len(train_idx),
        n_test=len(test_idx),
        accuracy=round(accuracy, 6),
        balanced_accuracy=round(balanced, 6),
        brier_score=round(brier, 6),
        ece=round(ece, 6),
        coverage=round(coverage, 6),
        selective_accuracy=round(selective_accuracy, 6),
        abstain_threshold=float(abstain_threshold),
        classes=[str(c) for c in classes.tolist()],
    )


def run_arena(
    dataset: EpochDataset,
    *,
    test_fraction: float = 0.25,
    seed: int = 7,
    abstain_threshold: float = 0.55,
) -> list[BenchmarkReport]:
    """Evaluate all built-in decoders under one deterministic split configuration."""
    from synapdrive_ai.benchmarking.decoders import (
        EnsembleDecoder,
        RiemannianCentroidDecoder,
        SpectralCentroidDecoder,
    )

    decoders = [
        SpectralCentroidDecoder(),
        RiemannianCentroidDecoder(),
        EnsembleDecoder(
            [SpectralCentroidDecoder(), RiemannianCentroidDecoder()]
        ),
    ]
    reports = [
        evaluate_decoder(
            decoder,
            dataset,
            test_fraction=test_fraction,
            seed=seed,
            abstain_threshold=abstain_threshold,
        )
        for decoder in decoders
    ]
    return sorted(
        reports,
        key=lambda report: (
            report.balanced_accuracy,
            report.selective_accuracy,
            -report.brier_score,
        ),
        reverse=True,
    )

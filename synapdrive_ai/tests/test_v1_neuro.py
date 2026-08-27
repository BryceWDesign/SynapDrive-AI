from __future__ import annotations

import numpy as np
import pytest

from synapdrive_ai.neuro.drift import FeatureDriftMonitor
from synapdrive_ai.neuro.errp import ErrPFeatureExtractor, ErrPLDAClassifier
from synapdrive_ai.neuro.fusion import ModalityEvidence, WeightedEvidenceFusion
from synapdrive_ai.neuro.signal_quality import SignalQualityAnalyzer
from synapdrive_ai.neuro.uncertainty import (
    ReliabilityCalibrator,
    estimate_uncertainty,
    normalize_distribution,
    packet_distribution,
)


def test_distribution_normalizes():
    p = normalize_distribution({"a": 2, "b": 1})
    assert abs(sum(p.values()) - 1.0) < 1e-12


def test_packet_distribution_has_unknown_mass():
    p = packet_distribution({"intent": "left", "confidence": 0.8})
    assert p["left"] == pytest.approx(0.8)
    assert p["unknown"] == pytest.approx(0.2)


def test_uncertainty_lower_for_decisive_distribution():
    decisive = estimate_uncertainty({"a": 0.99, "b": 0.01}).combined
    ambiguous = estimate_uncertainty({"a": 0.51, "b": 0.49}).combined
    assert decisive < ambiguous


def test_ensemble_disagreement_contributes_uncertainty():
    same = estimate_uncertainty({"a": 0.8, "b": 0.2}, [{"a": 0.8, "b": 0.2}, {"a": 0.8, "b": 0.2}])
    split = estimate_uncertainty(
        {"a": 0.5, "b": 0.5},
        [{"a": 0.99, "b": 0.01}, {"a": 0.01, "b": 0.99}],
    )
    assert split.disagreement > same.disagreement


def test_calibrator_requires_fit():
    with pytest.raises(RuntimeError):
        ReliabilityCalibrator().transform(0.8)


def test_calibrator_maps_to_empirical_accuracy():
    cal = ReliabilityCalibrator(n_bins=2).fit([0.1, 0.2, 0.8, 0.9], [False, False, True, True])
    assert cal.transform(0.85) == pytest.approx(1.0)
    assert cal.transform(0.15) == pytest.approx(0.0)


def test_signal_quality_good_clean_signal():
    sr = 256
    t = np.arange(sr * 2) / sr
    x = np.sin(2 * np.pi * 10 * t) + 0.1 * np.sin(2 * np.pi * 20 * t)
    report = SignalQualityAnalyzer(sr).analyze(x)
    assert report.score > 0.8
    assert report.state == "good"


def test_signal_quality_detects_nan():
    x = np.ones(512)
    x[::2] = np.nan
    report = SignalQualityAnalyzer(256).analyze(x)
    assert "non-finite-samples" in report.issues
    assert report.score < 0.8


def test_signal_quality_detects_flatline():
    report = SignalQualityAnalyzer(256).analyze(np.ones(512))
    assert "flatline" in report.issues
    assert report.state in {"unreliable", "invalid", "degraded"}


def test_signal_quality_detects_dropout():
    sr = 256
    t = np.arange(512) / sr
    x = np.sin(2 * np.pi * 10 * t)
    x[:300] = 0
    report = SignalQualityAnalyzer(sr).analyze(x)
    assert "dropout" in report.issues


def test_fusion_prefers_reliable_modality():
    result = WeightedEvidenceFusion().fuse([
        ModalityEvidence("eeg", {"left": 0.9, "right": 0.1}, 0.2),
        ModalityEvidence("gaze", {"left": 0.1, "right": 0.9}, 1.0),
    ])
    assert result.intent == "right"
    assert result.weights["gaze"] > result.weights["eeg"]


def test_fusion_rejects_zero_reliability():
    with pytest.raises(ValueError):
        WeightedEvidenceFusion().fuse([ModalityEvidence("eeg", {"left": 1.0}, 0.0)])


def test_drift_monitor_detects_far_outlier():
    rng = np.random.default_rng(2)
    baseline = rng.normal(0, 0.2, (100, 3))
    monitor = FeatureDriftMonitor().fit(baseline)
    assert monitor.evaluate([8, 8, 8]).drifted is True


def test_errp_feature_extractor_windows():
    sr = 100
    x = np.zeros(sr)
    x[20:35] = -2.0
    x[35:60] = 1.0
    f = ErrPFeatureExtractor(sr).extract(x)
    assert f.negative_peak == pytest.approx(-2.0)
    assert f.positive_peak == pytest.approx(1.0)


def test_errp_lda_learns_supplied_calibration():
    rng = np.random.default_rng(4)
    x0 = rng.normal(0, 0.1, (20, 4))
    x1 = rng.normal(2, 0.1, (20, 4))
    x = np.vstack([x0, x1])
    y = [0] * 20 + [1] * 20
    clf = ErrPLDAClassifier().fit(x, y)
    assert clf.predict([2, 2, 2, 2]) == 1
    assert clf.predict([0, 0, 0, 0]) == 0


def test_errp_classifier_requires_both_classes():
    with pytest.raises(ValueError):
        ErrPLDAClassifier().fit(np.zeros((4, 4)), [0, 0, 0, 0])

from __future__ import annotations

import numpy as np

from synapdrive_ai.adaptation.guarded import GuardedThresholdAdapter
from synapdrive_ai.benchmarking.dataset import EpochDataset, load_npz_dataset
from synapdrive_ai.benchmarking.decoders import (
    EnsembleDecoder,
    RiemannianCentroidDecoder,
    SpectralCentroidDecoder,
)
from synapdrive_ai.benchmarking.evaluation import evaluate_decoder
from synapdrive_ai.stress.campaign import StressCampaign
from synapdrive_ai.stress.faults import FaultInjector


def _dataset(n_per_class=24, sr=128.0):
    rng = np.random.default_rng(11)
    n = int(sr)
    t = np.arange(n) / sr
    epochs, labels = [], []
    for label, freq in [("left", 10.0), ("right", 20.0)]:
        for _ in range(n_per_class):
            ch1 = np.sin(2 * np.pi * freq * t) + rng.normal(0, 0.12, n)
            ch2 = 0.7 * np.sin(2 * np.pi * freq * t + 0.3) + rng.normal(0, 0.12, n)
            epochs.append(np.stack([ch1, ch2]))
            labels.append(label)
    return EpochDataset(np.asarray(epochs), np.asarray(labels), sr, ["C3", "C4"], "test-generated")


def test_npz_dataset_contract_roundtrip(tmp_path):
    ds = _dataset(4)
    p = tmp_path / "d.npz"
    np.savez(
        p,
        X=ds.epochs,
        y=ds.labels,
        sampling_rate=np.array([ds.sampling_rate]),
        channel_names=np.array(ds.channel_names),
    )
    loaded = load_npz_dataset(p)
    assert loaded.epochs.shape == ds.epochs.shape
    assert loaded.channel_names == ["C3", "C4"]


def test_spectral_decoder_learns_frequency_classes():
    ds = _dataset()
    report = evaluate_decoder(SpectralCentroidDecoder(), ds, seed=3)
    assert report.accuracy > 0.9
    assert report.n_test > 0


def test_riemannian_decoder_outputs_probabilities():
    ds = _dataset()
    decoder = RiemannianCentroidDecoder().fit(ds.epochs, ds.labels, ds.sampling_rate)
    p = decoder.predict_proba(ds.epochs[:3], ds.sampling_rate)
    assert p.shape == (3, 2)
    assert np.allclose(np.sum(p, axis=1), 1.0)


def test_ensemble_benchmark_metrics_are_bounded():
    ds = _dataset()
    decoder = EnsembleDecoder([SpectralCentroidDecoder(), RiemannianCentroidDecoder()])
    report = evaluate_decoder(decoder, ds)
    assert 0 <= report.accuracy <= 1
    assert 0 <= report.balanced_accuracy <= 1
    assert 0 <= report.ece <= 1
    assert 0 <= report.coverage <= 1


def test_guarded_adapter_promotes_safer_better_threshold():
    rows = [
        {"confidence": 0.9, "safe": True},
        {"confidence": 0.8, "safe": True},
        {"confidence": 0.6, "safe": False},
        {"confidence": 0.55, "safe": False},
    ]
    adapter = GuardedThresholdAdapter(0.45)
    decision = adapter.evaluate_candidate(0.7, rows)
    assert decision.promoted is True
    assert adapter.threshold == 0.7


def test_guarded_adapter_rejects_more_unsafe_accepts():
    rows = [
        {"confidence": 0.9, "safe": True},
        {"confidence": 0.6, "safe": False},
    ]
    adapter = GuardedThresholdAdapter(0.7)
    decision = adapter.evaluate_candidate(0.5, rows)
    assert decision.promoted is False
    assert adapter.threshold == 0.7


def test_fault_injector_is_seed_deterministic():
    x = np.ones(100)
    a = FaultInjector(5).dropout(x, 0.2)
    b = FaultInjector(5).dropout(x, 0.2)
    assert np.array_equal(a.signal, b.signal)
    assert a.metadata == b.metadata


def test_fault_dropout_writes_zeros():
    out = FaultInjector(1).dropout(np.ones(100), 0.5)
    assert np.sum(out.signal == 0) >= 50


def test_fault_channel_swap():
    x = np.vstack([np.zeros(8), np.ones(8)])
    out = FaultInjector().channel_swap(x, 0, 1).signal
    assert np.all(out[0] == 1)
    assert np.all(out[1] == 0)


def test_stress_campaign_enforces_low_quality_block():
    clean = np.sin(2 * np.pi * 10 * np.arange(512) / 256)
    bad = np.zeros(512)
    campaign = StressCampaign(256, min_quality=0.5)
    report = campaign.run([("clean", clean), ("flatline", bad)], lambda _sig, q: q < 0.5)
    assert report.invariant_failures == 0
    assert report.total_trials == 2


def test_decoder_arena_ranks_all_builtins():
    from synapdrive_ai.benchmarking.evaluation import run_arena

    reports = run_arena(_dataset())
    assert len(reports) == 3
    assert {report.decoder for report in reports} == {
        "SpectralCentroidDecoder",
        "RiemannianCentroidDecoder",
        "EnsembleDecoder",
    }


def test_epoch_recording_uses_explicit_events():
    from synapdrive_ai.benchmarking.epoching import LabeledEvent, epoch_recording
    from synapdrive_ai.neuro.eeg_loader import EEGLoader

    sr = 100.0
    data = np.vstack([np.arange(500), np.arange(500) * 2.0])
    recording = EEGLoader(sr).load_array(data, channel_names=["C3", "C4"])
    dataset = epoch_recording(
        recording,
        [LabeledEvent(1.0, "left"), LabeledEvent(3.0, "right")],
        tmin_s=0.0,
        tmax_s=0.5,
        channels=["C3"],
    )
    assert dataset.epochs.shape == (2, 1, 50)
    assert dataset.labels.tolist() == ["left", "right"]


def test_qualified_decoder_adapter_bridges_labeled_data_to_action_packet():
    from synapdrive_ai.benchmarking.runtime_adapter import QualifiedDecoderAdapter

    ds = _dataset()
    adapter = QualifiedDecoderAdapter(
        SpectralCentroidDecoder(),
        ds,
        {"left": "move_left", "right": "move_right"},
        seed=3,
    )
    assert adapter.qualification.qualified is True
    packet = adapter(ds.epochs[0], {"sampling_rate": ds.sampling_rate})
    assert packet["intent"] == "move_left"
    assert packet["analysis_only"] is False
    assert packet["neural_decode_performed"] is True
    assert 0.0 <= packet["confidence"] <= 1.0


def test_qualified_decoder_adapter_abstains_on_sampling_rate_mismatch():
    from synapdrive_ai.benchmarking.runtime_adapter import QualifiedDecoderAdapter

    ds = _dataset()
    adapter = QualifiedDecoderAdapter(
        SpectralCentroidDecoder(),
        ds,
        {"left": "move_left", "right": "move_right"},
        seed=3,
    )
    packet = adapter(ds.epochs[0], {"sampling_rate": ds.sampling_rate + 1})
    assert packet["intent"] == "unknown"
    assert packet["analysis_only"] is True
    assert "sampling-rate mismatch" in packet["abstention_reason"]


def test_qualified_decoder_requires_action_mapping_for_all_classes():
    from synapdrive_ai.benchmarking.runtime_adapter import QualifiedDecoderAdapter

    ds = _dataset()
    adapter = QualifiedDecoderAdapter(
        SpectralCentroidDecoder(),
        ds,
        {"left": "move_left"},
        seed=3,
    )
    assert adapter.qualification.qualified is False
    assert "unmapped-decoder-classes:right" in adapter.qualification.reason

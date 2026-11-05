from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pytest

from synapdrive_ai.acquisition import StreamDecoder
from synapdrive_ai.assurance.checkpoint import create_checkpoint, verify_checkpoint
from synapdrive_ai.assurance.hashchain import EvidenceHashChain
from synapdrive_ai.benchmarking.dataset import EpochDataset
from synapdrive_ai.benchmarking.decoders import SpectralCentroidDecoder
from synapdrive_ai.benchmarking.evaluation import evaluate_decoder
from synapdrive_ai.decoding import AcquisitionIdentity, EEGDecoder, metrics
from synapdrive_ai.pipeline import SynapDrivePipeline

ASSETS = Path(__file__).parents[1] / "assets/recorded_eeg.npz"


@pytest.fixture
def recorded():
    with np.load(ASSETS, allow_pickle=False) as d:
        ident = json.loads(str(d["identity"]))
        ident["channels"] = tuple(ident["channels"])
        subject = d["subject"] == "S004"
        return d["X"][subject], d["y"][subject], d["run"][subject], AcquisitionIdentity(**ident)


@pytest.fixture
def trained(recorded):
    x, y, run, identity = recorded
    model = EEGDecoder(identity).train(x[run == 4], y[run == 4])
    model.calibrate(x[run == 8], y[run == 8])
    model.qualify(x[run == 12], y[run == 12])
    return model


def test_real_eeg_training_calibration_and_exact_heldout_inference(recorded, trained):
    x, y, run, identity = recorded
    report = metrics(trained, x[run == 12], y[run == 12])
    assert report["n"] == 30
    assert trained.qualification["qualified"]
    assert report["balanced_accuracy"] == pytest.approx(0.6130952380952381)
    pipe = SynapDrivePipeline(False)
    for epoch in x[run == 12]:
        pipe.run_intent_packet(
            trained.packet(
                epoch,
                identity.to_dict(),
                {"left": "move_left", "right": "move_right", "rest": "no_command"},
            )
        )
    assert len(pipe.get_action_log()) == 7


def test_f10_exact_acquisition_identity_rejects_channel_units_and_processing(recorded, trained):
    x, _, _, identity = recorded
    mapping = {"left": "move_left", "right": "move_right", "rest": "no_command"}
    for field, value in [
        ("channels", list(reversed(identity.channels))),
        ("units", "uV"),
        ("reference", "different"),
        ("device", "different"),
        ("preprocessing", "different"),
        ("samples", 479),
    ]:
        metadata = identity.to_dict()
        metadata[field] = value
        packet = trained.packet(x[0], metadata, mapping)
        assert packet["analysis_only"]
        assert "identity mismatch" in packet["abstention_reason"]


def test_f10_audit_data_is_never_used_to_refit_or_calibrate(recorded, trained):
    x, y, run, _ = recorded
    frozen = trained.artifact_id()
    with pytest.raises(ValueError, match="already consumed"):
        trained.qualify(x[run == 12], y[run == 12])
    with pytest.raises(ValueError):
        trained.calibrate(x[run == 12], y[run == 12])
    assert trained.artifact_id() == frozen
    fresh = EEGDecoder(trained.identity).train(x[run == 4], y[run == 4])
    with pytest.raises(ValueError, match="overlaps"):
        fresh.qualify(x[run == 4], y[run == 4])


def test_artifact_roundtrip_and_mutated_weights_cannot_keep_qualification(
    tmp_path, trained, recorded
):
    x, _, _, identity = recorded
    file = tmp_path / "decoder.npz"
    trained.save(file)
    sha = hashlib.sha256(file.read_bytes()).hexdigest()
    loaded = EEGDecoder.load(file, expected_sha256=sha)
    assert loaded.artifact_id() == trained.artifact_id()
    assert np.array_equal(loaded.predict_proba(x[:3]), trained.predict_proba(x[:3]))
    with pytest.raises(ValueError, match="checksum"):
        EEGDecoder.load(file, expected_sha256="0" * 64)
    loaded.coef[0, 0] += 0.1
    packet = loaded.packet(x[0], identity.to_dict(), {})
    assert packet["analysis_only"]
    assert "changed" in packet["abstention_reason"]


def test_expiry_and_quality_faults_abstain(recorded, trained):
    x, _, _, identity = recorded
    mapping = {"left": "move_left", "right": "move_right", "rest": "no_command"}
    assert trained.packet(np.zeros_like(x[0]), identity.to_dict(), mapping)["analysis_only"]
    trained.qualification["expires_utc"] = time.time() - 1
    assert trained.packet(x[0], identity.to_dict(), mapping)["analysis_only"]


def test_stream_clock_age_gaps_and_replayed_windows(recorded, trained):
    x, _, _, identity = recorded
    end = 100.0
    t = end - np.arange(479, -1, -1) / 160
    mapping = {"left": "move_left", "right": "move_right", "rest": "no_command"}
    stream = StreamDecoder(trained, clock=lambda: end + 0.1)
    stream.packet(x[0], t, identity.to_dict(), mapping)
    assert "replayed" in stream.packet(x[0], t, identity.to_dict(), mapping)["abstention_reason"]
    for timestamps in [t - 10, t + 10, t[::-1], t + np.where(np.arange(480) > 200, 0.1, 0)]:
        out = StreamDecoder(trained, clock=lambda: end + 0.1).packet(
            x[0], timestamps, identity.to_dict(), mapping
        )
        assert out["analysis_only"]


def test_duplicate_epochs_across_train_test_groups_are_rejected():
    x = np.random.default_rng(1).normal(size=(8, 2, 128))
    x[4:] = x[:4]
    d = EpochDataset(
        x,
        np.array(["a", "b", "a", "b"] * 2),
        128,
        ["a", "b"],
        "duplicate-negative-control",
        groups=np.array([0] * 4 + [1] * 4),
    )
    with pytest.raises(ValueError, match="duplicate"):
        evaluate_decoder(SpectralCentroidDecoder(), d)


def test_signed_checkpoint_requires_retained_run_count_head_and_key():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    chain = EvidenceHashChain()
    chain.append({"event": 1})
    chain.append({"event": 2})
    key = Ed25519PrivateKey.generate()
    checkpoint = create_checkpoint(chain.entries(), "run-one", key)
    assert verify_checkpoint(chain.entries(), checkpoint, "run-one", key.public_key())
    assert not verify_checkpoint(chain.entries()[:1], checkpoint, "run-one", key.public_key())
    assert not verify_checkpoint(chain.entries(), checkpoint, "run-two", key.public_key())
    assert not verify_checkpoint(
        chain.entries(), checkpoint, "run-one", Ed25519PrivateKey.generate().public_key()
    )


def test_actual_decoder_update_uses_evaluator_owned_metrics_and_refuses_reused_audit(recorded):
    from synapdrive_ai.adaptation.decoder_updates import DecoderUpdates

    x, y, run, identity = recorded
    train = run == 4
    calibration = run == 8
    audit = run == 12
    baseline = EEGDecoder(identity).train(x[train], y[train])
    candidate = EEGDecoder(identity).train(x[train], y[train])
    candidate.calibrate(x[calibration], y[calibration])
    updates = DecoderUpdates(baseline)
    artifact = updates.stage(candidate, ("feedback-cycle",))
    evidence = updates.evaluate(
        artifact, x[audit], y[audit], trial_ids=[f"locked/{i}" for i in range(sum(audit))]
    )
    if evidence["promotion"]["eligible"]:
        updates.promote(artifact)
        assert updates.lifecycle.active == artifact
        assert updates.contradict("feedback-cycle") == baseline.artifact_id()
    else:
        with pytest.raises(ValueError):
            updates.promote(artifact)
    with pytest.raises(ValueError, match="already consumed"):
        updates.evaluate(
            artifact, x[audit], y[audit], trial_ids=[f"locked/{i}" for i in range(sum(audit))]
        )


def test_supervised_model_promotion_and_rollback_on_independent_spatial_fixture():
    from copy import deepcopy

    from synapdrive_ai.adaptation.decoder_updates import DecoderUpdates

    rng = np.random.default_rng(918)
    identity = AcquisitionIdentity(
        tuple(f"C{i}" for i in range(6)), 128.0, 256, device="synthetic-spatial-verification"
    )

    def dataset():
        x, y = [], []
        for label, channel in [("left", 0), ("rest", 2), ("right", 4)]:
            for _ in range(20):
                epoch = rng.normal(0, 0.1e-5, (6, 256))
                epoch[channel] += rng.normal(0, 3e-5, 256)
                x.append(epoch)
                y.append(label)
        return np.asarray(x), np.asarray(y)

    train, calibration, audit = dataset(), dataset(), dataset()
    candidate = EEGDecoder(identity).train(*train)
    candidate.calibrate(*calibration)
    baseline = deepcopy(candidate)
    baseline.coef[:] = 0
    baseline.intercept[:] = -20
    baseline.intercept[0] = 20  # Independent wrong-label control, not a physiological model.
    updates = DecoderUpdates(baseline)
    artifact = updates.stage(candidate, ("ground-truth-record",))
    evidence = updates.evaluate(artifact, *audit, trial_ids=[f"fixture/{i}" for i in range(60)])
    assert evidence["qualification"]["report"]["balanced_accuracy"] > 0.95
    assert evidence["promotion"]["eligible"]
    updates.promote(artifact)
    assert updates.lifecycle.active == artifact
    assert updates.contradict("ground-truth-record") == baseline.artifact_id()

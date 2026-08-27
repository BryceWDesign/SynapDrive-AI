from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pytest

from synapdrive_ai.agi.cognitive_optimizer import CognitiveOptimizer
from synapdrive_ai.bci.intent_generator import generate_intent
from synapdrive_ai.benchmarking.dataset import EpochDataset
from synapdrive_ai.benchmarking.decoders import SpectralCentroidDecoder
from synapdrive_ai.benchmarking.runtime_adapter import QualifiedDecoderAdapter
from synapdrive_ai.cognition.world_model import WorldModel
from synapdrive_ai.neuro.eeg_loader import EEGLoader, EEGRecording
from synapdrive_ai.neuro.session_analyzer import SessionAnalyzer
from synapdrive_ai.pipeline import SynapDrivePipeline
from synapdrive_ai.vision.visual_inference import VisualInferenceEngine


def test_declared_visual_context_has_no_random_certainty() -> None:
    engine = VisualInferenceEngine()
    first = engine.infer("road")
    second = engine.infer("road")
    assert first == second
    assert first["certainty"] == 1.0
    assert first["evidence_kind"] == "declared-label"
    assert first["model_used"] is False


def test_visual_context_does_not_boost_command_confidence() -> None:
    optimizer = CognitiveOptimizer()
    packet = generate_intent("move left")
    without_visual = optimizer.optimize(packet)
    with_visual = optimizer.optimize(packet, image_label="road")
    assert with_visual["confidence"] == without_visual["confidence"]


def test_unmodeled_world_action_fails_closed() -> None:
    prediction = WorldModel().predict("invented_action")
    assert prediction.feasible is False
    assert prediction.predicted_risk == 1.0
    assert prediction.after == prediction.before


def test_analysis_only_packet_cannot_reach_actuation() -> None:
    pipe = SynapDrivePipeline(simulate_delay=False)
    packet = {
        "intent": "move_left",
        "confidence": 1.0,
        "source": "analysis",
        "analysis_only": True,
        "signal_quality": 1.0,
    }
    out = pipe.run_intent_packet(packet)
    assert out["status"] == "blocked"
    assert "analysis-only-inference" in out["reason"]
    assert pipe.get_action_log() == []


def test_session_analyzer_without_decoder_is_analysis_only() -> None:
    sr = 128.0
    t = np.arange(256) / sr
    signal = np.sin(2 * np.pi * 10 * t)
    recording = EEGLoader(sr).load_array(signal, channel_names=["C3"])
    report = SessionAnalyzer(channel="C3", window_s=1.0, step_s=1.0).run(recording)
    assert report.n_epochs == 2
    assert all(epoch.pipeline_status == "blocked" for epoch in report.epochs)
    assert all(epoch.pipeline_confidence == 0.0 for epoch in report.epochs)


def _install_fake_brainflow(monkeypatch: pytest.MonkeyPatch) -> None:
    board_mod = types.ModuleType("brainflow.board_shim")

    class Params:
        serial_port = ""

    class Board:
        def __init__(self, board_id, params):
            self.board_id = board_id
            self.params = params

        def prepare_session(self):
            return None

        def start_stream(self):
            return None

        def get_board_data(self):
            t = np.arange(256) / 256.0
            return np.stack([np.sin(2 * np.pi * 10 * t), np.sin(2 * np.pi * 12 * t)])

        def stop_stream(self):
            return None

        def release_session(self):
            return None

        @staticmethod
        def get_eeg_channels(_board_id):
            return [0, 1]

        @staticmethod
        def get_sampling_rate(_board_id):
            return 256

    setattr(board_mod, "BoardShim", Board)
    setattr(board_mod, "BrainFlowInputParams", Params)
    pkg = types.ModuleType("brainflow")
    monkeypatch.setitem(sys.modules, "brainflow", pkg)
    monkeypatch.setitem(sys.modules, "brainflow.board_shim", board_mod)


def test_brainflow_without_decoder_abstains(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_brainflow(monkeypatch)
    import synapdrive_ai.integrations.brainflow_adapter as module

    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)
    source = module.BrainFlowIntentSource(stream_seconds=0.001)
    packet = source.next_intent_packet()
    assert packet["intent"] == "unknown"
    assert packet["confidence"] == 0.0
    assert packet["decoder_status"] == "not-configured"
    assert packet["analysis_only"] is True


def test_brainflow_explicit_decoder_is_only_decoder_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_brainflow(monkeypatch)
    import synapdrive_ai.integrations.brainflow_adapter as module

    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)

    def decoder(data, metadata):
        assert data.shape == (2, 256)
        assert metadata["sampling_rate"] == 256.0
        return {
            "intent": "move_left",
            "confidence": 0.8,
            "probabilities": {"move_left": 0.8, "unknown": 0.2},
            "source": "test-decoder",
        }

    source = module.BrainFlowIntentSource(stream_seconds=0.001, decoder=decoder)
    packet = source.next_intent_packet()
    assert packet["intent"] == "move_left"
    assert packet["confidence"] == 0.8
    assert packet["decoder_status"] == "configured"
    assert packet["source"] == "test-decoder"


def _install_fake_lsl(monkeypatch: pytest.MonkeyPatch, sampling_rate: float = 256.0) -> None:
    mod = types.ModuleType("pylsl")

    class Info:
        def name(self):
            return "unit-test-stream"

        def type(self):
            return "EEG"

        def nominal_srate(self):
            return sampling_rate

    class Inlet:
        def __init__(self, info, max_chunklen=512):
            self.info = info
            self.max_chunklen = max_chunklen
            self.calls = 0

        def pull_chunk(self, timeout=0.2, max_samples=512):
            self.calls += 1
            if self.calls == 1:
                t = np.arange(64) / 256.0
                samples = np.stack(
                    [np.sin(2 * np.pi * 10 * t), np.sin(2 * np.pi * 12 * t)], axis=1
                )
                return samples.tolist(), t.tolist()
            return [], []

    def resolve_stream(_prop, _value, timeout=5.0):
        del timeout
        return [Info()]

    setattr(mod, "StreamInlet", Inlet)
    setattr(mod, "resolve_stream", resolve_stream)
    monkeypatch.setitem(sys.modules, "pylsl", mod)


def test_lsl_without_decoder_abstains(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_lsl(monkeypatch)
    import synapdrive_ai.integrations.lsl_adapter as module

    ticks = iter([0.0, 0.0, 1.0])
    monkeypatch.setattr(module.time, "monotonic", lambda: next(ticks, 1.0))
    source = module.LSLIntentSource(snapshot_seconds=0.1)
    packet = source.next_intent_packet()
    assert packet["intent"] == "unknown"
    assert packet["confidence"] == 0.0
    assert packet["decoder_status"] == "not-configured"
    assert packet["analysis_only"] is True


def test_repository_contains_no_retired_fabricated_routes() -> None:
    root = Path(__file__).resolve().parents[2]
    retired = ("Tesla" + "AutonomySystem", "SpaceX" + "CommandCore", "Hyperloop" + "Ops")
    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for marker in retired:
            assert marker not in text, f"retired fabricated route {marker!r} remains in {path}"


def test_qualified_decoder_adapter_connects_to_session_analyzer() -> None:
    sr = 128.0
    n = 128
    times = np.arange(n, dtype=float) / sr
    rng = np.random.default_rng(123)
    epochs = []
    labels = []
    for label, frequency in (("left", 10.0), ("right", 20.0)):
        for _ in range(12):
            signal = np.sin(2.0 * np.pi * frequency * times)
            signal += rng.normal(0.0, 0.01, n)
            epochs.append(signal[None, :])
            labels.append(label)
    dataset = EpochDataset(
        epochs=np.asarray(epochs, dtype=float),
        labels=np.asarray(labels),
        sampling_rate=sr,
        channel_names=["C3"],
        source="deterministic-synthetic-verification",
    )
    adapter = QualifiedDecoderAdapter(
        SpectralCentroidDecoder(),
        dataset,
        {"left": "move_left", "right": "move_right"},
    )
    assert adapter.qualification.qualified is True

    recording = EEGRecording(
        channels=["C3"],
        data=np.sin(2.0 * np.pi * 10.0 * times)[None, :],
        sampling_rate=sr,
        duration_s=1.0,
        source_file="synthetic-verification",
    )
    report = SessionAnalyzer(
        channel="C3",
        window_s=1.0,
        step_s=1.0,
        decoder=adapter,
    ).run(recording)
    assert report.n_epochs == 1
    assert report.n_success == 1
    assert report.epochs[0].pipeline_status == "success"
    assert report.epochs[0].pipeline_confidence >= adapter.policy.abstain_threshold

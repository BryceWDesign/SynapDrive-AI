from __future__ import annotations

import numpy as np
import pytest

from synapdrive_ai.neuro.band_analyzer import BANDS, BandPowerAnalyzer
from synapdrive_ai.neuro.eeg_loader import EEGLoader, EEGRecording
from synapdrive_ai.neuro.session_analyzer import SessionAnalyzer
from synapdrive_ai.neuro.task_planner import ExecutorBridge, TaskPlan, TaskStep


SR = 256.0
DURATION = 2.0
N = int(SR * DURATION)
T = np.linspace(0, DURATION, N, endpoint=False)


def _make_signal(freq_hz: float, noise: float = 0.02) -> np.ndarray:
    return np.sin(2 * np.pi * freq_hz * T) + np.random.default_rng(42).normal(0, noise, N)


def _motor_signal() -> np.ndarray:
    return (
        0.1 * np.sin(2 * np.pi * 10 * T)
        + 1.5 * np.sin(2 * np.pi * 20 * T)
        + 0.8 * np.sin(2 * np.pi * 40 * T)
        + np.random.default_rng(0).normal(0, 0.02, N)
    )


def _alpha_signal() -> np.ndarray:
    return (
        2.0 * np.sin(2 * np.pi * 10 * T)
        + 0.1 * np.sin(2 * np.pi * 20 * T)
        + np.random.default_rng(1).normal(0, 0.02, N)
    )


class TestBandPowerAnalyzer:
    def test_returns_all_bands(self):
        analyzer = BandPowerAnalyzer(sampling_rate=SR)
        result = analyzer.analyze(_make_signal(10.0))
        assert set(result.absolute.keys()) == set(BANDS.keys())
        assert set(result.relative.keys()) == set(BANDS.keys())

    def test_relative_power_sums_to_one(self):
        analyzer = BandPowerAnalyzer(sampling_rate=SR)
        result = analyzer.analyze(_make_signal(10.0))
        assert abs(sum(result.relative.values()) - 1.0) < 1e-6

    def test_confidence_in_range(self):
        analyzer = BandPowerAnalyzer(sampling_rate=SR)
        for freq in (6, 10, 20, 40):
            result = analyzer.analyze(_make_signal(freq))
            assert 0.0 <= result.confidence <= 1.0

    def test_motor_signal_classified_motor(self):
        analyzer = BandPowerAnalyzer(sampling_rate=SR)
        result = analyzer.analyze(_motor_signal())
        assert result.intent_class == "motor"

    def test_alpha_signal_classified_unclear(self):
        analyzer = BandPowerAnalyzer(sampling_rate=SR)
        result = analyzer.analyze(_alpha_signal())
        assert result.intent_class == "unclear"

    def test_motor_signal_higher_confidence_than_alpha(self):
        analyzer = BandPowerAnalyzer(sampling_rate=SR)
        motor_conf = analyzer.analyze(_motor_signal()).confidence
        alpha_conf = analyzer.analyze(_alpha_signal()).confidence
        assert motor_conf > alpha_conf

    def test_short_signal_returns_zero_result(self):
        analyzer = BandPowerAnalyzer(sampling_rate=SR)
        result = analyzer.analyze(np.array([0.1, 0.2]))
        assert result.confidence == 0.0
        assert result.intent_class == "unclear"

    def test_engagement_ratio_positive(self):
        analyzer = BandPowerAnalyzer(sampling_rate=SR)
        result = analyzer.analyze(_motor_signal())
        assert result.engagement_ratio > 0.0


class TestEEGLoader:
    def test_load_1d_array(self):
        loader = EEGLoader(sampling_rate=SR)
        recording = loader.load_array(_make_signal(10.0))
        assert recording.n_channels == 1
        assert recording.n_samples == N
        assert recording.sampling_rate == SR

    def test_load_2d_array(self):
        loader = EEGLoader(sampling_rate=SR)
        data = np.stack([_make_signal(10.0), _make_signal(20.0)])
        recording = loader.load_array(data)
        assert recording.n_channels == 2
        assert recording.n_samples == N

    def test_channel_lookup_by_name(self):
        loader = EEGLoader(sampling_rate=SR)
        data = np.stack([_make_signal(10.0), _make_signal(20.0)])
        recording = loader.load_array(data, channel_names=["C3", "C4"])
        ch = recording.channel("C3")
        assert len(ch) == N

    def test_channel_lookup_case_insensitive(self):
        loader = EEGLoader(sampling_rate=SR)
        recording = loader.load_array(_make_signal(10.0), channel_names=["Cz"])
        recording.channel("cz")

    def test_channel_not_found_raises(self):
        loader = EEGLoader(sampling_rate=SR)
        recording = loader.load_array(_make_signal(10.0), channel_names=["C3"])
        with pytest.raises(KeyError):
            recording.channel("Fz")

    def test_duration_correct(self):
        loader = EEGLoader(sampling_rate=SR)
        recording = loader.load_array(_make_signal(10.0))
        assert abs(recording.duration_s - DURATION) < 0.01

    def test_summary_returns_string(self):
        loader = EEGLoader(sampling_rate=SR)
        recording = loader.load_array(_make_signal(10.0))
        assert isinstance(recording.summary(), str)


class TestSessionAnalyzer:
    def _recording(self, signal: np.ndarray) -> EEGRecording:
        return EEGLoader(sampling_rate=SR).load_array(signal, channel_names=["C3"])

    def test_produces_epochs(self):
        analyzer = SessionAnalyzer(channel="C3", window_s=0.5, step_s=0.25)
        report = analyzer.run(self._recording(_motor_signal()))
        assert report.n_epochs > 0

    def test_epoch_count_reasonable(self):
        analyzer = SessionAnalyzer(channel="C3", window_s=0.5, step_s=0.5)
        report = analyzer.run(self._recording(_motor_signal()))
        expected = int(DURATION / 0.5)
        assert abs(report.n_epochs - expected) <= 1

    def test_success_plus_blocked_equals_total(self):
        analyzer = SessionAnalyzer(channel="C3", window_s=0.5, step_s=0.5)
        report = analyzer.run(self._recording(_motor_signal()))
        assert report.n_success + report.n_blocked == report.n_epochs

    def test_block_rate_in_range(self):
        analyzer = SessionAnalyzer(channel="C3", window_s=0.5, step_s=0.5)
        report = analyzer.run(self._recording(_motor_signal()))
        assert 0.0 <= report.block_rate <= 1.0

    def test_mean_confidence_in_range(self):
        analyzer = SessionAnalyzer(channel="C3", window_s=0.5, step_s=0.5)
        report = analyzer.run(self._recording(_motor_signal()))
        assert 0.0 <= report.mean_confidence <= 1.0

    def test_intent_distribution_sums_to_n_epochs(self):
        analyzer = SessionAnalyzer(channel="C3", window_s=0.5, step_s=0.5)
        report = analyzer.run(self._recording(_motor_signal()))
        assert sum(report.intent_distribution.values()) == report.n_epochs

    def test_alpha_signal_has_higher_block_rate_than_motor(self):
        analyzer = SessionAnalyzer(channel="C3", window_s=0.5, step_s=0.5)
        motor_report = analyzer.run(self._recording(_motor_signal()))
        analyzer2 = SessionAnalyzer(channel="C3", window_s=0.5, step_s=0.5)
        alpha_report = analyzer2.run(self._recording(_alpha_signal()))
        assert alpha_report.block_rate >= motor_report.block_rate

    def test_save_jsonl(self, tmp_path):
        analyzer = SessionAnalyzer(channel="C3", window_s=0.5, step_s=0.5)
        report = analyzer.run(self._recording(_motor_signal()))
        out = tmp_path / "report.jsonl"
        report.save_jsonl(out)
        assert out.exists()
        lines = out.read_text().strip().splitlines()
        assert len(lines) == report.n_epochs + 1

    def test_save_csv(self, tmp_path):
        analyzer = SessionAnalyzer(channel="C3", window_s=0.5, step_s=0.5)
        report = analyzer.run(self._recording(_motor_signal()))
        out = tmp_path / "report.csv"
        report.save_csv(out)
        assert out.exists()

    def test_window_too_short_raises(self):
        analyzer = SessionAnalyzer(channel="C3", window_s=0.001, step_s=0.001)
        with pytest.raises(ValueError, match="Window too short"):
            analyzer.run(self._recording(_motor_signal()))


class TestTaskPlanner:
    def _simple_plan(self) -> TaskPlan:
        return TaskPlan(
            name="test plan",
            steps=[
                TaskStep("move left", min_confidence=0.0, label="step1"),
                TaskStep("stop", min_confidence=0.0, label="step2"),
            ],
        )

    def test_basic_plan_executes(self):
        bridge = ExecutorBridge(simulate_delay=False)
        trace = bridge.execute(self._simple_plan())
        assert trace.n_steps == 2
        assert trace.outcome in ("completed", "frozen", "partial", "aborted")

    def test_trace_has_all_steps(self):
        bridge = ExecutorBridge(simulate_delay=False)
        trace = bridge.execute(self._simple_plan())
        assert len(trace.steps) == 2

    def test_step_trace_fields_present(self):
        bridge = ExecutorBridge(simulate_delay=False)
        trace = bridge.execute(self._simple_plan())
        for step in trace.steps:
            assert step.pipeline_status in ("success", "blocked", "deferred", "aborted")
            assert 0.0 <= step.pipeline_confidence <= 1.0
            assert step.elapsed_s >= 0.0

    def test_impossible_confidence_defers(self):
        plan = TaskPlan(
            name="impossible",
            steps=[TaskStep("move left", min_confidence=1.1, fallback="freeze")],
        )
        bridge = ExecutorBridge(simulate_delay=False)
        trace = bridge.execute(plan)
        assert any(s.pipeline_status == "deferred" for s in trace.steps)

    def test_abort_fallback_stops_plan(self):
        plan = TaskPlan(
            name="abort test",
            steps=[
                TaskStep("move left", min_confidence=1.1, fallback="abort"),
                TaskStep("stop", min_confidence=0.0),
            ],
        )
        bridge = ExecutorBridge(simulate_delay=False)
        trace = bridge.execute(plan)
        assert trace.outcome == "aborted"
        assert len(trace.steps) == 1

    def test_complete_fallback_proceeds(self):
        plan = TaskPlan(
            name="complete test",
            steps=[TaskStep("move left", min_confidence=1.1, fallback="complete")],
        )
        bridge = ExecutorBridge(simulate_delay=False)
        trace = bridge.execute(plan)
        assert trace.steps[0].pipeline_status in ("success", "blocked")

    def test_plan_summary_returns_string(self):
        bridge = ExecutorBridge(simulate_delay=False)
        trace = bridge.execute(self._simple_plan())
        assert isinstance(trace.summary(), str)
        assert "test plan" in trace.summary()

    def test_empty_plan(self):
        plan = TaskPlan(name="empty", steps=[])
        bridge = ExecutorBridge(simulate_delay=False)
        trace = bridge.execute(plan)
        assert trace.n_steps == 0
        assert trace.outcome == "completed"

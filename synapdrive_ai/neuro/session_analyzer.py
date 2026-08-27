from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional

import numpy as np

from synapdrive_ai.neuro.band_analyzer import BandPowerAnalyzer, BandPowerResult
from synapdrive_ai.neuro.eeg_loader import EEGRecording
from synapdrive_ai.neuro.signal_quality import SignalQualityAnalyzer
from synapdrive_ai.pipeline import SynapDrivePipeline

EpochDecoder = Callable[[np.ndarray, Mapping[str, Any]], Mapping[str, Any]]


@dataclass
class EpochResult:
    epoch_index: int
    time_start_s: float
    time_end_s: float
    channel: str
    band_power: Dict[str, float]
    engagement_ratio: float
    cognitive_ratio: float
    intent_class: str
    signal_confidence: float
    pipeline_status: str
    pipeline_confidence: float
    block_reason: Optional[str]
    evaluation_score: float


@dataclass
class SessionReport:
    source_file: str
    channel: str
    window_s: float
    step_s: float
    n_epochs: int
    n_success: int
    n_blocked: int
    block_rate: float
    mean_confidence: float
    mean_engagement: float
    intent_distribution: Dict[str, int]
    epochs: List[EpochResult]
    safety_config: Dict[str, Any]
    created_utc: float = field(default_factory=time.time)

    def summary(self) -> str:
        lines = [
            f"Session Analysis: {self.source_file}",
            f"  Channel:        {self.channel}",
            f"  Window:         {self.window_s}s  step: {self.step_s}s",
            f"  Epochs:         {self.n_epochs}",
            f"  Passed gate:    {self.n_success} ({100 * (1 - self.block_rate):.1f}%)",
            f"  Blocked:        {self.n_blocked} ({100 * self.block_rate:.1f}%)",
            f"  Mean confidence:{self.mean_confidence:.3f}",
            f"  Mean engagement:{self.mean_engagement:.3f}",
            f"  Intent mix:     {self.intent_distribution}",
        ]
        return "\n".join(lines)

    def save_jsonl(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as f:
            header = {
                "schema": "synapdrive.session.v1",
                "source_file": self.source_file,
                "channel": self.channel,
                "window_s": self.window_s,
                "step_s": self.step_s,
                "n_epochs": self.n_epochs,
                "n_success": self.n_success,
                "n_blocked": self.n_blocked,
                "block_rate": self.block_rate,
                "mean_confidence": self.mean_confidence,
                "mean_engagement": self.mean_engagement,
                "intent_distribution": self.intent_distribution,
                "safety_config": self.safety_config,
                "created_utc": self.created_utc,
            }
            f.write(json.dumps(header) + "\n")
            for ep in self.epochs:
                f.write(json.dumps(asdict(ep)) + "\n")

    def save_csv(self, path: str | Path) -> None:
        import csv as _csv

        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        if not self.epochs:
            return
        fieldnames = list(asdict(self.epochs[0]).keys())
        with p.open("w", newline="", encoding="utf-8") as f:
            writer = _csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for ep in self.epochs:
                writer.writerow(asdict(ep))


class SessionAnalyzer:
    """
    Sliding-window EEG feature analysis with an explicit decoder boundary.

    Without ``decoder``, spectral features are analysis-only and are deliberately blocked
    from actuation. A supplied decoder must return an intent packet containing at least
    ``intent`` and ``confidence``; its outputs still pass through runtime governance.
    """

    def __init__(
        self,
        channel: Optional[str] = None,
        window_s: float = 1.0,
        step_s: float = 0.5,
        image_label: Optional[str] = None,
        simulate_delay: bool = False,
        pipeline: Optional[SynapDrivePipeline] = None,
        decoder: Optional[EpochDecoder] = None,
    ) -> None:
        self.channel = channel
        self.window_s = float(window_s)
        self.step_s = float(step_s)
        self.image_label = image_label
        self._pipe = pipeline or SynapDrivePipeline(simulate_delay=simulate_delay)
        self.decoder = decoder
        self._band_analyzer: Optional[BandPowerAnalyzer] = None

    def run(self, recording: EEGRecording) -> SessionReport:
        ch_name = self.channel or recording.channels[0]
        signal = recording.channel(ch_name)
        sr = recording.sampling_rate

        self._band_analyzer = BandPowerAnalyzer(sampling_rate=sr)

        window_samples = int(self.window_s * sr)
        step_samples = int(self.step_s * sr)

        if window_samples < 4:
            raise ValueError(
                f"Window too short: {self.window_s}s @ {sr}Hz = {window_samples} samples (min 4)"
            )

        epochs: List[EpochResult] = []
        start = 0
        epoch_idx = 0

        while start + window_samples <= len(signal):
            epoch_signal = signal[start : start + window_samples]
            t_start = start / sr
            t_end = (start + window_samples) / sr

            quality_result = SignalQualityAnalyzer(sr).analyze(epoch_signal)
            band_result = self._band_analyzer.analyze(epoch_signal)
            pipeline_out = self._run_epoch_through_pipeline(
                epoch_signal, sr, band_result, quality_result.score, quality_result.state
            )

            intent_out = pipeline_out.get("intent", {}) or {}
            eval_out = pipeline_out.get("evaluation", {}) or {}

            epochs.append(
                EpochResult(
                    epoch_index=epoch_idx,
                    time_start_s=round(t_start, 4),
                    time_end_s=round(t_end, 4),
                    channel=ch_name,
                    band_power=band_result.relative,
                    engagement_ratio=band_result.engagement_ratio,
                    cognitive_ratio=band_result.cognitive_ratio,
                    intent_class=band_result.intent_class,
                    signal_confidence=band_result.confidence,
                    pipeline_status=pipeline_out.get("status", "unknown"),
                    pipeline_confidence=float(intent_out.get("confidence", 0.0)),
                    block_reason=pipeline_out.get("reason"),
                    evaluation_score=float(eval_out.get("score", 0.0)),
                )
            )

            start += step_samples
            epoch_idx += 1

        return self._build_report(recording, ch_name, epochs)

    def _run_epoch_through_pipeline(
        self,
        epoch_signal: np.ndarray,
        sampling_rate: float,
        band_result: BandPowerResult,
        signal_quality: float = 1.0,
        quality_state: str = "good",
    ) -> Dict[str, Any]:
        if self.decoder is None:
            packet: Dict[str, Any] = {
                "intent": "unknown",
                "confidence": 0.0,
                "source": f"eeg_band_features/{band_result.intent_class}",
                "memory_context": [],
                "band_power": band_result.relative,
                "engagement_ratio": band_result.engagement_ratio,
                "cognitive_ratio": band_result.cognitive_ratio,
                "heuristic_score": band_result.confidence,
                "confidence_semantics": "no-decoder",
                "inference_authority": "analysis-only-band-features",
                "analysis_only": True,
                "neural_decode_performed": False,
                "signal_quality": float(signal_quality),
                "signal_quality_state": quality_state,
            }
        else:
            epoch_data = np.asarray(epoch_signal, dtype=float).reshape(1, -1)
            decoder_metadata = {
                "sampling_rate": float(sampling_rate),
                "n_channels": 1,
                "n_samples": int(epoch_data.shape[1]),
                "signal_quality": float(signal_quality),
                "signal_quality_state": quality_state,
            }
            packet = dict(self.decoder(epoch_data.copy(), decoder_metadata))
            packet.setdefault("intent", "unknown")
            packet.setdefault("confidence", 0.0)
            packet.setdefault("source", "external-epoch-decoder")
            packet.setdefault("memory_context", [])
            packet.setdefault("inference_authority", "external-decoder")
            packet.setdefault("neural_decode_performed", True)
            packet["signal_quality"] = float(signal_quality)
            packet["signal_quality_state"] = quality_state
            packet["band_power"] = band_result.relative
            packet["spectral_feature_class"] = band_result.intent_class
            packet["spectral_heuristic_score"] = band_result.confidence

        return self._pipe.run_intent_packet(packet, image_label=self.image_label)

    def _build_report(
        self,
        recording: EEGRecording,
        ch_name: str,
        epochs: List[EpochResult],
    ) -> SessionReport:
        n = len(epochs)
        n_success = sum(1 for e in epochs if e.pipeline_status == "success")
        n_blocked = n - n_success
        confidences = [e.pipeline_confidence for e in epochs]
        engagements = [e.engagement_ratio for e in epochs]
        intent_dist: Dict[str, int] = {"motor": 0, "cognitive": 0, "unclear": 0}
        for e in epochs:
            intent_dist[e.intent_class] = intent_dist.get(e.intent_class, 0) + 1

        guard = self._pipe.guard
        safety_config = {
            "min_confidence_threshold": guard.min_confidence_threshold,
            "blocked_intents_count": len(guard.get_blocked_log()),
            "risk_keywords": guard.risk_keywords,
        }

        return SessionReport(
            source_file=recording.source_file,
            channel=ch_name,
            window_s=self.window_s,
            step_s=self.step_s,
            n_epochs=n,
            n_success=n_success,
            n_blocked=n_blocked,
            block_rate=round(n_blocked / max(n, 1), 4),
            mean_confidence=round(float(np.mean(confidences)) if confidences else 0.0, 4),
            mean_engagement=round(float(np.mean(engagements)) if engagements else 0.0, 4),
            intent_distribution=intent_dist,
            epochs=epochs,
            safety_config=safety_config,
        )

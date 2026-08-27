from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Mapping, Optional

import numpy as np

from synapdrive_ai.neuro.signal_quality import SignalQualityAnalyzer

Decoder = Callable[[np.ndarray, Mapping[str, Any]], Mapping[str, Any]]


@dataclass(frozen=True)
class LSLSnapshot:
    """Acquired Lab Streaming Layer window. No intent is inferred here."""

    data: np.ndarray
    sampling_rate: float
    n_channels: int
    n_samples: int
    stream_name: str
    stream_type: str
    rms: float

    def metadata(self) -> Dict[str, Any]:
        return {
            "sampling_rate": self.sampling_rate,
            "n_channels": self.n_channels,
            "n_samples": self.n_samples,
            "stream_name": self.stream_name,
            "stream_type": self.stream_type,
            "rms": self.rms,
        }


class LSLIntentSource:
    """Optional LSL acquisition adapter with an explicit decoder boundary.

    LSL samples are acquired and quality-checked. No RMS-to-intent heuristic exists. If
    a decoder is not supplied the returned packet is an explicit abstention and therefore
    cannot pass the governed runtime's confidence gate.
    """

    def __init__(
        self,
        stream_name: Optional[str] = None,
        stream_type: Optional[str] = None,
        resolve_timeout_s: float = 5.0,
        snapshot_seconds: float = 2.0,
        max_chunk_samples: int = 512,
        decoder: Decoder | None = None,
    ) -> None:
        try:
            from pylsl import StreamInlet, resolve_stream  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "pylsl is not installed. Run: pip install -r requirements-lsl.txt"
            ) from exc

        if resolve_timeout_s <= 0:
            raise ValueError("resolve_timeout_s must be > 0")
        if snapshot_seconds <= 0:
            raise ValueError("snapshot_seconds must be > 0")
        if max_chunk_samples <= 0:
            raise ValueError("max_chunk_samples must be > 0")

        self._StreamInlet = StreamInlet
        self._resolve_stream = resolve_stream
        self.stream_name = stream_name
        self.stream_type = stream_type
        self.resolve_timeout_s = float(resolve_timeout_s)
        self.snapshot_seconds = float(snapshot_seconds)
        self.max_chunk_samples = int(max_chunk_samples)
        self.decoder = decoder

    def _resolve(self):
        if self.stream_name:
            streams = self._resolve_stream("name", self.stream_name, timeout=self.resolve_timeout_s)
        else:
            requested_type = self.stream_type or "EEG"
            streams = self._resolve_stream("type", requested_type, timeout=self.resolve_timeout_s)

        if not streams:
            raise RuntimeError(
                "No LSL stream found. Provide --lsl-name or --lsl-type, or start an LSL publisher."
            )

        info = streams[0]
        inlet = self._StreamInlet(info, max_chunklen=self.max_chunk_samples)
        return inlet, info

    def _snapshot(self) -> LSLSnapshot:
        inlet, info = self._resolve()
        name = str(getattr(info, "name", lambda: "unknown")())
        stream_type = str(getattr(info, "type", lambda: "unknown")())
        nominal_srate = float(getattr(info, "nominal_srate", lambda: 0.0)() or 0.0)

        samples: List[List[float]] = []
        start = time.monotonic()
        while (time.monotonic() - start) < self.snapshot_seconds:
            chunk, _timestamps = inlet.pull_chunk(timeout=0.2, max_samples=self.max_chunk_samples)
            if chunk:
                samples.extend(chunk)

        if not samples:
            data = np.empty((0, 0), dtype=float)
        else:
            arr = np.asarray(samples, dtype=float)
            if arr.ndim == 1:
                arr = arr[:, None]
            # Internal convention is channels x samples.
            data = arr.T

        rms = float(np.sqrt(np.mean(np.square(data)))) if data.size else 0.0
        return LSLSnapshot(
            data=data,
            sampling_rate=nominal_srate,
            n_channels=int(data.shape[0]) if data.ndim == 2 else 0,
            n_samples=int(data.shape[1]) if data.ndim == 2 else 0,
            stream_name=name,
            stream_type=stream_type,
            rms=rms,
        )

    def next_observation(self) -> LSLSnapshot:
        return self._snapshot()

    def next_intent_packet(self) -> Dict[str, Any]:
        snap = self._snapshot()
        metadata = snap.metadata()

        if snap.sampling_rate <= 0:
            quality_score = 0.0
            quality_state = "invalid"
            quality_detail: Dict[str, Any] = {"issues": ["unknown-sampling-rate"]}
        else:
            quality = SignalQualityAnalyzer(snap.sampling_rate).analyze(snap.data)
            quality_score = quality.score
            quality_state = quality.state
            quality_detail = quality.to_dict()
        metadata["signal_quality"] = quality_detail

        if self.decoder is None:
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "source": "lsl/acquisition-only",
                "raw_text": "",
                "params": metadata,
                "memory_context": [],
                "signal_quality": quality_score,
                "signal_quality_state": quality_state,
                "decoder_status": "not-configured",
                "inference_authority": "acquisition-only",
                "analysis_only": True,
                "abstention_reason": "LSL acquisition has no configured decoder",
            }

        decoded = dict(self.decoder(snap.data.copy(), metadata))
        intent = str(decoded.get("intent") or "unknown").strip() or "unknown"
        try:
            confidence = float(decoded.get("confidence", 0.0))
        except (TypeError, ValueError) as exc:
            raise ValueError("decoder confidence must be numeric") from exc
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("decoder confidence must be in [0, 1]")

        packet = dict(decoded)
        packet.update(
            {
                "intent": intent,
                "confidence": confidence,
                "source": str(decoded.get("source") or "lsl/decoder"),
                "memory_context": list(decoded.get("memory_context") or []),
                "signal_quality": quality_score,
                "signal_quality_state": quality_state,
                "acquisition": metadata,
                "decoder_status": "configured",
                "inference_authority": str(
                    decoded.get("inference_authority") or "external-decoder"
                ),
            }
        )
        return packet

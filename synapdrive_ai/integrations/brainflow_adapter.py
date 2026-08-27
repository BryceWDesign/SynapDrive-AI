from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Optional

import numpy as np

from synapdrive_ai.neuro.signal_quality import SignalQualityAnalyzer

Decoder = Callable[[np.ndarray, Mapping[str, Any]], Mapping[str, Any]]


@dataclass(frozen=True)
class BrainFlowSample:
    """EEG acquisition snapshot from a BrainFlow board.

    ``data`` contains only the channels BrainFlow identifies as EEG channels. No intent
    is inferred by this acquisition object.
    """

    data: np.ndarray
    sampling_rate: float
    board_id: int
    n_channels: int
    n_samples: int
    rms: float

    def metadata(self) -> Dict[str, Any]:
        return {
            "board_id": self.board_id,
            "sampling_rate": self.sampling_rate,
            "n_channels": self.n_channels,
            "n_samples": self.n_samples,
            "rms": self.rms,
        }


class BrainFlowIntentSource:
    """Optional BrainFlow acquisition adapter with an explicit decoder boundary.

    The adapter acquires EEG samples and computes engineering signal-quality checks. It
    does **not** convert signal energy into an intent. If no decoder callable is supplied,
    ``next_intent_packet`` returns an ``unknown`` packet with zero confidence so the
    governed runtime abstains.

    The default board id is BrainFlow's SYNTHETIC_BOARD (-1), which keeps the optional
    smoke path hardware-independent when BrainFlow is installed.
    """

    def __init__(
        self,
        board_id: int = -1,
        serial_port: Optional[str] = None,
        stream_seconds: float = 2.0,
        decoder: Decoder | None = None,
    ) -> None:
        try:
            from brainflow.board_shim import BoardShim, BrainFlowInputParams  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "BrainFlow is not installed. Run: pip install -r requirements-brainflow.txt"
            ) from exc

        if stream_seconds <= 0:
            raise ValueError("stream_seconds must be > 0")

        self._BoardShim = BoardShim
        self._BrainFlowInputParams = BrainFlowInputParams
        self.board_id = int(board_id)
        self.serial_port = serial_port
        self.stream_seconds = float(stream_seconds)
        self.decoder = decoder

    def _acquire(self) -> BrainFlowSample:
        params = self._BrainFlowInputParams()
        if self.serial_port:
            params.serial_port = self.serial_port

        board = self._BoardShim(self.board_id, params)
        board.prepare_session()
        try:
            board.start_stream()
            time.sleep(self.stream_seconds)
            raw = board.get_board_data()
        finally:
            try:
                board.stop_stream()
            except Exception:
                # Session cleanup must continue even if a driver reports that streaming
                # already stopped. The acquisition error, if any, occurs before this path.
                pass
            try:
                board.release_session()
            except Exception:
                pass

        arr = np.asarray(raw, dtype=float)
        if arr.ndim != 2 or arr.size == 0:
            eeg = np.empty((0, 0), dtype=float)
        else:
            eeg_indices = list(self._BoardShim.get_eeg_channels(self.board_id))
            eeg = arr[eeg_indices, :] if eeg_indices else np.empty((0, arr.shape[1]), dtype=float)

        sampling_rate = float(self._BoardShim.get_sampling_rate(self.board_id))
        rms = float(np.sqrt(np.mean(np.square(eeg)))) if eeg.size else 0.0
        return BrainFlowSample(
            data=eeg,
            sampling_rate=sampling_rate,
            board_id=self.board_id,
            n_channels=int(eeg.shape[0]) if eeg.ndim == 2 else 0,
            n_samples=int(eeg.shape[1]) if eeg.ndim == 2 else 0,
            rms=rms,
        )

    def next_observation(self) -> BrainFlowSample:
        """Acquire and return EEG samples without interpreting them."""
        return self._acquire()

    def next_intent_packet(self) -> Dict[str, Any]:
        sample = self._acquire()
        quality = SignalQualityAnalyzer(sample.sampling_rate).analyze(sample.data)
        metadata = sample.metadata()
        metadata["signal_quality"] = quality.to_dict()

        if self.decoder is None:
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "source": "brainflow/acquisition-only",
                "raw_text": "",
                "params": metadata,
                "memory_context": [],
                "signal_quality": quality.score,
                "signal_quality_state": quality.state,
                "decoder_status": "not-configured",
                "inference_authority": "acquisition-only",
                "analysis_only": True,
                "abstention_reason": "brainflow acquisition has no configured decoder",
            }

        decoded = dict(self.decoder(sample.data.copy(), metadata))
        return self._validate_decoded_packet(decoded, quality.score, quality.state, metadata)

    @staticmethod
    def _validate_decoded_packet(
        decoded: Dict[str, Any],
        quality_score: float,
        quality_state: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
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
                "source": str(decoded.get("source") or "brainflow/decoder"),
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

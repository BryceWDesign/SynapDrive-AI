from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np


@dataclass
class BrainFlowSample:
    """A minimal sample snapshot derived from BrainFlow board data."""
    rms: float
    n_channels: int
    n_samples: int


class BrainFlowIntentSource:
    """
    Optional “real-ish” input source backed by BrainFlow.

    - This does NOT claim medical validity.
    - It uses BrainFlow's Synthetic board by default to keep it runnable.
    - The mapping from sample→intent is a conservative placeholder heuristic.
      Replace it with a real decoder when you integrate a headset/dataset.
    """

    def __init__(
        self,
        board_id: int = 0,
        serial_port: Optional[str] = None,
        stream_seconds: float = 2.0,
    ) -> None:
        # Import only when used (so base installs remain lightweight)
        try:
            from brainflow.board_shim import BoardShim, BrainFlowInputParams  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "BrainFlow is not installed. Run: pip install -r requirements-brainflow.txt"
            ) from e

        self._BoardShim = BoardShim
        self._BrainFlowInputParams = BrainFlowInputParams

        self.board_id = int(board_id)
        self.serial_port = serial_port
        self.stream_seconds = float(stream_seconds)

    def _acquire(self) -> BrainFlowSample:
        params = self._BrainFlowInputParams()
        if self.serial_port:
            params.serial_port = self.serial_port

        board = self._BoardShim(self.board_id, params)
        self._BoardShim.enable_dev_board_logger()

        board.prepare_session()
        try:
            board.start_stream()
            # BrainFlow streams continuously; we keep this short & deterministic.
            self._BoardShim.sleep(int(self.stream_seconds * 1000))
            data = board.get_board_data()  # shape: (channels, samples)
        finally:
            try:
                board.stop_stream()
            except Exception:
                pass
            try:
                board.release_session()
            except Exception:
                pass

        # Compute RMS across all channels/samples as a minimal “signal energy” proxy
        if data is None or len(data) == 0:
            return BrainFlowSample(rms=0.0, n_channels=0, n_samples=0)

        arr = np.array(data, dtype=float)
        rms = float(np.sqrt(np.mean(np.square(arr)))) if arr.size else 0.0
        n_channels = int(arr.shape[0]) if arr.ndim == 2 else 0
        n_samples = int(arr.shape[1]) if arr.ndim == 2 else int(arr.size)

        return BrainFlowSample(rms=rms, n_channels=n_channels, n_samples=n_samples)

    def next_intent_packet(self) -> Dict[str, Any]:
        """
        Return a packet compatible with SynapDrivePipeline._run_common().

        Heuristic mapping:
          - very low energy -> 'halt_all_motion' (safe default)
          - moderate energy -> 'expand_context'
          - high energy -> 'initiate_walk'
        """
        sample = self._acquire()

        # Conservative thresholds (placeholders) — tuned for “don’t do risky things by accident”
        if sample.rms < 5.0:
            intent = "halt_all_motion"
            conf = 0.70
        elif sample.rms < 20.0:
            intent = "expand_context"
            conf = 0.75
        else:
            intent = "initiate_walk"
            conf = 0.80

        return {
            "intent": intent,
            "confidence": float(conf),
            "source": "brainflow",
            "raw_text": "",
            "params": {
                "rms": f"{sample.rms:.3f}",
                "n_channels": str(sample.n_channels),
                "n_samples": str(sample.n_samples),
            },
            "memory_context": [],
        }

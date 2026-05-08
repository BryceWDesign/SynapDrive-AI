from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class LSLSnapshot:
    rms: float
    n_channels: int
    n_samples: int
    stream_name: str
    stream_type: str


class LSLIntentSource:
    """
    Optional lab-stream input source backed by pylsl (Lab Streaming Layer).

    - This does NOT claim medical validity.
    - By default, it resolves the *first* matching stream and takes a short snapshot window.
    - Mapping from snapshot → intent is conservative placeholder logic.
    """

    def __init__(
        self,
        stream_name: Optional[str] = None,
        stream_type: Optional[str] = None,
        resolve_timeout_s: float = 5.0,
        snapshot_seconds: float = 2.0,
        max_chunk_samples: int = 512,
    ) -> None:
        try:
            from pylsl import StreamInlet, resolve_stream  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "pylsl is not installed. Run: pip install -r requirements-lsl.txt"
            ) from e

        self._StreamInlet = StreamInlet
        self._resolve_stream = resolve_stream

        self.stream_name = stream_name
        self.stream_type = stream_type
        self.resolve_timeout_s = float(resolve_timeout_s)
        self.snapshot_seconds = float(snapshot_seconds)
        self.max_chunk_samples = int(max_chunk_samples)

    def _resolve(self):
        """
        Resolve an LSL stream.
        If both name and type are unset, resolve any stream (first match).
        """
        streams = []

        # pylsl resolve_stream supports property queries like ("name", "X") or ("type", "EEG")
        if self.stream_name:
            streams = self._resolve_stream("name", self.stream_name, timeout=self.resolve_timeout_s)
        elif self.stream_type:
            streams = self._resolve_stream("type", self.stream_type, timeout=self.resolve_timeout_s)
        else:
            # Fallback: pylsl does not support a type wildcard, so try a common type first.
            # then fall back to a short "anything" attempt by name is not possible.
            # Best-effort: try EEG first (common) then raise if none found.
            streams = self._resolve_stream("type", "EEG", timeout=self.resolve_timeout_s)

        if not streams:
            raise RuntimeError(
                "No LSL stream found. Provide --lsl-name or --lsl-type, or start an LSL publisher."
            )

        info = streams[0]
        inlet = self._StreamInlet(info, max_chunklen=self.max_chunk_samples)

        return inlet, info

    def _snapshot(self) -> LSLSnapshot:
        inlet, info = self._resolve()

        name = getattr(info, "name", lambda: "unknown")()
        stype = getattr(info, "type", lambda: "unknown")()

        # pull_chunk returns (samples, timestamps)
        # samples is List[List[float]] with shape approx [n_samples][n_channels]
        samples: List[List[float]] = []
        start = time.time()

        while (time.time() - start) < self.snapshot_seconds:
            chunk, _ts = inlet.pull_chunk(timeout=0.2, max_samples=self.max_chunk_samples)
            if chunk:
                samples.extend(chunk)

        if not samples:
            return LSLSnapshot(
                rms=0.0,
                n_channels=0,
                n_samples=0,
                stream_name=str(name),
                stream_type=str(stype),
            )

        arr = np.array(samples, dtype=float)  # shape: (n_samples, n_channels)
        rms = float(np.sqrt(np.mean(np.square(arr)))) if arr.size else 0.0
        n_samples = int(arr.shape[0]) if arr.ndim == 2 else int(arr.size)
        n_channels = int(arr.shape[1]) if arr.ndim == 2 else 0

        return LSLSnapshot(
            rms=rms,
            n_channels=n_channels,
            n_samples=n_samples,
            stream_name=str(name),
            stream_type=str(stype),
        )

    def next_intent_packet(self) -> Dict[str, Any]:
        """
        Return a packet compatible with SynapDrivePipeline._run_common().

        Conservative placeholder mapping:
          - very low energy -> halt_all_motion
          - moderate -> expand_context
          - high -> initiate_walk

        You can replace this with a real decoder later (bandpower features, ML classifier, etc).
        """
        snap = self._snapshot()

        # Conservative thresholds — tuned to avoid accidental movement on noisy data.
        if snap.rms < 5.0:
            intent = "halt_all_motion"
            conf = 0.70
        elif snap.rms < 20.0:
            intent = "expand_context"
            conf = 0.75
        else:
            intent = "initiate_walk"
            conf = 0.80

        return {
            "intent": intent,
            "confidence": float(conf),
            "source": "lsl",
            "raw_text": "",
            "params": {
                "rms": f"{snap.rms:.3f}",
                "n_channels": str(snap.n_channels),
                "n_samples": str(snap.n_samples),
                "stream_name": snap.stream_name,
                "stream_type": snap.stream_type,
            },
            "memory_context": [],
        }

from __future__ import annotations

import csv
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np


@dataclass
class EEGRecording:
    """
    A loaded EEG recording.

    Attributes:
        channels: Ordered list of channel names.
        data: 2-D array, shape (n_channels, n_samples).
        sampling_rate: Hz.
        duration_s: Total duration in seconds.
        source_file: Original file path.
        metadata: Header fields from EDF or user-supplied dict.
    """
    channels: List[str]
    data: np.ndarray
    sampling_rate: float
    duration_s: float
    source_file: str
    metadata: Dict = field(default_factory=dict)

    def channel(self, name: str) -> np.ndarray:
        name_upper = name.upper()
        for i, ch in enumerate(self.channels):
            if ch.upper() == name_upper:
                return self.data[i]
        raise KeyError(f"Channel {name!r} not found. Available: {self.channels}")

    def channel_index(self, idx: int) -> np.ndarray:
        return self.data[idx]

    @property
    def n_channels(self) -> int:
        return len(self.channels)

    @property
    def n_samples(self) -> int:
        return self.data.shape[1] if self.data.ndim == 2 else len(self.data)

    def summary(self) -> str:
        return (
            f"EEGRecording: {self.n_channels} channels × {self.n_samples} samples "
            f"@ {self.sampling_rate} Hz ({self.duration_s:.1f}s) — {self.source_file}"
        )


class EEGLoader:
    """
    Loads EEG recordings from EDF, CSV, or NPY files.

    Args:
        sampling_rate: Default Hz used when the file doesn't encode it (CSV/NPY).
    """

    def __init__(self, sampling_rate: float = 256.0) -> None:
        self.default_sampling_rate = float(sampling_rate)

    def load(self, path: str | Path) -> EEGRecording:
        p = Path(path)
        suffix = p.suffix.lower()
        if suffix in (".edf", ".bdf"):
            return self._load_edf(p)
        if suffix == ".csv":
            return self._load_csv(p)
        if suffix == ".npy":
            return self._load_npy(p)
        raise ValueError(f"Unsupported file format: {suffix!r}. Use .edf, .bdf, .csv, or .npy")

    def load_array(
        self,
        data: np.ndarray,
        sampling_rate: Optional[float] = None,
        channel_names: Optional[List[str]] = None,
        source_label: str = "array",
    ) -> EEGRecording:
        data = np.atleast_2d(np.asarray(data, dtype=float))
        if data.shape[0] > data.shape[1]:
            data = data.T

        sr = float(sampling_rate or self.default_sampling_rate)
        n_ch = data.shape[0]
        names = channel_names or [f"CH{i+1}" for i in range(n_ch)]
        duration = data.shape[1] / sr

        return EEGRecording(
            channels=names,
            data=data,
            sampling_rate=sr,
            duration_s=duration,
            source_file=source_label,
        )

    def _load_edf(self, path: Path) -> EEGRecording:
        with open(path, "rb") as f:
            raw = f.read()

        hdr = raw[:256]
        n_records = int(hdr[236:244].decode("ascii", errors="replace").strip() or -1)
        record_duration = float(hdr[244:252].decode("ascii", errors="replace").strip() or 1)
        n_signals = int(hdr[252:256].decode("ascii", errors="replace").strip())

        sh_start = 256
        sh_size = n_signals * 256

        def _field(offset: int, width: int, sig_idx: int) -> str:
            base = sh_start + offset * n_signals + sig_idx * width
            return raw[base:base + width].decode("ascii", errors="replace").strip()

        channel_names = [_field(0, 16, i) for i in range(n_signals)]
        physical_min = [float(_field(104, 8, i) or 0) for i in range(n_signals)]
        physical_max = [float(_field(112, 8, i) or 1) for i in range(n_signals)]
        digital_min = [float(_field(120, 8, i) or -32768) for i in range(n_signals)]
        digital_max = [float(_field(128, 8, i) or 32767) for i in range(n_signals)]
        n_samples_per_record = [int(_field(216, 8, i) or 0) for i in range(n_signals)]

        sr_per_signal = [
            (ns / record_duration if record_duration > 0 else self.default_sampling_rate)
            for ns in n_samples_per_record
        ]
        sampling_rate = float(sr_per_signal[0]) if sr_per_signal else self.default_sampling_rate

        gains, offsets = [], []
        for i in range(n_signals):
            d_range = digital_max[i] - digital_min[i] or 1
            p_range = physical_max[i] - physical_min[i]
            gain = p_range / d_range
            offset = physical_max[i] / gain - digital_max[i]
            gains.append(gain)
            offsets.append(offset)

        data_start = 256 + sh_size
        data_raw = raw[data_start:]

        total_per_record = sum(n_samples_per_record)
        records_available = len(data_raw) // (total_per_record * 2)
        if n_records < 0:
            n_records = records_available
        n_records = min(n_records, records_available)

        channels_raw: List[List[int]] = [[] for _ in range(n_signals)]
        offset_bytes = 0
        for _ in range(n_records):
            for sig_idx in range(n_signals):
                ns = n_samples_per_record[sig_idx]
                chunk = data_raw[offset_bytes:offset_bytes + ns * 2]
                samples = struct.unpack(f"<{ns}h", chunk)
                channels_raw[sig_idx].extend(samples)
                offset_bytes += ns * 2

        data = np.array(
            [
                (np.array(channels_raw[i], dtype=float) + offsets[i]) * gains[i]
                for i in range(n_signals)
            ],
            dtype=float,
        )
        duration = data.shape[1] / sampling_rate if sampling_rate > 0 else 0.0

        return EEGRecording(
            channels=channel_names,
            data=data,
            sampling_rate=sampling_rate,
            duration_s=duration,
            source_file=str(path),
            metadata={
                "n_records": n_records,
                "record_duration_s": record_duration,
                "format": path.suffix.upper(),
            },
        )

    def _load_csv(self, path: Path) -> EEGRecording:
        with open(path, newline="", encoding="utf-8") as f:
            sample = f.read(2048)
            f.seek(0)
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t ")
            has_header = csv.Sniffer().has_header(sample)
            reader = csv.reader(f, dialect)
            rows = list(reader)

        if not rows:
            raise ValueError(f"CSV file is empty: {path}")

        if has_header:
            headers = [h.strip() for h in rows[0]]
            data_rows = rows[1:]
        else:
            headers = None
            data_rows = rows

        arr = np.array([[float(v) for v in row] for row in data_rows if row], dtype=float)

        is_time_col = False
        if arr.shape[1] > 1:
            col0 = arr[:, 0]
            diffs = np.diff(col0)
            if np.all(diffs > 0) and np.std(diffs) / (np.mean(diffs) + 1e-9) < 0.05:
                is_time_col = True

        if is_time_col:
            time_col = arr[:, 0]
            signal_arr = arr[:, 1:].T
            sr = 1.0 / np.mean(np.diff(time_col)) if len(time_col) > 1 else self.default_sampling_rate
            ch_names = (headers[1:] if headers else None) or [f"CH{i+1}" for i in range(signal_arr.shape[0])]
        else:
            signal_arr = arr.T
            sr = self.default_sampling_rate
            ch_names = (headers if headers else None) or [f"CH{i+1}" for i in range(signal_arr.shape[0])]

        return EEGRecording(
            channels=ch_names,
            data=signal_arr,
            sampling_rate=sr,
            duration_s=signal_arr.shape[1] / sr,
            source_file=str(path),
            metadata={"format": "CSV"},
        )

    def _load_npy(self, path: Path) -> EEGRecording:
        arr = np.load(path).astype(float)
        recording = self.load_array(arr, source_label=str(path))
        recording.metadata["format"] = "NPY"
        return recording

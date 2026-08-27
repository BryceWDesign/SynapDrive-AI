from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np


@dataclass(frozen=True)
class EpochDataset:
    epochs: np.ndarray
    labels: np.ndarray
    sampling_rate: float
    channel_names: List[str]
    source: str

    def __post_init__(self) -> None:
        if self.epochs.ndim != 3:
            raise ValueError("epochs must have shape (n_epochs, n_channels, n_samples)")
        if len(self.epochs) != len(self.labels):
            raise ValueError("epochs and labels length mismatch")
        if self.sampling_rate <= 0:
            raise ValueError("sampling_rate must be positive")
        if len(self.channel_names) != self.epochs.shape[1]:
            raise ValueError("channel_names must match epoch channel count")


def load_npz_dataset(path: str | Path) -> EpochDataset:
    """Load a labeled EEG epoch dataset from an explicit NPZ contract.

    Required arrays: X (epochs x channels x samples), y (labels), sampling_rate.
    Optional: channel_names. No demo or fabricated labels are substituted.
    """

    p = Path(path)
    with np.load(p, allow_pickle=False) as data:
        missing = {"X", "y", "sampling_rate"} - set(data.files)
        if missing:
            raise ValueError(f"dataset missing required arrays: {sorted(missing)}")
        x = np.asarray(data["X"], dtype=float)
        y = np.asarray(data["y"])
        sr = float(np.asarray(data["sampling_rate"]).reshape(-1)[0])
        if "channel_names" in data.files:
            names = [str(v) for v in np.asarray(data["channel_names"]).tolist()]
        else:
            names = [f"CH{i + 1}" for i in range(x.shape[1] if x.ndim >= 2 else 0)]
    return EpochDataset(x, y, sr, names, str(p))

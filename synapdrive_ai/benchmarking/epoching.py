from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from synapdrive_ai.benchmarking.dataset import EpochDataset
from synapdrive_ai.neuro.eeg_loader import EEGRecording


@dataclass(frozen=True)
class LabeledEvent:
    onset_s: float
    label: str


def load_events_csv(path: str | Path) -> list[LabeledEvent]:
    """Load event onsets from CSV columns `onset_s` and `label`."""
    events: list[LabeledEvent] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        if not {"onset_s", "label"}.issubset(fields):
            raise ValueError("event CSV requires columns: onset_s,label")
        for row in reader:
            label = str(row.get("label") or "").strip()
            if not label:
                raise ValueError("event label must not be empty")
            events.append(LabeledEvent(float(row["onset_s"]), label))
    if not events:
        raise ValueError("event CSV contains no events")
    return events


def epoch_recording(
    recording: EEGRecording,
    events: Iterable[LabeledEvent],
    *,
    tmin_s: float = 0.0,
    tmax_s: float = 1.0,
    channels: Sequence[str] | None = None,
) -> EpochDataset:
    """Cut labeled fixed-length epochs from a loaded recording.

    Events whose requested window extends outside the recording are rejected rather than
    silently padded or shortened.
    """
    if tmax_s <= tmin_s:
        raise ValueError("tmax_s must be greater than tmin_s")
    selected_names = list(channels) if channels else list(recording.channels)
    selected = np.stack([recording.channel(name) for name in selected_names])
    sr = recording.sampling_rate
    n_samples = int(round((tmax_s - tmin_s) * sr))
    if n_samples < 2:
        raise ValueError("epoch window is too short")

    epochs = []
    labels = []
    for event in events:
        start = int(round((event.onset_s + tmin_s) * sr))
        end = start + n_samples
        if start < 0 or end > recording.n_samples:
            raise ValueError(
                f"event {event.label!r} at {event.onset_s}s exceeds recording bounds"
            )
        epochs.append(selected[:, start:end])
        labels.append(event.label)
    if not epochs:
        raise ValueError("no events supplied")
    return EpochDataset(
        epochs=np.asarray(epochs, dtype=float),
        labels=np.asarray(labels),
        sampling_rate=sr,
        channel_names=selected_names,
        source=recording.source_file,
    )

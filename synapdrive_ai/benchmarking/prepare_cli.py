from __future__ import annotations

import argparse

import numpy as np

from synapdrive_ai.benchmarking.epoching import epoch_recording, load_events_csv
from synapdrive_ai.neuro.eeg_loader import EEGLoader


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a labeled SynapDrive benchmark NPZ from a recording and event CSV."
    )
    parser.add_argument("recording")
    parser.add_argument("events", help="CSV with onset_s,label columns")
    parser.add_argument("--out", required=True)
    parser.add_argument("--tmin", type=float, default=0.0)
    parser.add_argument("--tmax", type=float, default=1.0)
    parser.add_argument("--sr", type=float, default=256.0)
    parser.add_argument("--channel", action="append", dest="channels")
    args = parser.parse_args(argv)

    recording = EEGLoader(sampling_rate=args.sr).load(args.recording)
    events = load_events_csv(args.events)
    dataset = epoch_recording(
        recording,
        events,
        tmin_s=args.tmin,
        tmax_s=args.tmax,
        channels=args.channels,
    )
    np.savez(
        args.out,
        X=dataset.epochs,
        y=dataset.labels,
        sampling_rate=np.array([dataset.sampling_rate]),
        channel_names=np.asarray(dataset.channel_names),
    )
    print(
        f"wrote {len(dataset.labels)} epochs x {dataset.epochs.shape[1]} channels "
        f"x {dataset.epochs.shape[2]} samples to {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

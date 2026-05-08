from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np


def cmd_demo(args) -> int:
    from synapdrive_ai.neuro.band_analyzer import BandPowerAnalyzer
    from synapdrive_ai.neuro.eeg_loader import EEGLoader
    from synapdrive_ai.neuro.session_analyzer import SessionAnalyzer

    print("SynapDrive-AI  ·  Neuroscience demo\n")

    sr = 256.0
    duration = 10.0
    n_samples = int(sr * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)

    signal = (
        0.5 * np.sin(2 * np.pi * 6 * t)
        + 1.0 * np.sin(2 * np.pi * 10 * t)
        + 0.3 * np.sin(2 * np.pi * 20 * t)
        + 0.1 * np.sin(2 * np.pi * 40 * t)
    )

    burst = (t >= 4.0) & (t <= 7.0)
    signal[burst] = (
        0.2 * np.sin(2 * np.pi * 6 * t[burst])
        + 0.2 * np.sin(2 * np.pi * 10 * t[burst])
        + 1.2 * np.sin(2 * np.pi * 20 * t[burst])
        + 0.8 * np.sin(2 * np.pi * 40 * t[burst])
    )
    signal += np.random.normal(0, 0.05, n_samples)

    loader = EEGLoader(sampling_rate=sr)
    recording = loader.load_array(
        signal, sampling_rate=sr, channel_names=["C3"], source_label="demo_synthetic"
    )

    print(f"Synthetic recording: {recording.summary()}")
    print("Motor intent burst injected at t=4s–7s\n")

    analyzer = BandPowerAnalyzer(sampling_rate=sr)
    result = analyzer.analyze(signal)
    print("Full-signal band power:")
    for band, power in result.relative.items():
        bar = "█" * int(power * 40)
        print(f"  {band:6s} {power:.3f}  {bar}")
    print(f"  engagement ratio: {result.engagement_ratio:.3f}")
    print(f"  intent class:     {result.intent_class}")
    print(f"  confidence:       {result.confidence:.3f}\n")

    session_analyzer = SessionAnalyzer(channel="C3", window_s=1.0, step_s=0.5)
    report = session_analyzer.run(recording)

    print(report.summary())
    print("\nEpoch detail:")
    print(f"  {'t_start':>7}  {'class':>10}  {'conf':>6}  {'status':>8}")
    for ep in report.epochs:
        print(
            f"  {ep.time_start_s:>7.1f}s  {ep.intent_class:>10}  "
            f"{ep.signal_confidence:>6.3f}  {ep.pipeline_status:>8}"
        )

    return 0


def cmd_analyze(args) -> int:
    from synapdrive_ai.neuro.eeg_loader import EEGLoader
    from synapdrive_ai.neuro.session_analyzer import SessionAnalyzer

    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1

    print(f"Loading {path}...")
    loader = EEGLoader(sampling_rate=args.sr)
    recording = loader.load(path)
    print(recording.summary())

    if args.channels:
        print(f"Available channels: {recording.channels}")
        return 0

    channel = args.channel or recording.channels[0]
    print(f"Analyzing channel: {channel}  window={args.window}s  step={args.step}s\n")

    analyzer = SessionAnalyzer(
        channel=channel,
        window_s=args.window,
        step_s=args.step,
        image_label=args.image,
    )
    report = analyzer.run(recording)
    print(report.summary())

    if args.out:
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = path.stem
        jsonl_path = out_dir / f"{stem}_analysis.jsonl"
        csv_path = out_dir / f"{stem}_epochs.csv"
        report.save_jsonl(jsonl_path)
        report.save_csv(csv_path)
        print(f"\nSaved: {jsonl_path}")
        print(f"Saved: {csv_path}")

    return 0


def cmd_threshold(args) -> int:
    from synapdrive_ai.neuro.eeg_loader import EEGLoader
    from synapdrive_ai.neuro.session_analyzer import SessionAnalyzer

    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1

    loader = EEGLoader(sampling_rate=args.sr)
    recording = loader.load(path)
    channel = args.channel or recording.channels[0]

    thresholds = [float(t) for t in args.min_conf]
    print(f"Threshold sweep — {path.name}  channel={channel}\n")
    print(f"  {'threshold':>10}  {'blocked%':>10}  {'mean_conf':>10}  {'n_success':>10}")

    for thresh in thresholds:
        analyzer = SessionAnalyzer(channel=channel, window_s=args.window, step_s=args.step)
        analyzer._pipe.guard.min_confidence_threshold = thresh
        report = analyzer.run(recording)
        print(
            f"  {thresh:>10.3f}  {report.block_rate * 100:>9.1f}%  "
            f"{report.mean_confidence:>10.3f}  {report.n_success:>10}"
        )

    return 0


def cmd_plan(args) -> int:
    from synapdrive_ai.neuro.task_planner import ExecutorBridge, TaskPlan, TaskStep

    plans = {
        "reach_grasp": TaskPlan(
            name="reach and grasp",
            steps=[
                TaskStep("move forward", min_confidence=0.55, label="approach"),
                TaskStep("move left", min_confidence=0.55, label="align"),
                TaskStep("pick up", min_confidence=0.70, fallback="freeze", label="grasp"),
            ],
        ),
        "navigate": TaskPlan(
            name="navigate to target",
            steps=[
                TaskStep("move forward", min_confidence=0.50, label="forward"),
                TaskStep("turn left", min_confidence=0.55, label="turn"),
                TaskStep("move forward", min_confidence=0.50, label="approach"),
                TaskStep("stop", min_confidence=0.45, label="halt"),
            ],
        ),
        "cognitive_sequence": TaskPlan(
            name="cognitive task sequence",
            steps=[
                TaskStep("calculate", min_confidence=0.55, label="compute"),
                TaskStep("recall", min_confidence=0.50, label="retrieve"),
                TaskStep("stop", min_confidence=0.45, label="confirm"),
            ],
        ),
    }

    if args.list:
        print("Available plans:")
        for name, plan in plans.items():
            print(f"  {name}: {len(plan)} steps — {plan.name}")
        return 0

    task_name = args.task or "reach_grasp"
    if task_name not in plans:
        print(f"Unknown plan: {task_name!r}. Use --list to see options.", file=sys.stderr)
        return 1

    plan = plans[task_name]
    bridge = ExecutorBridge(simulate_delay=False)
    print(f"Executing plan: {plan.name}\n")
    trace = bridge.execute(plan)
    print(trace.summary())
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m synapdrive_ai.neuro.cli",
        description="SynapDrive-AI neuroscience tools",
    )
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("analyze", help="Analyze an EEG file session")
    a.add_argument("file", help="EEG file (.edf, .bdf, .csv, .npy)")
    a.add_argument("--channel", default=None, help="Channel to analyze (default: first)")
    a.add_argument("--channels", action="store_true", help="List available channels and exit")
    a.add_argument("--window", type=float, default=1.0, help="Epoch window in seconds")
    a.add_argument("--step", type=float, default=0.5, help="Sliding step in seconds")
    a.add_argument("--image", default=None, help="Optional visual context label")
    a.add_argument("--sr", type=float, default=256.0, help="Sampling rate Hz for CSV/NPY")
    a.add_argument("--out", default=None, help="Output directory for JSONL + CSV results")

    t = sub.add_parser("threshold", help="Test multiple confidence thresholds")
    t.add_argument("file")
    t.add_argument("--min-conf", nargs="+", default=["0.4", "0.5", "0.6", "0.7"])
    t.add_argument("--channel", default=None)
    t.add_argument("--window", type=float, default=1.0)
    t.add_argument("--step", type=float, default=0.5)
    t.add_argument("--sr", type=float, default=256.0)

    pl = sub.add_parser("plan", help="Execute a sequential task plan")
    pl.add_argument("--task", default=None, help="Plan name")
    pl.add_argument("--list", action="store_true", help="List available plans")

    sub.add_parser("demo", help="Run a full demo with synthetic EEG data")

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    dispatch = {
        "analyze": cmd_analyze,
        "threshold": cmd_threshold,
        "plan": cmd_plan,
        "demo": cmd_demo,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())

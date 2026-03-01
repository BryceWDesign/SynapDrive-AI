# synapdrive_ai/main/cli.py

from __future__ import annotations

import argparse
import json
import sys
import time

from synapdrive_ai.pipeline import SynapDrivePipeline


def _print_summary(out: dict) -> None:
    print("\n=== SynapDrive-AI Output ===")
    print(f"status: {out.get('status')}")
    if out.get("status") == "blocked":
        print(f"reason: {out.get('reason')}")
    print("\nintent_packet:")
    print(json.dumps(out.get("intent", {}), indent=2, default=str))
    print("\nresult_packet:")
    print(json.dumps(out.get("result", {}), indent=2, default=str))
    print("\nevaluation:")
    print(json.dumps(out.get("evaluation", {}), indent=2, default=str))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="synapdrive-ai",
        description="SynapDrive-AI simulation CLI (canonical pipeline).",
    )

    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--text", help="Run one cycle using decoded intent text (e.g. 'move left', 'stop').")
    mode.add_argument("--signal", nargs="?", const="RANDOM", help="Run one cycle using a signal label (or RANDOM).")

    p.add_argument("--image", default=None, help="Optional simulated vision label (road, hazard, person, vehicle).")
    p.add_argument("--count", type=int, default=1, help="How many cycles to run (default: 1).")
    p.add_argument("--interval", type=float, default=0.0, help="Seconds between cycles (default: 0).")

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    pipe = SynapDrivePipeline()

    for i in range(args.count):
        if args.text is not None:
            out = pipe.run_text_command(args.text, image_label=args.image)
        else:
            label = None if args.signal == "RANDOM" else args.signal
            out = pipe.run_signal_event(label=label, image_label=args.image)

        _print_summary(out)

        if i < args.count - 1 and args.interval > 0:
            time.sleep(args.interval)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

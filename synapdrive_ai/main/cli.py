from __future__ import annotations

import argparse
import json
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
    mode.add_argument("--text", help='Run one cycle using decoded intent text (e.g. "move left", "stop").')
    mode.add_argument("--signal", nargs="?", const="RANDOM", help="Run one cycle using a signal label (or RANDOM).")
    mode.add_argument(
        "--brainflow",
        action="store_true",
        help="Run one cycle using BrainFlow input (optional dependency; defaults to Synthetic board).",
    )
    mode.add_argument(
        "--lsl",
        action="store_true",
        help="Run one cycle using LSL (pylsl) stream input (optional dependency).",
    )

    p.add_argument("--image", default=None, help='Optional simulated vision label (road, hazard, person, vehicle).')
    p.add_argument("--count", type=int, default=1, help="How many cycles to run (default: 1).")
    p.add_argument("--interval", type=float, default=0.0, help="Seconds between cycles (default: 0).")

    # BrainFlow options (only used if --brainflow)
    p.add_argument("--bf-board-id", type=int, default=0, help="BrainFlow board_id (0 = Synthetic board).")
    p.add_argument("--bf-serial-port", default=None, help="Optional serial port for supported boards.")
    p.add_argument("--bf-seconds", type=float, default=2.0, help="Seconds to stream before taking a snapshot.")

    # LSL options (only used if --lsl)
    p.add_argument("--lsl-name", default=None, help="Resolve LSL stream by name.")
    p.add_argument("--lsl-type", default=None, help='Resolve LSL stream by type (common: "EEG").')
    p.add_argument("--lsl-timeout", type=float, default=5.0, help="Seconds to wait while resolving stream.")
    p.add_argument("--lsl-seconds", type=float, default=2.0, help="Seconds to snapshot the stream for a packet.")

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    pipe = SynapDrivePipeline()

    for i in range(args.count):
        if args.text is not None:
            out = pipe.run_text_command(args.text, image_label=args.image)

        elif args.brainflow:
            from synapdrive_ai.integrations.brainflow_adapter import BrainFlowIntentSource

            src = BrainFlowIntentSource(
                board_id=args.bf_board_id,
                serial_port=args.bf_serial_port,
                stream_seconds=args.bf_seconds,
            )
            intent_packet = src.next_intent_packet()
            out = pipe._run_common(intent_packet, image_label=args.image)

        elif args.lsl:
            from synapdrive_ai.integrations.lsl_adapter import LSLIntentSource

            src = LSLIntentSource(
                stream_name=args.lsl_name,
                stream_type=args.lsl_type,
                resolve_timeout_s=args.lsl_timeout,
                snapshot_seconds=args.lsl_seconds,
            )
            intent_packet = src.next_intent_packet()
            out = pipe._run_common(intent_packet, image_label=args.image)

        else:
            label = None if args.signal == "RANDOM" else args.signal
            out = pipe.run_signal_event(label=label, image_label=args.image)

        _print_summary(out)

        if i < args.count - 1 and args.interval > 0:
            time.sleep(args.interval)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

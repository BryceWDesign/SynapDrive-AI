from __future__ import annotations

import argparse
import json
import time

from synapdrive_ai.pipeline import SynapDrivePipeline
from synapdrive_ai.replay.recording import JsonlRecorder, iter_jsonl, make_record


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
    print("\nruntime:")
    print(json.dumps(out.get("runtime", {}), indent=2, default=str))
    print("\nreality:")
    print(json.dumps(out.get("reality", {}), indent=2, default=str))
    print("\nassurance:")
    print(json.dumps(out.get("assurance", {}), indent=2, default=str))
    print("\nevidence:")
    print(json.dumps(out.get("evidence", {}), indent=2, default=str))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="synapdrive-ai",
        description="SynapDrive-AI simulation CLI (canonical pipeline).",
    )

    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--text",
        help='Run one cycle using caller-declared command text (e.g. "move left", "stop").',
    )
    mode.add_argument(
        "--signal",
        nargs="?",
        const="RANDOM",
        help="Run one cycle using an explicit synthetic fixture label (or seeded RANDOM).",
    )
    mode.add_argument(
        "--brainflow",
        action="store_true",
        help="Acquire one BrainFlow window. CLI has no implicit decoder, so this path abstains.",
    )
    mode.add_argument(
        "--lsl",
        action="store_true",
        help="Acquire one LSL window. CLI has no implicit decoder, so this path abstains.",
    )
    mode.add_argument("--replay", help="Replay JSONL records from a prior --record run.")

    p.add_argument(
        "--image",
        default=None,
        help=(
            "Optional caller-declared context label (road, hazard, person, vehicle); "
            "no image model runs."
        ),
    )
    p.add_argument("--count", type=int, default=1, help="How many cycles to run (default: 1).")
    p.add_argument(
        "--interval", type=float, default=0.0, help="Seconds between cycles (default: 0)."
    )

    # Record/replay
    p.add_argument(
        "--record", default=None, help="Write each cycle to a JSONL file (reproducible runs)."
    )
    p.add_argument(
        "--evidence-out",
        default=None,
        help="Export the tamper-evident cycle ledger to JSONL after the run.",
    )
    p.add_argument(
        "--errp-probability",
        type=float,
        default=None,
        help="Optional externally-derived error-potential probability for feedback testing.",
    )
    p.add_argument(
        "--reject-feedback",
        action="store_true",
        help="Explicitly mark the action feedback as rejected.",
    )
    p.add_argument(
        "--no-delay",
        action="store_true",
        help="Disable actuation sleep (best for CI, tests, replay).",
    )

    # BrainFlow options
    p.add_argument("--bf-board-id", type=int, default=-1)
    p.add_argument("--bf-serial-port", default=None)
    p.add_argument("--bf-seconds", type=float, default=2.0)

    # LSL options
    p.add_argument("--lsl-name", default=None)
    p.add_argument("--lsl-type", default=None)
    p.add_argument("--lsl-timeout", type=float, default=5.0)
    p.add_argument("--lsl-seconds", type=float, default=2.0)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    simulate_delay = not args.no_delay
    pipe = SynapDrivePipeline(simulate_delay=simulate_delay)

    recorder = JsonlRecorder(args.record) if args.record else None
    feedback = {}
    if args.errp_probability is not None:
        feedback["errp_probability"] = args.errp_probability
    if args.reject_feedback:
        feedback["accepted"] = False
    feedback = feedback or None

    if args.replay:
        # Replay should be deterministic + fast
        pipe = SynapDrivePipeline(simulate_delay=False)
        for rec in iter_jsonl(args.replay):
            intent_packet = rec["intent_packet"]
            image_label = rec.get("image_label")
            out = pipe.run_intent_packet(
                intent_packet, image_label=image_label, feedback=feedback
            )
            _print_summary(out)
        if args.evidence_out:
            pipe.evidence.export_jsonl(args.evidence_out)
        return 0

    for i in range(args.count):
        mode = ""
        raw_input = {}
        intent_packet = None

        if args.text is not None:
            mode = "text"
            raw_input = {"text": args.text}
            out = pipe.run_text_command(
                args.text, image_label=args.image, feedback=feedback
            )

        elif args.brainflow:
            mode = "brainflow"
            from synapdrive_ai.integrations.brainflow_adapter import BrainFlowIntentSource

            src = BrainFlowIntentSource(
                board_id=args.bf_board_id,
                serial_port=args.bf_serial_port,
                stream_seconds=args.bf_seconds,
            )
            intent_packet = src.next_intent_packet()
            raw_input = {"brainflow": {"board_id": args.bf_board_id, "seconds": args.bf_seconds}}
            out = pipe.run_intent_packet(
                intent_packet, image_label=args.image, feedback=feedback
            )

        elif args.lsl:
            mode = "lsl"
            from synapdrive_ai.integrations.lsl_adapter import LSLIntentSource

            src = LSLIntentSource(
                stream_name=args.lsl_name,
                stream_type=args.lsl_type,
                resolve_timeout_s=args.lsl_timeout,
                snapshot_seconds=args.lsl_seconds,
            )
            intent_packet = src.next_intent_packet()
            raw_input = {
                "lsl": {"name": args.lsl_name, "type": args.lsl_type, "seconds": args.lsl_seconds}
            }
            out = pipe.run_intent_packet(
                intent_packet, image_label=args.image, feedback=feedback
            )

        else:
            mode = "signal"
            label = None if args.signal == "RANDOM" else args.signal
            raw_input = {"label": label or "RANDOM"}
            out = pipe.run_signal_event(
                label=label, image_label=args.image, feedback=feedback
            )

        _print_summary(out)

        # Record the original packet when possible; otherwise store the optimized packet.
        if recorder:
            if intent_packet is None:
                intent_packet = out.get("intent", {}) or {}
            recorder.append(
                make_record(
                    mode=mode,
                    raw_input=raw_input,
                    image_label=args.image,
                    intent_packet=intent_packet,
                    pipeline_output=out,
                )
            )

        if i < args.count - 1 and args.interval > 0:
            time.sleep(args.interval)

    if args.evidence_out:
        pipe.evidence.export_jsonl(args.evidence_out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

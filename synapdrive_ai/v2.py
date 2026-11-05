"""Executable local demonstrations and fixed recorded-EEG evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def demo():
    from synapdrive_ai.access import AccessSession
    from synapdrive_ai.adaptation.lifecycle import ModelLifecycle
    from synapdrive_ai.pipeline import SynapDrivePipeline
    from synapdrive_ai.replay.recording import replay_capsule
    from synapdrive_ai.simulation import Plant, PlantEndpoint

    pipe = SynapDrivePipeline(False)
    rejected = pipe.run_text_command("do not move left")
    action = pipe.run_text_command("move left", feedback={"accepted": False})
    replay = replay_capsule(action["replay_context"])
    plant = Plant(position=0.5, velocity=0.8)
    recovering = SynapDrivePipeline(False, fallback_controller=plant.fallback)
    recovering.router = PlantEndpoint(plant)
    fallback = recovering.run_text_command("unknown")
    replay_capsule(fallback["replay_context"])
    access = AccessSession(pipe)
    access.edit_draft("Please move the chair closer.")
    access.propose("Please move the chair now.")
    approved = access.approve()
    output = access.commit_local(approved)
    lifecycle = ModelLifecycle("baseline")
    lifecycle.propose("candidate", ("feedback-1",))
    lifecycle.evaluate(
        "candidate",
        audit_id="independent-software-fixture",
        baseline_utility=0.5,
        candidate_utility=0.6,
        baseline_unsafe=1,
        candidate_unsafe=0,
        samples=20,
    )
    lifecycle.promote("candidate")
    rolled_back = lifecycle.contradict("feedback-1")
    return {
        "schema": "synapdrive.demo.v2",
        "evidence": "software-and-declared-plant-simulation",
        "negated_command": rejected["status"],
        "normal_action": action["status"],
        "rejected_feedback_memory": action["memory"]["state"],
        "replayed_memory": replay["memory"]["state"],
        "fallback": fallback["result"]["fallback_result"],
        "exact_approved_local_output": output,
        "rollback": rolled_back,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["demo", "eeg"])
    parser.add_argument(
        "--dataset", type=Path, default=Path(__file__).parent / "assets/recorded_eeg.npz"
    )
    parser.add_argument("--out", type=Path, default=Path("results/eeg-reproduced"))
    args = parser.parse_args()
    if args.command == "demo":
        print(json.dumps(demo(), indent=2, allow_nan=False))
    else:
        # Importable within installed wheels as well as repository checkouts.
        from synapdrive_ai.recorded_eeg import evaluate

        result = evaluate(args.dataset, args.out)
        print(json.dumps({k: v for k, v in result.items() if k != "participants"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

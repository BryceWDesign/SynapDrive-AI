from __future__ import annotations

import argparse
import json

import numpy as np

from synapdrive_ai.bci.intent_generator import generate_intent
from synapdrive_ai.pipeline import SynapDrivePipeline
from synapdrive_ai.stress.campaign import StressCampaign
from synapdrive_ai.stress.faults import FaultInjector


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Run deterministic SynapDrive signal fault-injection campaign."
    )
    parser.add_argument("--runs", type=int, default=25)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--sampling-rate", type=float, default=256.0)
    args = parser.parse_args(argv)
    rng = np.random.default_rng(args.seed)
    n = int(args.sampling_rate * 2)
    t = np.arange(n) / args.sampling_rate
    base = np.sin(2 * np.pi * 20 * t) + 0.05 * rng.normal(size=n)
    injector = FaultInjector(args.seed)
    trials = []
    for i in range(args.runs):
        mode = i % 4
        if mode == 0:
            res = injector.dropout(base, min(0.95, 0.25 + 0.03 * i))
        elif mode == 1:
            res = injector.line_noise(base, args.sampling_rate, amplitude=1.5)
        elif mode == 2:
            res = injector.clip(base, quantile=0.6)
        else:
            res = injector.gaussian_noise(base, sigma=1.0)
        trials.append((str(res.metadata["fault"]), res.signal))

    pipe = SynapDrivePipeline(simulate_delay=False)
    campaign = StressCampaign(
        args.sampling_rate,
        min_quality=pipe.runtime.policy.min_signal_quality,
    )

    def callback(_signal, quality_score: float) -> bool:
        packet = generate_intent("move left")
        packet["signal_quality"] = quality_score
        packet["source"] = "stress-campaign"
        return pipe.run_intent_packet(packet)["status"] == "blocked"

    report = campaign.run(trials, callback)
    print(json.dumps(report.to_dict(), indent=2))
    return 1 if report.invariant_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

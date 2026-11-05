"""Independent software/fault/plant validation; no physiological success claim."""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from synapdrive_ai.bci.intent_generator import generate_intent
from synapdrive_ai.neuro.signal_quality import SignalQualityAnalyzer
from synapdrive_ai.pipeline import SynapDrivePipeline
from synapdrive_ai.replay.recording import replay_capsule
from synapdrive_ai.simulation import Plant, PlantEndpoint
from synapdrive_ai.v2 import demo


def validate():
    checks = {}
    output = demo()
    checks["executable_local_tasks"] = (
        output["negated_command"] == "blocked"
        and output["normal_action"] == "success"
        and output["rollback"] == "baseline"
    )
    rng = np.random.default_rng(20261102)
    fault_cases = []
    for scenario in (
        "clean",
        "flatline",
        "nonfinite",
        "dropout",
        "line-noise",
        "single-channel-flat",
    ):
        for repetition in range(20):
            data = rng.normal(0, 1e-5, (8, 512))
            if scenario == "flatline":
                data[:] = 1e-5
            elif scenario == "nonfinite":
                data[repetition % 8, 10] = np.nan
            elif scenario == "dropout":
                data[:, 50:350] = 0
            elif scenario == "line-noise":
                data[:] = 1e-5 * np.sin(2 * np.pi * 60 * np.arange(512) / 256)
            elif scenario == "single-channel-flat":
                data[repetition % 8] = 1e-5
            pipe = SynapDrivePipeline(False)
            packet = generate_intent("move left")
            packet["signal_quality"] = SignalQualityAnalyzer(256).analyze(data).score
            out = pipe.run_intent_packet(packet)
            expected = "success" if scenario == "clean" else "blocked"
            passed = out["status"] == expected and len(pipe.get_action_log()) == int(
                expected == "success"
            )
            fault_cases.append(
                {
                    "scenario": scenario,
                    "trial": repetition,
                    "expected": expected,
                    "observed": out["status"],
                    "passed": passed,
                }
            )
    checks["independent_fault_oracle"] = all(c["passed"] for c in fault_cases)
    plants = []
    for _ in range(1000):
        plant = Plant(position=float(rng.uniform(-0.9, 0.9)), velocity=float(rng.uniform(-1, 1)))
        if not plant.recoverable():
            continue
        initial = {"position": plant.position, "velocity": plant.velocity}
        result = plant.fallback()
        plants.append(
            {
                "initial": initial,
                "result": result,
                "passed": result["status"] == "stopped" and result["inside"],
            }
        )
    checks["independent_recovery_oracle"] = bool(plants) and all(c["passed"] for c in plants)
    # Actual endpoint is attached to canonical permissions, dispatch and evidence.
    plant = Plant()
    pipe = SynapDrivePipeline(False, fallback_controller=plant.fallback)
    pipe.router = PlantEndpoint(plant)
    for _ in range(150):
        out = pipe.run_text_command("move right")
        if not abs(plant.position) <= plant.limit:
            break
    checks["canonical_plant_envelope"] = abs(plant.position) <= plant.limit
    checks["plant_capsule_replay"] = (
        replay_capsule(out["replay_context"])["status"] == out["status"]
    )
    pipe = SynapDrivePipeline(False)
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=8) as pool:
        outputs = list(pool.map(lambda _: pipe.run_text_command("move left"), range(800)))
    elapsed = time.perf_counter() - start
    checks["800_concurrent_cycles"] = (
        all(o["status"] == "success" for o in outputs)
        and len(pipe.get_action_log()) == len(pipe.evidence.chain.entries()) == 800
        and pipe.evidence.verify(pipe.evidence.chain.entries())
    )
    return {
        "schema": "synapdrive.release-validation.v2",
        "software_validation_passed": all(checks.values()),
        "scope": "local software, independent labeled fault fixtures and bounded 1D simulation",
        "checks": checks,
        "fault_cases": fault_cases,
        "recovery_cases": len(plants),
        "recovery_failures": sum(not c["passed"] for c in plants),
        "concurrency": {"threads": 8, "cycles": 800, "elapsed_s": elapsed},
        "remote_ci_verified": False,
        "physical_safety_verified": False,
        "clinical_benefit_verified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("results/software-validation.json"))
    args = parser.parse_args()
    report = validate()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "fault_cases"}, indent=2))
    return 0 if report["software_validation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json

from synapdrive_ai.benchmarking.dataset import load_npz_dataset
from synapdrive_ai.benchmarking.decoders import (
    EnsembleDecoder,
    RiemannianCentroidDecoder,
    SpectralCentroidDecoder,
)
from synapdrive_ai.benchmarking.evaluation import evaluate_decoder, run_arena


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark SynapDrive decoders on an explicit labeled NPZ dataset."
    )
    parser.add_argument("dataset")
    parser.add_argument(
        "--decoder",
        choices=("spectral", "riemannian", "ensemble", "all"),
        default="all",
    )
    parser.add_argument("--test-fraction", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--abstain", type=float, default=0.55)
    args = parser.parse_args(argv)
    dataset = load_npz_dataset(args.dataset)

    if args.decoder == "all":
        reports = run_arena(
            dataset,
            test_fraction=args.test_fraction,
            seed=args.seed,
            abstain_threshold=args.abstain,
        )
        print(json.dumps({"arena": [report.to_dict() for report in reports]}, indent=2))
        return 0

    if args.decoder == "spectral":
        decoder = SpectralCentroidDecoder()
    elif args.decoder == "riemannian":
        decoder = RiemannianCentroidDecoder()
    else:
        decoder = EnsembleDecoder(
            [SpectralCentroidDecoder(), RiemannianCentroidDecoder()]
        )
    report = evaluate_decoder(
        decoder,
        dataset,
        test_fraction=args.test_fraction,
        seed=args.seed,
        abstain_threshold=args.abstain,
    )
    print(json.dumps(report.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

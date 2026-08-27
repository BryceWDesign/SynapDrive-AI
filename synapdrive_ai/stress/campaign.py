from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable, Iterable, List

import numpy as np

from synapdrive_ai.neuro.signal_quality import SignalQualityAnalyzer


@dataclass(frozen=True)
class CampaignTrial:
    trial: int
    fault: str
    quality_score: float
    quality_state: str
    expected_block: bool
    blocked: bool
    invariant_passed: bool


@dataclass(frozen=True)
class CampaignReport:
    total_trials: int
    invariant_passes: int
    invariant_failures: int
    trials: List[CampaignTrial]

    def to_dict(self):
        return {
            "total_trials": self.total_trials,
            "invariant_passes": self.invariant_passes,
            "invariant_failures": self.invariant_failures,
            "trials": [asdict(t) for t in self.trials],
        }


class StressCampaign:
    """Runs faulted signals through a supplied analysis callback and checks fail-closed behavior.

    callback(signal, quality_score) must return True when the action path is blocked.
    """

    def __init__(self, sampling_rate: float, min_quality: float = 0.35) -> None:
        self.sampling_rate = float(sampling_rate)
        self.min_quality = float(min_quality)
        self.quality = SignalQualityAnalyzer(sampling_rate)

    def run(
        self,
        trials: Iterable[tuple[str, np.ndarray]],
        callback: Callable[[np.ndarray, float], bool],
    ) -> CampaignReport:
        results: List[CampaignTrial] = []
        for idx, (fault_name, signal) in enumerate(trials, 1):
            quality = self.quality.analyze(signal)
            expected_block = quality.score < self.min_quality
            blocked = bool(callback(signal, quality.score))
            invariant = (not expected_block) or blocked
            results.append(
                CampaignTrial(
                    idx,
                    fault_name,
                    quality.score,
                    quality.state,
                    expected_block,
                    blocked,
                    invariant,
                )
            )
        passes = sum(1 for t in results if t.invariant_passed)
        return CampaignReport(len(results), passes, len(results) - passes, results)

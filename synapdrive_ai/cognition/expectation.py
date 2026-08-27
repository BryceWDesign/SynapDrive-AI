from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThreeWayDelta:
    machine_reality: float
    human_reality: float | None
    machine_human: float | None


class ExpectationReconciler:
    """Computes machine/human/reality deltas for scalar expected success.

    Human expectation is optional and must be supplied explicitly; it is never inferred from
    neural data by this class.
    """

    def compare(
        self,
        machine_expected_success: float,
        observed_success: bool,
        human_expected_success: float | None = None,
    ) -> ThreeWayDelta:
        machine = max(0.0, min(1.0, float(machine_expected_success)))
        reality = float(bool(observed_success))
        if human_expected_success is None:
            return ThreeWayDelta(abs(machine - reality), None, None)
        human = max(0.0, min(1.0, float(human_expected_success)))
        return ThreeWayDelta(
            abs(machine - reality),
            abs(human - reality),
            abs(machine - human),
        )

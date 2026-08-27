from __future__ import annotations

from typing import Any, Dict

from synapdrive_ai.bci.signal_simulator import BrainSignalSimulator
from synapdrive_ai.pipeline import SynapDrivePipeline


class SynapDriveBridge:
    """Backward-compatible streaming bridge into the canonical governed pipeline.

    The bridge is intentionally simulation-only. It subscribes to the bundled synthetic
    signal generator and forwards the *declared synthetic label* through the canonical
    pipeline. There is no parallel actuator or bypass around runtime governance.
    """

    def __init__(self, simulate_delay: bool = False) -> None:
        self.simulator = BrainSignalSimulator()
        self.pipeline = SynapDrivePipeline(simulate_delay=simulate_delay)
        self.running = False
        self._cycle_log: list[Dict[str, Any]] = []

    @property
    def reasoner(self):
        """Compatibility access to the pipeline's labeled-signal mapper."""
        return self.pipeline.reasoner

    def _signal_handler(self, label, _signal_data) -> None:
        result = self.pipeline.run_signal_event(label=label)
        self._cycle_log.append(result)

    def start(self, interval: float = 1.0) -> None:
        self.simulator.subscribe(self._signal_handler)
        self.simulator.start_real_time_stream(interval=interval)
        self.running = True

    def stop(self) -> None:
        self.simulator.stop()
        self.running = False

    def get_action_log(self):
        return self.pipeline.get_action_log()

    def get_cycle_log(self) -> list[Dict[str, Any]]:
        return list(self._cycle_log)

    def get_assurance_report(self) -> Dict[str, Any]:
        return self.pipeline.get_assurance_report()

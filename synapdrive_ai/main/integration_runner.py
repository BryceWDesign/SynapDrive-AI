from __future__ import annotations

from typing import Any, Dict, Optional

from synapdrive_ai.pipeline import SynapDrivePipeline


class SynapDriveExecutor:
    """
    Compatibility wrapper around the canonical SynapDrivePipeline.

    Older examples import SynapDriveExecutor directly. Keeping this class as a thin
    wrapper prevents a second, drifting implementation of the same safety loop.
    """

    def __init__(self, simulate_delay: bool = True) -> None:
        self.pipeline = SynapDrivePipeline(simulate_delay=simulate_delay)

    def run_once(
        self, simulated_input: str, simulated_image: Optional[str] = None
    ) -> Dict[str, Any]:
        return self.pipeline.run_text_command(simulated_input, image_label=simulated_image)

    def get_action_log(self):
        return self.pipeline.get_action_log()

    def get_assurance_report(self) -> Dict[str, Any]:
        return self.pipeline.get_assurance_report()

from __future__ import annotations

import threading
import time

from synapdrive_ai.core.logger import SynapLogger
from synapdrive_ai.interface.bridge import SynapDriveBridge


class SynapDriveDashboard:
    """Console monitor for the canonical governed simulation bridge.

    Historical versions contained a fabricated "cloud" router and a feedback learner that
    updated weights outside the governed adaptation path. Both have been removed. This
    dashboard only displays results already produced by the canonical runtime.
    """

    def __init__(self) -> None:
        self.bridge = SynapDriveBridge(simulate_delay=False)
        self.logger = SynapLogger()
        self.running = False
        self._seen_cycles = 0

    def _monitor(self) -> None:
        while self.running:
            cycles = self.bridge.get_cycle_log()
            while self._seen_cycles < len(cycles):
                latest = cycles[self._seen_cycles]
                self._seen_cycles += 1
                intent = latest.get("intent", {}) or {}
                result = latest.get("result", {}) or {}
                reality = latest.get("reality", {}) or {}
                runtime = latest.get("runtime", {}) or {}

                print("\n--- SynapDrive-AI Governed Snapshot ---")
                print(
                    f"Intent: {intent.get('intent', 'unknown')} | "
                    f"confidence={float(intent.get('confidence', 0.0)):.3f}"
                )
                print(
                    f"Runtime: {'allowed' if runtime.get('allowed') else 'blocked'} | "
                    f"reason={runtime.get('reason', 'unknown')}"
                )
                print(
                    f"Result: {result.get('status', 'unknown')} | "
                    f"reality_aligned={reality.get('aligned', False)}"
                )
            time.sleep(0.2)

    def launch(self) -> None:
        self.logger.info("Starting SynapDrive-AI governed console dashboard")
        self.bridge.start()
        self.running = True
        thread = threading.Thread(target=self._monitor, daemon=True)
        thread.start()

    def shutdown(self) -> None:
        self.running = False
        self.bridge.stop()
        self.logger.info("Dashboard stopped")

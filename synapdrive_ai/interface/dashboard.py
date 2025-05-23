# synapdrive_ai/interface/dashboard.py

import time
import threading
from synapdrive_ai.interface.bridge import SynapDriveBridge
from synapdrive_ai.agi.feedback_learning import FeedbackLearner
from synapdrive_ai.cloud.cloud_stub import CloudControlStub
from synapdrive_ai.core.logger import SynapLogger

class SynapDriveDashboard:
    """
    Real-time console dashboard showing BCI input, AGI decision,
    actuator feedback, memory, and cloud control results.
    """

    def __init__(self):
        self.bridge = SynapDriveBridge()
        self.learner = FeedbackLearner(self.bridge.reasoner)
        self.cloud = CloudControlStub()
        self.logger = SynapLogger()
        self.running = False

    def _monitor(self):
        while self.running:
            log = self.bridge.get_action_log()
            if log:
                latest = log[-1]
                print("\n--- SynapDrive-AI Live Snapshot ---")
                print(f"🧠 Intent: {latest['intent']} | Conf: {latest['confidence']}")
                print(f"🤖 Result: {latest['status']} | Duration: {latest['duration']}s")
                print(f"📡 Source: {latest['source']}")
                print(f"🧬 Memory: {latest['memory']}")
                self.cloud.transmit_intent(latest)
                self.learner.apply_feedback(
                    {
                        "intent": latest["intent"],
                        "confidence": latest["confidence"],
                        "source": latest["source"],
                        "memory_context": []
                    },
                    latest
                )
                print(f"✅ Cloud Routed → {self.cloud.transmitted_packets[-1]['system']}")
            time.sleep(2)

    def launch(self):
        self.logger.info("Starting SynapDrive-AI dashboard...")
        self.bridge.start()
        self.running = True
        t = threading.Thread(target=self._monitor)
        t.daemon = True
        t.start()

    def shutdown(self):
        self.running = False
        self.bridge.stop()
        self.logger.info("Dashboard stopped.")

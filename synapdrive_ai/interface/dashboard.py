import threading
import time

from synapdrive_ai.agi.feedback_learning import FeedbackLearner
from synapdrive_ai.cloud.cloud_stub import CloudControlStub
from synapdrive_ai.core.logger import SynapLogger
from synapdrive_ai.interface.bridge import SynapDriveBridge


class SynapDriveDashboard:
    """
    Real-time console dashboard showing BCI input, AGI decision,
    actuator feedback, memory, and cloud control results.

    This must never crash on schema drift — we use .get() defaults everywhere.
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

                intent = latest.get("intent", "unknown")
                conf = latest.get("confidence", 0.0)
                status = latest.get("status", "unknown")
                duration = latest.get("duration", 0.0)
                source = latest.get("source", "unknown")
                memory = latest.get("memory", latest.get("memory_context", []))

                print("\n--- SynapDrive-AI Live Snapshot ---")
                print(f"🧠 Intent: {intent} | Conf: {conf}")
                print(f"🤖 Result: {status} | Duration: {duration}s")
                print(f"📡 Source: {source}")
                print(f"🧬 Memory: {memory}")

                # Cloud wants intent/confidence/source
                if intent != "unknown":
                    self.cloud.transmit_intent(
                        {
                            "intent": intent,
                            "confidence": conf,
                            "source": source,
                            "memory_context": latest.get("memory_context", []),
                        }
                    )

                # Feedback learner expects (intent_packet, result)
                self.learner.apply_feedback(
                    {
                        "intent": intent,
                        "confidence": conf,
                        "source": source,
                        "memory_context": [],
                    },
                    latest,
                )

                if self.cloud.transmitted_packets:
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

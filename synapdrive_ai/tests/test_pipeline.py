# synapdrive_ai/tests/test_pipeline.py

from synapdrive_ai.interface.bridge import SynapDriveBridge
from synapdrive_ai.agi.feedback_learning import FeedbackLearner
import time

def test_synapdrive_pipeline(runtime=10):
    """
    Runs a test of the full SynapDrive pipeline with feedback learning.
    Simulates brain activity, AGI cognition, actuation, and adaptation.

    Args:
        runtime (int): Duration in seconds to run the test.
    """
    print("[TEST] Starting full system test...")
    bridge = SynapDriveBridge()
    feedback_module = FeedbackLearner(bridge.reasoner)
    bridge.start(interval=1.0)

    start_time = time.time()
    try:
        while time.time() - start_time < runtime:
            log = bridge.get_action_log()
            if log:
                last_packet = log[-1]
                # Reconstruct original intent_packet for testing
                intent_packet = {
                    "intent": last_packet["intent"],
                    "confidence": last_packet["confidence"],
                    "source": "test_source",
                    "memory_context": []
                }
                feedback_module.apply_feedback(intent_packet, last_packet)
                print(f"[TEST] Intent: {last_packet['intent']} | "
                      f"Conf: {round(last_packet['confidence'], 2)} | "
                      f"Adjusted Priority: {bridge.reasoner.intent_weights.get('test_source', {}).get('priority')}")
            time.sleep(1.0)
    finally:
        bridge.stop()
        print("[TEST] System test complete.")

if __name__ == "__main__":
    test_synapdrive_pipeline(runtime=15)

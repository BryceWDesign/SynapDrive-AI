# synapdrive_ai/dashboard/realtime_ui.py

import time
from synapdrive_ai.interface.bridge import SynapDriveBridge

def run_realtime_console(duration=10):
    """
    Runs the SynapDrive-AI system for a fixed duration and displays
    real-time system status in the terminal.

    Args:
        duration (int): Time in seconds to run the demo.
    """
    bridge = SynapDriveBridge()
    bridge.start(interval=1.0)

    start_time = time.time()
    try:
        while time.time() - start_time < duration:
            log = bridge.get_action_log()
            if log:
                last_entry = log[-1]
                print(f"[UI] ⏱️ {round(time.time() - start_time, 2)}s | "
                      f"Intent: {last_entry['intent']} | "
                      f"Confidence: {round(last_entry['confidence'], 2)}")
            time.sleep(0.5)
    finally:
        bridge.stop()
        print("[UI] ✅ System run complete.")

if __name__ == "__main__":
    run_realtime_console(duration=15)

# synapdrive_ai/interface/bridge.py

from synapdrive_ai.bci.signal_simulator import BrainSignalSimulator
from synapdrive_ai.agi.core_reasoning import AGICoreReasoner
from synapdrive_ai.control.actuation_engine import ActuationEngine
import threading

class SynapDriveBridge:
    """
    Integration layer that bridges brain signal simulator, AGI reasoning core,
    and control actuation engine.

    Simulates a closed-loop system where brain signals drive cognition,
    which in turn drives real-world control responses.
    """

    def __init__(self):
        self.simulator = BrainSignalSimulator()
        self.reasoner = AGICoreReasoner()
        self.actuator = ActuationEngine()
        self.running = False

    def _signal_handler(self, label, signal_data):
        """Receive brain signal, reason about it, and pass intent to control."""
        intent_packet = self.reasoner.receive_signal(label, signal_data)
        result = self.actuator.execute_intent(intent_packet)
        print(f"[Bridge] Intent executed: {result}")

    def start(self, interval=1.0):
        """
        Start the full simulated pipeline with real-time signal streaming.
        """
        self.simulator.subscribe(self._signal_handler)
        self.simulator.start_real_time_stream(interval=interval)
        self.running = True
        print("[Bridge] SynapDrive-AI system started.")

    def stop(self):
        """
        Stop the simulated pipeline.
        """
        self.simulator.stop()
        self.running = False
        print("[Bridge] SynapDrive-AI system stopped.")

    def get_action_log(self):
        """
        Access logs from the actuation engine.
        """
        return self.actuator.get_action_log()

# synapdrive_ai/bci/signal_simulator.py

import numpy as np
import time
import threading

class BrainSignalSimulator:
    """
    Simulates EEG-like brain signals and emits structured event signals
    that can be consumed by AGI modules.

    Simulated 'thought events':
        - motor_intent: left_arm, right_arm, walk, stop
        - cognitive_intent: calculate, recall, explore

    Each signal has amplitude, frequency, and optional noise components.
    """

    def __init__(self, sampling_rate=256, noise_level=0.05):
        self.sampling_rate = sampling_rate  # in Hz
        self.noise_level = noise_level
        self.running = False
        self.subscribers = []

    def generate_waveform(self, frequency, duration=1.0):
        t = np.linspace(0, duration, int(self.sampling_rate * duration), endpoint=False)
        signal = np.sin(2 * np.pi * frequency * t)
        noise = np.random.normal(0, self.noise_level, signal.shape)
        return signal + noise

    def emit_event(self, label):
        """Emit a synthetic brain signal for a labeled thought event."""
        patterns = {
            "left_arm": 10,
            "right_arm": 12,
            "walk": 8,
            "stop": 3,
            "calculate": 25,
            "recall": 18,
            "explore": 30
        }
        if label not in patterns:
            raise ValueError(f"Unknown signal label: {label}")
        signal = self.generate_waveform(patterns[label])
        for callback in self.subscribers:
            callback(label, signal)

    def subscribe(self, callback):
        """Register a callback to receive signals: callback(label, signal)"""
        self.subscribers.append(callback)

    def start_real_time_stream(self, interval=1.0):
        """Starts a background thread that emits random events in real time."""
        self.running = True
        def stream_loop():
            event_labels = ["left_arm", "right_arm", "walk", "stop", "calculate", "recall", "explore"]
            while self.running:
                label = np.random.choice(event_labels)
                self.emit_event(label)
                time.sleep(interval)
        threading.Thread(target=stream_loop, daemon=True).start()

    def stop(self):
        """Stop the real-time simulation."""
        self.running = False

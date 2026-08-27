from __future__ import annotations

import threading
import time
from typing import Callable

import numpy as np


class BrainSignalSimulator:
    """Deterministic-by-seed EEG-like waveform fixture generator.

    Labels are injected ground truth for software testing. Generated waveforms are not
    asserted to reproduce physiological EEG or to validate a neural decoder.
    """

    EVENT_FREQUENCIES = {
        "left_arm": 10.0,
        "right_arm": 12.0,
        "walk": 8.0,
        "stop": 3.0,
        "calculate": 25.0,
        "recall": 18.0,
        "explore": 30.0,
    }

    def __init__(self, sampling_rate: int = 256, noise_level: float = 0.05, seed: int = 0):
        if sampling_rate <= 0:
            raise ValueError("sampling_rate must be > 0")
        if noise_level < 0:
            raise ValueError("noise_level must be >= 0")
        self.sampling_rate = int(sampling_rate)
        self.noise_level = float(noise_level)
        self.running = False
        self.subscribers: list[Callable[[str, np.ndarray], None]] = []
        self._rng = np.random.default_rng(seed)

    def generate_waveform(self, frequency: float, duration: float = 1.0) -> np.ndarray:
        if frequency <= 0 or duration <= 0:
            raise ValueError("frequency and duration must be > 0")
        t = np.linspace(0, duration, int(self.sampling_rate * duration), endpoint=False)
        signal = np.sin(2 * np.pi * frequency * t)
        noise = self._rng.normal(0.0, self.noise_level, signal.shape)
        return signal + noise

    def random_label(self) -> str:
        labels = tuple(self.EVENT_FREQUENCIES)
        return str(self._rng.choice(labels))

    def emit_event(self, label: str) -> None:
        if label not in self.EVENT_FREQUENCIES:
            raise ValueError(f"Unknown signal label: {label}")
        signal = self.generate_waveform(self.EVENT_FREQUENCIES[label])
        for callback in tuple(self.subscribers):
            callback(label, signal)

    def subscribe(self, callback: Callable[[str, np.ndarray], None]) -> None:
        self.subscribers.append(callback)

    def start_real_time_stream(self, interval: float = 1.0) -> None:
        if interval <= 0:
            raise ValueError("interval must be > 0")
        self.running = True

        def stream_loop() -> None:
            while self.running:
                self.emit_event(self.random_label())
                time.sleep(interval)

        threading.Thread(target=stream_loop, daemon=True).start()

    def stop(self) -> None:
        self.running = False

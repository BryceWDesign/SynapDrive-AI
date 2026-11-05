"""Independent one-dimensional plant and recovery monitor for simulation only.

Position limit ±1 m, bounded |velocity| <= 1 m/s, guaranteed brake 1 m/s²,
monitor/actuator delay <= .04s, observation position error <= .01m.
These declared experiment assumptions are not hardware measurements.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from synapdrive_ai.action.decision_router import DecisionRouter


@dataclass
class Plant:
    position: float = 0.0
    velocity: float = 0.0
    dt: float = 0.02
    limit: float = 1.0
    brake: float = 1.0
    delay: float = 0.04
    observation_error: float = 0.01
    steps: int = 0

    def __post_init__(self):
        values = (
            self.position,
            self.velocity,
            self.dt,
            self.limit,
            self.brake,
            self.delay,
            self.observation_error,
        )
        if (
            not all(math.isfinite(v) for v in values)
            or self.dt <= 0
            or self.limit <= 0
            or not 0 < self.brake <= 1
            or self.delay < 0
            or self.observation_error < 0
            or abs(self.velocity) > 1
        ):
            raise ValueError("invalid plant state or bounds")

    def recoverable(self, position=None, velocity=None):
        x = self.position if position is None else position
        v = self.velocity if velocity is None else velocity
        distance = (
            v * v / (2 * self.brake) + abs(v) * (self.delay + self.dt) + self.observation_error
        )
        margin = self.limit - (x if v >= 0 else -x)
        return margin >= distance and abs(x) <= self.limit

    def step(self, acceleration: float, disturbance=0.0):
        if not math.isfinite(acceleration) or not math.isfinite(disturbance):
            raise ValueError("finite plant inputs required")
        if abs(disturbance) > 0.1:
            raise ValueError("disturbance exceeds declared experiment bound")
        # Independent integrator; monitor does not directly assign outcome state.
        acceleration = min(1.0, max(-1.0, acceleration)) + disturbance
        self.position += self.velocity * self.dt + 0.5 * acceleration * self.dt * self.dt
        self.velocity = min(1.0, max(-1.0, self.velocity + acceleration * self.dt))
        self.steps += 1
        return {
            "position": self.position,
            "velocity": self.velocity,
            "inside": abs(self.position) <= self.limit,
        }

    def fallback(self, _action="hold_position"):
        if abs(self.velocity) <= 1e-10:
            return {
                "status": "stopped",
                "position": self.position,
                "velocity": self.velocity,
                "inside": abs(self.position) <= self.limit,
            }
        initial = self.velocity
        # Guaranteed net brake 1; no ongoing disturbance in this specific fallback oracle.
        while abs(self.velocity) > 1e-10 and self.steps < 100000:
            acceleration = -math.copysign(
                min(self.brake, abs(self.velocity) / self.dt), self.velocity
            )
            self.step(acceleration)
            if self.velocity * initial < 0 and abs(self.velocity) > 1e-10:
                raise AssertionError("brake overshot")
        return {
            "status": "stopped" if abs(self.velocity) <= 1e-10 else "timeout",
            "position": self.position,
            "velocity": self.velocity,
            "inside": abs(self.position) <= self.limit,
        }

    def command(self, packet):
        action = packet["intent"]
        if action in {"halt_all_motion", "hold_position"}:
            return self.fallback(action)
        acceleration = {
            "move_left": -1.0,
            "move_right": 1.0,
            "move_forward": 1.0,
            "move_backward": -1.0,
        }.get(action)
        if acceleration is None:
            return {"status": "unsupported", "intent": action}
        v = min(1.0, max(-1.0, self.velocity + acceleration * self.dt))
        x = self.position + self.velocity * self.dt + 0.5 * acceleration * self.dt * self.dt
        if not self.recoverable(x, v):
            out = self.fallback()
            return {**out, "controller": "baseline", "intent": action}
        return {
            **self.step(acceleration),
            "status": "advanced",
            "controller": "advanced",
            "intent": action,
        }


class PlantEndpoint(DecisionRouter):
    """Connect the independent plant to the canonical admission/execution pipeline."""

    def __init__(self, plant):
        self.plant = plant
        self.actions = []

    def route(self, packet):
        observed = self.plant.command(packet)
        result = {
            "status": "success" if observed["status"] in {"advanced", "stopped"} else "failed",
            "intent": packet["intent"],
            "confidence": packet["confidence"],
            "duration": self.plant.dt,
            "plant": observed,
        }
        self.actions.append(result)
        return result

    def get_action_log(self):
        return list(self.actions)

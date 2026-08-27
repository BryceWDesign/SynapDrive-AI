from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Tuple


@dataclass(frozen=True)
class ActionModel:
    name: str
    effects: Mapping[str, Any] = field(default_factory=dict)
    required: Mapping[str, Any] = field(default_factory=dict)
    predicted_risk: float = 0.0
    reversible: bool = True

    def __post_init__(self) -> None:
        if not 0.0 <= float(self.predicted_risk) <= 1.0:
            raise ValueError("predicted_risk must be in [0, 1]")


@dataclass(frozen=True)
class Prediction:
    action: str
    feasible: bool
    before: Dict[str, Any]
    after: Dict[str, Any]
    predicted_risk: float
    reversible: bool
    unmet_requirements: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "feasible": self.feasible,
            "before": self.before,
            "after": self.after,
            "predicted_risk": self.predicted_risk,
            "reversible": self.reversible,
            "unmet_requirements": list(self.unmet_requirements),
        }


class WorldModel:
    """Explicit symbolic action model with fail-closed behavior for unknown actions.

    Only registered action effects are predicted. An unregistered action is infeasible and
    receives maximal software risk rather than silently being treated as safe.
    """

    def __init__(self, state: Mapping[str, Any] | None = None) -> None:
        self.state: Dict[str, Any] = dict(state or {})
        self._actions: Dict[str, ActionModel] = {}

    def register(self, model: ActionModel) -> None:
        self._actions[model.name] = model

    def register_many(self, models: Iterable[ActionModel]) -> None:
        for model in models:
            self.register(model)

    def registered_actions(self) -> tuple[str, ...]:
        return tuple(sorted(self._actions))

    def predict(self, action: str) -> Prediction:
        before = deepcopy(self.state)
        model = self._actions.get(action)
        if model is None:
            return Prediction(
                action=action,
                feasible=False,
                before=before,
                after=deepcopy(before),
                predicted_risk=1.0,
                reversible=False,
                unmet_requirements=("unmodeled-action",),
            )

        unmet = tuple(
            key for key, expected in model.required.items() if self.state.get(key) != expected
        )
        after = deepcopy(before)
        if not unmet:
            after.update(dict(model.effects))
        return Prediction(
            action=action,
            feasible=not unmet,
            before=before,
            after=after,
            predicted_risk=float(model.predicted_risk),
            reversible=bool(model.reversible),
            unmet_requirements=unmet,
        )

    def commit(self, prediction: Prediction) -> None:
        if not prediction.feasible:
            raise ValueError("cannot commit an infeasible prediction")
        self.state = deepcopy(prediction.after)


def default_simulation_world_model() -> WorldModel:
    """Create the finite action model used by the bundled simulation runtime.

    Risk values are software policy fixtures for exercising routing behavior. They are not
    physical risk probabilities and are never presented as measured safety performance.
    """

    world = WorldModel({"mode": "manual", "last_action": "hold_position"})
    actions = [
        ActionModel("halt_all_motion", {"last_action": "halt_all_motion"}, predicted_risk=0.0),
        ActionModel("hold_position", {"last_action": "hold_position"}, predicted_risk=0.0),
        ActionModel("move_left", {"last_action": "move_left"}, predicted_risk=0.15),
        ActionModel("move_right", {"last_action": "move_right"}, predicted_risk=0.15),
        ActionModel("move_forward", {"last_action": "move_forward"}, predicted_risk=0.20),
        ActionModel("move_backward", {"last_action": "move_backward"}, predicted_risk=0.20),
        ActionModel("turn_left", {"last_action": "turn_left"}, predicted_risk=0.15),
        ActionModel("turn_right", {"last_action": "turn_right"}, predicted_risk=0.15),
        ActionModel("move_left_arm", {"last_action": "move_left_arm"}, predicted_risk=0.20),
        ActionModel("move_right_arm", {"last_action": "move_right_arm"}, predicted_risk=0.20),
        ActionModel("initiate_walk", {"last_action": "initiate_walk"}, predicted_risk=0.30),
        ActionModel("pick_up", {"last_action": "pick_up"}, predicted_risk=0.25),
        ActionModel("drop", {"last_action": "drop"}, predicted_risk=0.25),
        ActionModel(
            "initiate_computation",
            {"last_action": "initiate_computation"},
            predicted_risk=0.0,
        ),
        ActionModel("retrieve_memory", {"last_action": "retrieve_memory"}, predicted_risk=0.0),
        ActionModel("expand_context", {"last_action": "expand_context"}, predicted_risk=0.0),
        ActionModel(
            "switch_mode_manual",
            {"mode": "manual", "last_action": "switch_mode_manual"},
            predicted_risk=0.05,
        ),
        ActionModel(
            "switch_mode_assistive",
            {"mode": "assistive", "last_action": "switch_mode_assistive"},
            predicted_risk=0.10,
        ),
    ]
    world.register_many(actions)
    return world

from typing import cast

import pytest

from synapdrive_ai.cognition.expectation import ExpectationReconciler
from synapdrive_ai.cognition.planner import CandidateAction, CounterfactualPlanner
from synapdrive_ai.cognition.shared_autonomy import SharedAutonomyArbiter
from synapdrive_ai.cognition.world_model import ActionModel, WorldModel
from synapdrive_ai.runtime.governed_runtime import GovernedRuntime
from synapdrive_ai.runtime.shadow import ShadowController
from synapdrive_ai.runtime.simplex import SimplexController


def test_shared_autonomy_can_choose_lower_risk_machine_action():
    world = WorldModel({"goal": 0})
    world.register(ActionModel("direct", effects={"goal": 1}, predicted_risk=0.8))
    world.register(ActionModel("detour", effects={"goal": 1}, predicted_risk=0.1))
    arbiter = SharedAutonomyArbiter(CounterfactualPlanner(world))

    proposal = arbiter.propose(
        user_intent="direct",
        user_confidence=0.8,
        machine_candidates=[CandidateAction("detour", 0.95, 0.9)],
        goal=lambda state: float(
            cast(int | float, state.get("goal", 0))
        ),
    )

    assert proposal.selected_action == "detour"
    assert proposal.preserved_user_goal is True


def test_expectation_reconciler_requires_explicit_human_expectation():
    delta = ExpectationReconciler().compare(0.8, True)

    assert delta.machine_reality == pytest.approx(0.2)
    assert delta.human_reality is None


def test_expectation_three_way_delta():
    delta = ExpectationReconciler().compare(
        0.2,
        True,
        human_expected_success=0.9,
    )

    assert delta.machine_reality == 0.8
    assert delta.human_reality is not None
    assert delta.human_reality < delta.machine_reality
    assert delta.machine_human == pytest.approx(0.7)


def test_simplex_uses_reversionary_controller_when_blocked():
    runtime = GovernedRuntime()
    packet = {
        "intent": "move_left",
        "confidence": 0.1,
        "uncertainty": 0.1,
    }
    decision = runtime.assess(packet)

    simplex = SimplexController(
        lambda p: {
            "status": "success",
            "action": p["intent"],
        },
        lambda action: {
            "status": "safe-state",
            "action": action,
        },
    )

    out = simplex.execute(packet, decision)

    assert out.controller == "reversionary"
    assert out.result["action"] == "hold_position"


def test_simplex_uses_advanced_controller_when_allowed():
    runtime = GovernedRuntime()
    packet = {
        "intent": "move_left",
        "confidence": 0.95,
        "uncertainty": 0.1,
    }
    decision = runtime.assess(packet)

    simplex = SimplexController(
        lambda p: {
            "status": "success",
            "action": p["intent"],
        },
        lambda action: {
            "status": "safe-state",
            "action": action,
        },
    )

    assert simplex.execute(packet, decision).controller == "advanced"


def test_shadow_controller_never_executes_trusted_path():
    calls = []

    def policy(context):
        calls.append(context)
        return "experimental", {"score": 0.9}

    shadow = ShadowController(policy)
    result = shadow.evaluate("trusted", {"x": 1})

    assert result.shadow_action == "experimental"
    assert result.agreement is False
    assert len(calls) == 1
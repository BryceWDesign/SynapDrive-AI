from __future__ import annotations

import json

import pytest

from synapdrive_ai.cognition.world_model import ActionModel, WorldModel
from synapdrive_ai.governance.permission import PermissionGate
from synapdrive_ai.governance.policy import RuntimePolicy
from synapdrive_ai.runtime.governed_runtime import GovernedRuntime


def test_runtime_policy_rejects_bad_probability():
    with pytest.raises(ValueError):
        RuntimePolicy(min_confidence=1.2)


def test_runtime_policy_roundtrip_json(tmp_path):
    path = tmp_path / "policy.json"
    policy = RuntimePolicy(min_confidence=0.6)
    path.write_text(json.dumps(policy.to_dict()))
    assert RuntimePolicy.from_json(path).min_confidence == 0.6


def test_permission_safe_state_survives_revoke():
    gate = PermissionGate()
    gate.revoke_all()
    assert gate.evaluate("halt_all_motion").allowed is True
    assert gate.evaluate("move_left").allowed is False


def test_permission_deny_pattern():
    gate = PermissionGate()
    assert gate.evaluate("override_security_now").allowed is False


def test_runtime_blocks_low_confidence():
    rt = GovernedRuntime(policy=RuntimePolicy(min_confidence=0.7))
    out = rt.assess({"intent": "move_left", "confidence": 0.6, "uncertainty": 0.1})
    assert out.allowed is False
    assert "confidence-below-policy" in out.assessment.issues


def test_runtime_blocks_uncertainty():
    rt = GovernedRuntime(policy=RuntimePolicy(max_uncertainty=0.2))
    out = rt.assess({"intent": "move_left", "confidence": 0.9, "uncertainty": 0.5})
    assert out.allowed is False
    assert "uncertainty-above-policy" in out.assessment.issues


def test_runtime_blocks_signal_quality():
    rt = GovernedRuntime(policy=RuntimePolicy(min_signal_quality=0.8))
    out = rt.assess(
        {
            "intent": "move_left",
            "confidence": 0.9,
            "uncertainty": 0.1,
            "signal_quality": 0.2,
        }
    )
    assert out.allowed is False
    assert "signal-quality-below-policy" in out.assessment.issues


def test_runtime_world_precondition_failure():
    world = WorldModel({"armed": False})
    world.register(ActionModel("move_left", required={"armed": True}))
    rt = GovernedRuntime(world_model=world)
    out = rt.assess({"intent": "move_left", "confidence": 0.9, "uncertainty": 0.1})
    assert out.allowed is False
    assert "world-model-precondition-failed" in out.assessment.issues


def test_runtime_blocks_predicted_risk():
    world = WorldModel()
    world.register(ActionModel("move_left", predicted_risk=0.9))
    rt = GovernedRuntime(world_model=world)
    out = rt.assess({"intent": "move_left", "confidence": 0.9, "uncertainty": 0.1})
    assert out.allowed is False
    assert "predicted-risk-above-policy" in out.assessment.issues

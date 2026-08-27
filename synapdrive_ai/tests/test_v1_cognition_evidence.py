from __future__ import annotations

from typing import cast

from synapdrive_ai.assurance.hashchain import EvidenceHashChain
from synapdrive_ai.cognition.planner import CandidateAction, CounterfactualPlanner
from synapdrive_ai.cognition.world_model import ActionModel, WorldModel
from synapdrive_ai.memory.evidence_memory import EvidenceMemory
from synapdrive_ai.runtime.reality import RealityReconciler


def test_world_model_known_action_predicts_effects():
    world = WorldModel({"x": 0})
    world.register(ActionModel("right", effects={"x": 1}, predicted_risk=0.1))
    p = world.predict("right")
    assert p.after["x"] == 1
    assert world.state["x"] == 0


def test_world_model_commit_changes_state():
    world = WorldModel({"x": 0})
    world.register(ActionModel("right", effects={"x": 1}))
    world.commit(world.predict("right"))
    assert world.state["x"] == 1


def test_world_model_unknown_does_not_invent_effects():
    world = WorldModel({"x": 3})
    p = world.predict("unmodeled")
    assert p.after == {"x": 3}
    assert "unmodeled-action" in p.unmet_requirements


def test_counterfactual_planner_penalizes_risk():
    world = WorldModel({"goal": 0})
    world.register_many([
        ActionModel("safe", effects={"goal": 1}, predicted_risk=0.1),
        ActionModel("risky", effects={"goal": 1}, predicted_risk=0.9),
    ])
    planner = CounterfactualPlanner(world)
    choice = planner.rank([
        CandidateAction("safe", 1.0, 0.9),
        CandidateAction("risky", 1.0, 0.9),
    ], lambda s: float(cast(int | float, s.get("goal", 0))))
    assert choice.selected is not None
    assert choice.selected.action == "safe"


def test_evidence_hash_chain_verifies():
    chain = EvidenceHashChain()
    chain.append({"a": 1})
    chain.append({"b": 2})
    assert EvidenceHashChain.verify(chain.entries()) is True


def test_evidence_hash_chain_detects_tamper():
    chain = EvidenceHashChain()
    chain.append({"a": 1})
    rows = [e.to_dict() for e in chain.entries()]
    rows[0]["payload"]["a"] = 999
    assert EvidenceHashChain.verify(rows) is False


def test_evidence_memory_validates_aligned():
    memory = EvidenceMemory()
    row = memory.record(
        cycle_id="1",
        intent="left",
        confidence=0.8,
        outcome="success",
        aligned=True,
        reason="ok",
    )
    assert row.state == "validated"
    assert len(memory.validated_for_intent("left")) == 1


def test_evidence_memory_quarantines_contradiction():
    memory = EvidenceMemory()
    memory.record(
        cycle_id="1",
        intent="left",
        confidence=0.8,
        outcome="success",
        aligned=False,
        reason="ErrP",
    )
    assert len(memory.quarantined()) == 1
    assert memory.validated_for_intent("left") == []


def test_reality_reconciler_errp_contradicts_success():
    verdict = RealityReconciler().reconcile(
        predicted_success=0.9,
        result_packet={"status": "success"},
        feedback={"errp_probability": 0.95},
    )
    assert verdict.aligned is False
    assert verdict.outcome == "contradicted"


def test_reality_reconciler_explicit_rejection_wins():
    verdict = RealityReconciler().reconcile(
        predicted_success=0.9,
        result_packet={"status": "success"},
        feedback={"accepted": False},
    )
    assert verdict.aligned is False
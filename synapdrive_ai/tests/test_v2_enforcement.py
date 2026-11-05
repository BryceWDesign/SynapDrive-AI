from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

import numpy as np
import pytest

from synapdrive_ai.access import AccessSession
from synapdrive_ai.adaptation.lifecycle import ModelLifecycle
from synapdrive_ai.assurance.hashchain import EvidenceHashChain
from synapdrive_ai.bci.intent_generator import generate_intent
from synapdrive_ai.cognition.planner import CounterfactualPlanner
from synapdrive_ai.cognition.shared_autonomy import SharedAutonomyArbiter
from synapdrive_ai.cognition.world_model import ActionModel, WorldModel
from synapdrive_ai.neuro.session_analyzer import SessionAnalyzer
from synapdrive_ai.neuro.signal_quality import SignalQualityAnalyzer
from synapdrive_ai.neuro.task_planner import ExecutorBridge, TaskPlan, TaskStep
from synapdrive_ai.pipeline import SynapDrivePipeline
from synapdrive_ai.processing.intent_classifier import IntentClassifier
from synapdrive_ai.replay.recording import replay_capsule
from synapdrive_ai.runtime.dispatch import DispatchGate, DispatchJournal
from synapdrive_ai.runtime.simplex import SimplexController
from synapdrive_ai.simulation import Plant
from synapdrive_ai.v2 import demo


@pytest.mark.parametrize(
    "field",
    [
        "confidence",
        "signal_quality",
        "drift_score",
        "predicted_risk",
        "uncertainty",
        "required_confidence",
    ],
)
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, True, "0.9"])
def test_f01_invalid_numbers_never_dispatch(field, value):
    pipe = SynapDrivePipeline(False)
    packet = generate_intent("move left")
    packet[field] = value
    out = pipe.run_intent_packet(packet)
    assert out["status"] == "blocked"
    assert not pipe.get_action_log()
    json.dumps(out, allow_nan=False)


def test_f02_missing_source_cannot_act_then_crash():
    pipe = SynapDrivePipeline(False)
    out = pipe.run_intent_packet({"intent": "move_left", "confidence": 0.99})
    assert out["status"] == "blocked"
    assert not pipe.get_action_log()
    assert len(pipe.evidence.chain.entries()) == 1


def test_f03_distribution_and_uncertainty_are_enforced():
    pipe = SynapDrivePipeline(False)
    p = generate_intent("move left")
    p["probabilities"] = {"move_left": 0.0, "move_right": 1.0}
    assert pipe.run_intent_packet(p)["status"] == "blocked"
    p["probabilities"] = {"move_left": 0.5, "move_right": 0.5}
    p["uncertainty"] = 0.0
    assert pipe.run_intent_packet(p)["status"] == "blocked"
    assert not pipe.get_action_log()


@pytest.mark.parametrize("fault", ["flat", "nan", "line", "one-flat-channel", "dropout"])
def test_f04_f05_independent_fault_labels_block(fault):
    rng = np.random.default_rng(12)
    x = rng.normal(size=(8, 1024))
    if fault == "flat":
        x[:] = 1
    elif fault == "nan":
        x[0, 10] = np.nan
    elif fault == "line":
        x[:] = np.sin(2 * np.pi * 60 * np.arange(1024) / 256)
    elif fault == "one-flat-channel":
        x[0] = 1
    else:
        x[:, 100:800] = 0
    report = SignalQualityAnalyzer(256).analyze(x)
    pipe = SynapDrivePipeline(False)
    p = generate_intent("move left")
    p["signal_quality"] = report.score
    assert pipe.run_intent_packet(p)["status"] == "blocked"
    assert not pipe.get_action_log()


def test_quality_negative_control_clean_volts_is_usable():
    x = np.random.default_rng(14).normal(0, 10e-6, (8, 1024))
    assert SignalQualityAnalyzer(256).analyze(x).score > 0.80


def test_f06_neural_evidence_cannot_default_to_perfect_quality():
    pipe = SynapDrivePipeline(False)
    p = generate_intent("move left")
    p["neural_decode_performed"] = True
    assert pipe.run_intent_packet(p)["status"] == "blocked"


@pytest.mark.parametrize(
    "text",
    ["do not move left", "stop move left", "move left and move right", "please move left now"],
)
def test_f07_exact_grammar_rejects_negated_or_conflicting_text(text):
    pipe = SynapDrivePipeline(False)
    assert pipe.run_text_command(text)["status"] == "blocked"
    assert not pipe.get_action_log()


def test_f07_stop_is_independent_of_journal_failure(monkeypatch):
    pipe = SynapDrivePipeline(False)

    def fail(*args):
        raise OSError("disk unavailable")

    monkeypatch.setattr(pipe.dispatch.journal, "prepare", fail)
    assert pipe.emergency_stop()["status"] == "success"
    assert pipe.dispatch.stopped.is_set()


def test_f08_safe_name_substring_grants_no_capability():
    pipe = SynapDrivePipeline(False)
    pipe.runtime.world_model.register(ActionModel("stop_disable_brakes"))
    pipe.runtime.permissions.revoke_all()
    assert not pipe.runtime.permissions.evaluate("stop_disable_brakes").allowed


def test_f09_replay_restores_feedback_policy_permissions_and_world():
    pipe = SynapDrivePipeline(False)
    pipe.run_text_command("switch mode to assistive")
    out = pipe.run_text_command("move left", feedback={"accepted": False})
    replay = replay_capsule(out["replay_context"])
    assert replay["memory"]["state"] == "quarantined"
    assert replay["world_state"]["mode"] == "assistive"
    capsule = deepcopy(out["replay_context"])
    capsule["feedback"] = {"accepted": True}
    with pytest.raises(ValueError, match="divergence"):
        replay_capsule(capsule)


def test_f11_simplex_cannot_substitute_a_different_action():
    pipe = SynapDrivePipeline(False)
    decision = pipe.runtime.assess(generate_intent("move left"))
    calls = []
    controller = SimplexController(lambda p: calls.append(p) or {}, lambda _: {})
    assert controller.execute(generate_intent("move right"), decision).controller == "reversionary"
    assert not calls


def test_f12_frozen_prerequisite_stops_remaining_plan():
    bridge = ExecutorBridge(False)
    out = bridge.execute(
        TaskPlan("dependent", [TaskStep("unknown"), TaskStep("move left", requires=(0,))])
    )
    assert out.outcome == "frozen"
    assert len(out.steps) == 1
    assert not bridge._pipe.get_action_log()


@pytest.mark.parametrize("step", [0, -1, float("nan"), float("inf")])
def test_f13_invalid_step_raises(step):
    with pytest.raises(ValueError):
        SessionAnalyzer(step_s=step)


def test_f14_no_goal_support_is_not_called_goal_preservation():
    world = WorldModel()
    world.register(ActionModel("move_left"))
    p = SharedAutonomyArbiter(CounterfactualPlanner(world)).propose(
        user_intent="move_left", user_confidence=0.9, machine_candidates=[], goal=lambda _: 0
    )
    assert p.preserved_user_goal is False


def test_f14_unconfirmed_and_delayed_contradiction():
    pipe = SynapDrivePipeline(False)
    out = pipe.run_text_command("move left")
    assert out["memory"]["state"] == "unconfirmed"
    revised = pipe.evidence_memory.apply_feedback(out["memory"]["cycle_id"], False)
    assert revised.state == "quarantined"


def test_f14_retained_checkpoint_rejects_prefix_and_empty_chain():
    chain = EvidenceHashChain()
    chain.append({"x": 1})
    head = chain.append({"x": 2}).event_hash
    assert chain.verify(chain.entries(), expected_count=2, expected_head=head)
    assert not chain.verify(chain.entries()[:1], expected_count=2, expected_head=head)
    assert not chain.verify([], expected_count=2, expected_head=head)


def test_compatibility_classifier_method_is_callable():
    assert IntentClassifier().classify({"label": "think_move"})["intent"] == "move_forward"


@pytest.mark.parametrize("change", ["packet", "state", "policy", "capability", "expiry", "veto"])
def test_dispatch_checks_bindings_before_side_effect(change):
    clock = [0.0]
    gate = DispatchGate(clock=lambda: clock[0])
    packet, state, policy, cap = {"intent": "left"}, {"x": 0}, {"limit": 1}, {"version": 0}
    permit = gate.issue(packet, state, policy, cap)
    if change == "packet":
        packet["intent"] = "right"
    elif change == "state":
        state["x"] = 1
    elif change == "policy":
        policy["limit"] = 0
    elif change == "capability":
        cap["version"] = 1
    elif change == "expiry":
        clock[0] = 2
    else:
        gate.veto()
    calls = []
    with pytest.raises(ValueError):
        gate.execute(permit, packet, state, policy, cap, lambda p: calls.append(p) or {})
    assert not calls


def test_permit_consumption_and_uncertain_restart(tmp_path):
    path = tmp_path / "journal.sqlite"
    gate = DispatchGate(DispatchJournal(path))
    packet = {"intent": "left"}
    permit = gate.issue(packet, {}, {}, {})

    def uncertain(_):
        raise RuntimeError("endpoint disconnected after possible execution")

    with pytest.raises(RuntimeError):
        gate.execute(permit, packet, {}, {}, {}, uncertain)
    restarted = DispatchGate(DispatchJournal(path))
    assert restarted.journal.unresolved() == [permit.token]
    with pytest.raises(ValueError):
        restarted.issue(packet, {}, {}, {})
    restarted.journal.reconcile(permit.token, "confirmed-not-executed")
    permit2 = restarted.issue(packet, {}, {}, {})
    restarted.execute(permit2, packet, {}, {}, {}, lambda _: {"status": "success"})
    with pytest.raises(ValueError):
        restarted.execute(permit2, packet, {}, {}, {}, lambda _: {})


def test_concurrent_canonical_cycles_remain_complete():
    pipe = SynapDrivePipeline(False)
    with ThreadPoolExecutor(max_workers=8) as pool:
        outputs = list(pool.map(lambda _: pipe.run_text_command("move left"), range(80)))
    assert all(out["status"] == "success" for out in outputs)
    assert len(pipe.get_action_log()) == len(pipe.evidence.chain.entries()) == 80
    assert pipe.evidence.verify(pipe.evidence.chain.entries())


def test_access_exact_output_binding_and_private_export(tmp_path):
    access = AccessSession()
    access.edit_draft("original")
    access.propose("machine rewrite")
    token = access.approve()
    access.edit_draft("changed")
    with pytest.raises(PermissionError):
        access.commit_local(token)
    assert access.commit_local(access.approve()) == "changed"
    with pytest.raises(PermissionError):
        access.export(tmp_path / "private.json", consent=True)
    with pytest.raises(PermissionError):
        access.set_preferences(actor="caregiver", mode="bounded-task")
    access.set_privacy("locked")
    with pytest.raises(PermissionError):
        access.command("move left")


def test_access_encrypted_export_omits_plain_content(tmp_path):
    from cryptography.fernet import Fernet

    access = AccessSession(privacy="local-audited")
    access.edit_draft("private words")
    key = Fernet.generate_key()
    file = tmp_path / "audit.json"
    access.export(file, content_key=key, consent=True)
    assert "private words" not in file.read_text()
    raw = json.loads(file.read_text())
    assert "private words" in Fernet(key).decrypt(raw["encrypted_content"].encode()).decode()


def test_input_switch_and_sequential_confirmations():
    access = AccessSession()
    access.register_input("eeg", "q1", True)
    access.request_input("eeg")
    access.confirm_input("eeg")
    p = generate_intent("move left")
    p["qualification_id"] = "q1"
    p["evidence_id"] = "window-1"
    assert access.decoded(p, "eeg")["status"] == "waiting"
    p["evidence_id"] = "window-2"
    assert access.decoded(p, "eeg")["status"] == "success"
    with pytest.raises(ValueError):
        access.request_input("missing-device")


def test_lifecycle_promotion_and_full_descendant_rollback():
    cycle = ModelLifecycle("A")
    cycle.propose("B", ("f1",))
    cycle.evaluate(
        "B",
        audit_id="audit1",
        baseline_utility=0.5,
        candidate_utility=0.6,
        baseline_unsafe=1,
        candidate_unsafe=0,
        samples=100,
    )
    cycle.promote("B")
    cycle.propose("C", ("f2",))
    with pytest.raises(ValueError):
        cycle.evaluate(
            "C",
            audit_id="audit1",
            baseline_utility=0.6,
            candidate_utility=0.7,
            baseline_unsafe=0,
            candidate_unsafe=0,
            samples=100,
        )
    cycle.evaluate(
        "C",
        audit_id="audit2",
        baseline_utility=0.6,
        candidate_utility=0.7,
        baseline_unsafe=0,
        candidate_unsafe=0,
        samples=100,
    )
    cycle.promote("C")
    assert cycle.contradict("f1") == "A"


def test_independent_plant_recovery_and_unsafe_initial_state():
    plant = Plant(position=0.5, velocity=0.8)
    assert plant.recoverable()
    pipe = SynapDrivePipeline(False, fallback_controller=plant.fallback)
    out = pipe.run_text_command("unknown")
    assert out["result"]["fallback_result"]["status"] == "stopped"
    assert plant.velocity == pytest.approx(0)
    assert abs(plant.position) < 1
    unsafe = Plant(position=0.95, velocity=1.0)
    assert not unsafe.recoverable()
    assert not unsafe.fallback()["inside"]


def test_executable_demo_runs_end_to_end():
    result = demo()
    assert result["negated_command"] == "blocked"
    assert result["replayed_memory"] == "quarantined"
    assert result["fallback"]["inside"]
    assert result["rollback"] == "baseline"


def test_simplex_rechecks_revocation_after_assessment():
    pipe = SynapDrivePipeline(False)
    packet = generate_intent("move left")
    old = pipe.runtime.assess(packet)
    pipe.runtime.permissions.revoke_all()
    calls = []
    controller = SimplexController(
        lambda p: calls.append(p) or {}, lambda _: {}, runtime=pipe.runtime
    )
    assert controller.execute(packet, old).controller == "reversionary"
    assert not calls


def test_delayed_feedback_retracts_confirmed_history_and_learning_lineage():
    pipe = SynapDrivePipeline(False)
    out = pipe.run_text_command("move left", feedback={"accepted": True})
    cycle_id = out["memory"]["cycle_id"]
    lifecycle = ModelLifecycle("A")
    lifecycle.propose("B", (cycle_id,))
    lifecycle.evaluate(
        "B",
        audit_id="audit",
        baseline_utility=0.1,
        candidate_utility=0.2,
        baseline_unsafe=1,
        candidate_unsafe=0,
        samples=10,
    )
    lifecycle.promote("B")
    pipe.apply_feedback(cycle_id, False, lifecycle)
    assert not pipe.memory.episodes
    assert lifecycle.active == "A"
    assert pipe.evidence.chain.entries()[-1].payload["accepted"] is False


def test_planner_clarifies_when_goals_have_no_common_progress():
    from synapdrive_ai.cognition.clarification import propose_progress

    world = WorldModel()
    world.register(ActionModel("left", effects={"x": -1}))
    world.register(ActionModel("right", effects={"x": 1}))
    proposal = propose_progress(
        world,
        {"left-goal": lambda s: int(s["x"] == -1), "right-goal": lambda s: int(s["x"] == 1)},
        ["left", "right"],
        assisted=True,
    )
    assert proposal.kind == "clarify"
    assert proposal.action is None


def test_cycle_budget_cannot_disable_independent_stop():
    pipe = SynapDrivePipeline(False, max_cycles=1)
    pipe.run_text_command("move left")
    with pytest.raises(RuntimeError, match="budget"):
        pipe.run_text_command("move right")
    assert pipe.emergency_stop()["status"] == "success"


def test_invalid_feedback_cannot_create_post_action_recording_failure():
    pipe = SynapDrivePipeline(False)
    out = pipe.run_text_command("move left", feedback={"unexpected": float("nan")})
    assert out["status"] == "blocked"
    assert not pipe.get_action_log()
    json.dumps(out, allow_nan=False)


def test_replay_restores_nondefault_lexical_guard():
    pipe = SynapDrivePipeline(False)
    pipe.guard.risk_keywords.append("move_left")
    out = pipe.run_text_command("move left")
    assert out["status"] == "blocked"
    assert replay_capsule(out["replay_context"])["status"] == "blocked"


def test_expiry_during_durable_prepare_prevents_endpoint_call(monkeypatch):
    now = [0.0]
    journal = DispatchJournal()
    original_prepare = journal.prepare

    def delayed_prepare(cycle, packet):
        original_prepare(cycle, packet)
        now[0] = 2.0

    monkeypatch.setattr(journal, "prepare", delayed_prepare)
    gate = DispatchGate(journal, clock=lambda: now[0])
    packet = {"intent": "left"}
    permit = gate.issue(packet, {}, {}, {})
    calls = []
    with pytest.raises(ValueError, match="preparing"):
        gate.execute(permit, packet, {}, {}, {}, lambda p: calls.append(p) or {})
    assert not calls

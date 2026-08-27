from __future__ import annotations

from synapdrive_ai.bci.intent_generator import generate_intent
from synapdrive_ai.pipeline import SynapDrivePipeline


def test_pipeline_exposes_runtime_reality_memory_and_evidence():
    pipe = SynapDrivePipeline(simulate_delay=False)
    out = pipe.run_text_command("move left")
    assert out["status"] == "success"
    assert out["runtime"]["allowed"] is True
    assert out["reality"]["aligned"] is True
    assert out["memory"]["state"] == "validated"
    assert len(out["evidence"]["event_hash"]) == 64


def test_pipeline_quarantines_errp_contradicted_success():
    pipe = SynapDrivePipeline(simulate_delay=False)
    out = pipe.run_text_command("move left", feedback={"errp_probability": 0.99})
    assert out["status"] == "success"
    assert out["reality"]["aligned"] is False
    assert out["memory"]["state"] == "quarantined"


def test_quarantined_memory_does_not_boost_legacy_optimizer():
    pipe = SynapDrivePipeline(simulate_delay=False)
    first = pipe.run_text_command("move left", feedback={"errp_probability": 0.99})
    second = pipe.run_text_command("move left")
    assert first["intent"]["confidence"] == second["intent"]["confidence"]


def test_validated_memory_is_context_not_confidence_inflation():
    pipe = SynapDrivePipeline(simulate_delay=False)
    first = pipe.run_text_command("move left")
    second = pipe.run_text_command("move left")
    assert second["intent"]["confidence"] == first["intent"]["confidence"]
    assert first["intent"]["history_support_count"] == 0
    assert second["intent"]["history_support_count"] == 1


def test_bad_signal_quality_blocks_before_action():
    pipe = SynapDrivePipeline(simulate_delay=False)
    packet = generate_intent("move left")
    packet["signal_quality"] = 0.0
    out = pipe.run_intent_packet(packet)
    assert out["status"] == "blocked"
    assert "signal-quality-below-policy" in out["reason"]
    assert pipe.get_action_log() == []


def test_permission_revoke_blocks_but_stop_stays_available():
    pipe = SynapDrivePipeline(simulate_delay=False)
    pipe.runtime.permissions.revoke_all()
    blocked = pipe.run_text_command("move left")
    stop = pipe.run_text_command("stop")
    assert blocked["status"] == "blocked"
    assert stop["status"] == "success"


def test_successful_action_commits_explicit_world_model_state():
    pipe = SynapDrivePipeline(simulate_delay=False)
    out = pipe.run_text_command("switch mode to assistive")
    assert out["status"] == "success"
    assert out["world_state"]["mode"] == "assistive"
    assert pipe.runtime.world_model.state["mode"] == "assistive"


def test_evidence_chain_detects_no_tamper_after_multiple_cycles():
    pipe = SynapDrivePipeline(simulate_delay=False)
    pipe.run_text_command("move left")
    pipe.run_text_command("stop")
    report = pipe.get_assurance_report()
    assert report["evidence_chain_entries"] == 2
    assert report["evidence_chain_valid"] is True


def test_unknown_text_abstains_with_runtime_evidence():
    pipe = SynapDrivePipeline(simulate_delay=False)
    out = pipe.run_text_command("not a known command")
    assert out["status"] == "blocked"
    assert out["runtime"]["allowed"] is False
    assert out["memory"]["state"] == "not-recorded"

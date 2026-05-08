from __future__ import annotations

import pytest

from synapdrive_ai.bci.intent_generator import generate_intent
from synapdrive_ai.pipeline import SynapDrivePipeline

# ---------------------------------------------------------------------------
# Text command path
# ---------------------------------------------------------------------------


def test_text_command_known_intent_succeeds(pipeline: SynapDrivePipeline) -> None:
    out = pipeline.run_text_command("move left", image_label="road")
    assert out["status"] in {"success", "blocked"}
    assert "intent" in out
    assert "evaluation" in out


def test_text_command_stop_succeeds(pipeline: SynapDrivePipeline) -> None:
    out = pipeline.run_text_command("stop")
    assert out["status"] in {"success", "blocked"}


def test_text_command_unknown_input_is_blocked(pipeline: SynapDrivePipeline) -> None:
    # Unknown inputs resolve to low confidence and should be blocked by safety.
    out = pipeline.run_text_command("xyzzy nonsense")
    assert out["status"] == "blocked"


def test_text_command_returns_required_keys(pipeline: SynapDrivePipeline) -> None:
    out = pipeline.run_text_command("move right")
    for key in ("status", "intent", "result", "evaluation"):
        assert key in out, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# Signal path
# ---------------------------------------------------------------------------


def test_signal_event_known_labels(pipeline: SynapDrivePipeline) -> None:
    for label in ("walk", "stop", "left_arm", "right_arm", "calculate", "recall", "explore"):
        out = pipeline.run_signal_event(label=label)
        assert out["status"] in {"success", "blocked"}


def test_signal_event_random_label(pipeline: SynapDrivePipeline) -> None:
    out = pipeline.run_signal_event()
    assert out["status"] in {"success", "blocked"}


def test_signal_event_unknown_label_raises(pipeline: SynapDrivePipeline) -> None:
    with pytest.raises(ValueError, match="Unknown signal label"):
        pipeline.run_signal_event(label="brain_blast")


# ---------------------------------------------------------------------------
# Safety gate
# ---------------------------------------------------------------------------


def test_blocked_result_has_reason(pipeline: SynapDrivePipeline) -> None:
    out = pipeline.run_text_command("xyzzy")
    assert out["status"] == "blocked"
    assert "reason" in out


def test_blocked_result_has_zero_evaluation_score(pipeline: SynapDrivePipeline) -> None:
    out = pipeline.run_text_command("xyzzy")
    assert out["status"] == "blocked"
    assert out["evaluation"]["score"] == 0.0


# ---------------------------------------------------------------------------
# Action log
# ---------------------------------------------------------------------------


def test_action_log_grows(pipeline: SynapDrivePipeline) -> None:
    pipeline.run_text_command("move left", image_label="road")
    pipeline.run_signal_event(label="walk")
    log = pipeline.get_action_log()
    assert len(log) >= 1  # blocked intents do not reach actuation


def test_action_log_entries_have_schema(pipeline: SynapDrivePipeline) -> None:
    pipeline.run_text_command("move right")
    for entry in pipeline.get_action_log():
        for key in ("intent", "confidence", "status", "duration"):
            assert key in entry


# ---------------------------------------------------------------------------
# run_intent_packet (public entrypoint used by replay + integrations)
# ---------------------------------------------------------------------------


def test_run_intent_packet_roundtrip(pipeline: SynapDrivePipeline) -> None:
    packet = generate_intent("move left")
    out = pipeline.run_intent_packet(packet, image_label="road")
    assert out["status"] in {"success", "blocked"}
    assert out["result"]["intent"] is not None


def test_run_intent_packet_with_visual_context(pipeline: SynapDrivePipeline) -> None:
    for image_label in ("road", "hazard", "person", "vehicle"):
        packet = generate_intent("move forward")
        out = pipeline.run_intent_packet(packet, image_label=image_label)
        assert out["status"] in {"success", "blocked"}

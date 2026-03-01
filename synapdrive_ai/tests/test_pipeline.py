# synapdrive_ai/tests/test_pipeline.py

def test_text_command_happy_path(pipeline):
    """
    A high-confidence known command should:
      - pass SafetyGuard
      - execute successfully
      - return a stable response shape
    """
    out = pipeline.run_text_command("move left", image_label="road")

    assert isinstance(out, dict)
    assert out["status"] == "success"
    assert "intent" in out and isinstance(out["intent"], dict)
    assert "result" in out and isinstance(out["result"], dict)
    assert "evaluation" in out and isinstance(out["evaluation"], dict)

    # Result contract (normalized by DecisionRouter)
    assert out["result"]["status"] == "success"
    assert "duration" in out["result"]


def test_unknown_command_gets_safety_blocked(pipeline):
    """
    Unknown text defaults to low confidence -> optimizer reduces further -> SafetyGuard blocks.
    This proves the repo has a real guardrail loop, not just a demo printout.
    """
    out = pipeline.run_text_command("asdkjhasd kjashd kjashd", image_label=None)

    assert out["status"] == "blocked"
    assert "confidence too low" in out["reason"].lower()


def test_action_log_schema_is_stable(pipeline):
    """
    Telemetry schema must stay stable because dashboards/CI depend on it.
    """
    pipeline.run_text_command("stop", image_label="hazard")
    log = pipeline.get_action_log()
    assert isinstance(log, list)
    assert len(log) >= 1

    latest = log[-1]
    required_keys = {
        "timestamp",
        "intent",
        "confidence",
        "status",
        "duration",
        "source",
        "memory",
        "memory_context",
    }
    missing = required_keys.difference(set(latest.keys()))
    assert not missing, f"Missing telemetry keys: {missing}"

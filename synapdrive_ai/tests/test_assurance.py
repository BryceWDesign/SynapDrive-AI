from __future__ import annotations

from synapdrive_ai.assurance import AssuranceMonitor
from synapdrive_ai.pipeline import SynapDrivePipeline


def test_pipeline_success_cycle_includes_passing_assurance_receipt(
    pipeline: SynapDrivePipeline,
) -> None:
    out = pipeline.run_text_command("move left", image_label="road")

    assert out["status"] == "success"
    assert out["assurance"]["schema"] == "synapdrive.assurance.v1"
    assert out["assurance"]["passed"] is True
    assert out["assurance"]["safety_allowed"] is True
    assert out["assurance"]["result_status"] == "success"


def test_pipeline_blocked_cycle_includes_passing_assurance_receipt(
    pipeline: SynapDrivePipeline,
) -> None:
    out = pipeline.run_text_command("xyzzy nonsense")

    assert out["status"] == "blocked"
    assert out["assurance"]["passed"] is True
    assert out["assurance"]["safety_allowed"] is False
    assert out["assurance"]["result_status"] == "blocked"
    assert pipeline.get_action_log() == []


def test_assurance_health_report_counts_cycles(pipeline: SynapDrivePipeline) -> None:
    pipeline.run_text_command("move left")
    pipeline.run_text_command("xyzzy nonsense")

    report = pipeline.get_assurance_report()

    assert report["schema"] == "synapdrive.assurance.health.v1"
    assert report["total_cycles"] == 2
    assert report["passed_receipts"] == 2
    assert report["failed_receipts"] == 0
    assert report["blocked_cycles"] == 1
    assert report["executed_cycles"] == 1
    assert isinstance(report["latest_receipt_id"], str)


def test_assurance_monitor_detects_blocked_actuation_drift() -> None:
    monitor = AssuranceMonitor()

    receipt = monitor.record_cycle(
        intent_packet={"intent": "unknown", "confidence": 0.2, "source": "test"},
        image_label=None,
        safety_allowed=False,
        safety_reason="Intent confidence too low: 0.2",
        result_packet={"status": "success", "intent": "unknown", "confidence": 0.2},
        evaluation={"score": 1.0},
        executed=True,
    )

    assert receipt.passed is False
    assert "blocked-cycle-returned-nonblocked-result" in receipt.issues
    assert "blocked-cycle-reached-actuation" in receipt.issues

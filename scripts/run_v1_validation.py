from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

import numpy as np
from cryptography.hazmat.primitives import serialization

from synapdrive_ai.adaptation.guarded import GuardedThresholdAdapter
from synapdrive_ai.assurance.hashchain import EvidenceHashChain
from synapdrive_ai.assurance.signing import Ed25519EvidenceSigner, verify_ed25519
from synapdrive_ai.bci.intent_generator import generate_intent
from synapdrive_ai.benchmarking.dataset import EpochDataset
from synapdrive_ai.benchmarking.decoders import (
    EnsembleDecoder,
    RiemannianCentroidDecoder,
    SpectralCentroidDecoder,
)
from synapdrive_ai.benchmarking.evaluation import evaluate_decoder
from synapdrive_ai.benchmarking.runtime_adapter import QualifiedDecoderAdapter
from synapdrive_ai.cognition.planner import CandidateAction, CounterfactualPlanner
from synapdrive_ai.cognition.shared_autonomy import SharedAutonomyArbiter
from synapdrive_ai.cognition.world_model import ActionModel, WorldModel
from synapdrive_ai.neuro.drift import FeatureDriftMonitor
from synapdrive_ai.neuro.eeg_loader import EEGRecording
from synapdrive_ai.neuro.fusion import ModalityEvidence, WeightedEvidenceFusion
from synapdrive_ai.neuro.session_analyzer import SessionAnalyzer
from synapdrive_ai.neuro.signal_quality import SignalQualityAnalyzer
from synapdrive_ai.neuro.task_planner import ExecutorBridge, TaskPlan, TaskStep
from synapdrive_ai.pipeline import SynapDrivePipeline
from synapdrive_ai.runtime.shadow import ShadowController
from synapdrive_ai.stress.campaign import StressCampaign
from synapdrive_ai.stress.faults import FaultInjector


def _verification_dataset(seed: int = 41) -> EpochDataset:
    """Deterministic synthetic verification data, never presented as human EEG."""
    rng = np.random.default_rng(seed)
    sr = 128.0
    n = 128
    t = np.arange(n) / sr
    epochs = []
    labels = []
    for label, freq in (("class_10hz", 10.0), ("class_20hz", 20.0)):
        for _ in range(24):
            a = np.sin(2 * np.pi * freq * t) + rng.normal(0, 0.10, n)
            b = 0.8 * np.sin(2 * np.pi * freq * t + 0.2) + rng.normal(0, 0.10, n)
            epochs.append(np.stack([a, b]))
            labels.append(label)
    return EpochDataset(
        np.asarray(epochs),
        np.asarray(labels),
        sr,
        ["SIM-A", "SIM-B"],
        "deterministic-synthetic-verification-only",
    )


def _check(name: str, passed: bool, **details) -> dict:
    return {"check": name, "passed": bool(passed), **details}


def run_validation() -> dict:
    checks: list[dict] = []

    pipe = SynapDrivePipeline(simulate_delay=False)
    success = pipe.run_text_command("move left")
    checks.append(
        _check(
            "governed_declared_command_path",
            success["status"] == "success" and success["runtime"]["allowed"],
            authority=success["intent"].get("inference_authority"),
        )
    )

    unmodeled = pipe.run_intent_packet(
        {
            "intent": "invented_action",
            "confidence": 1.0,
            "source": "validation",
            "uncertainty": 0.0,
            "signal_quality": 1.0,
        }
    )
    checks.append(
        _check(
            "unmodeled_action_fails_closed",
            unmodeled["status"] == "blocked"
            and "world-model-precondition-failed" in unmodeled["reason"],
            reason=unmodeled.get("reason"),
        )
    )

    analysis_only = pipe.run_intent_packet(
        {
            "intent": "move_left",
            "confidence": 1.0,
            "source": "analysis-only-validation",
            "analysis_only": True,
            "uncertainty": 0.0,
            "signal_quality": 1.0,
        }
    )
    checks.append(
        _check(
            "analysis_only_inference_cannot_actuate",
            analysis_only["status"] == "blocked"
            and "analysis-only-inference" in analysis_only["reason"],
        )
    )

    action_count_before = len(pipe.get_action_log())
    low_quality_packet = generate_intent("move left")
    low_quality_packet["signal_quality"] = 0.0
    blocked = pipe.run_intent_packet(low_quality_packet)
    checks.append(
        _check(
            "low_quality_fail_closed",
            blocked["status"] == "blocked"
            and len(pipe.get_action_log()) == action_count_before,
            reason=blocked.get("reason"),
        )
    )

    uncertainty_packet = generate_intent("move left")
    uncertainty_packet["probabilities"] = {"move_left": 0.5, "move_right": 0.5}
    uncertain = pipe.run_intent_packet(uncertainty_packet)
    checks.append(
        _check(
            "high_uncertainty_abstains",
            uncertain["status"] == "blocked"
            and "uncertainty-above-policy" in uncertain["reason"],
            uncertainty=uncertain["intent"].get("uncertainty"),
        )
    )

    drift_monitor = FeatureDriftMonitor(quantile=0.95).fit(
        [[0.0, 0.0], [0.1, -0.1], [-0.1, 0.1], [0.05, 0.02], [-0.05, -0.02]]
    )
    drift = drift_monitor.evaluate([5.0, 5.0])
    drift_packet = generate_intent("move left")
    drift_packet["drift_score"] = drift.score
    drift_block = pipe.run_intent_packet(drift_packet)
    checks.append(
        _check(
            "decoder_drift_fail_closed",
            drift.drifted
            and drift_block["status"] == "blocked"
            and "decoder-drift-above-policy" in drift_block["reason"],
            drift_score=drift.score,
            learned_threshold=drift.threshold,
        )
    )

    permission_pipe = SynapDrivePipeline(simulate_delay=False)
    permission_pipe.runtime.permissions.revoke_all()
    denied = permission_pipe.run_text_command("move left")
    stop = permission_pipe.run_text_command("stop")
    checks.append(
        _check(
            "permission_revoke_preserves_safe_stop",
            denied["status"] == "blocked" and stop["status"] == "success",
        )
    )

    contradicted = pipe.run_text_command("move right", feedback={"errp_probability": 0.99})
    checks.append(
        _check(
            "errp_contradiction_quarantines_memory",
            contradicted["reality"]["aligned"] is False
            and contradicted["memory"]["state"] == "quarantined",
        )
    )

    entries = pipe.evidence.chain.entries()
    checks.append(
        _check(
            "evidence_chain_valid",
            EvidenceHashChain.verify(entries),
            entries=len(entries),
        )
    )
    tampered = [entry.to_dict() for entry in entries]
    tampered[-1]["payload"]["result"]["status"] = "tampered"
    checks.append(
        _check(
            "evidence_tamper_detected",
            not EvidenceHashChain.verify(tampered),
        )
    )

    signer = Ed25519EvidenceSigner.generate()
    signing_payload = json.dumps(entries[-1].to_dict(), sort_keys=True).encode("utf-8")
    signature = signer.sign(signing_payload)
    public_pem = signer.private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    signing_ok = verify_ed25519(public_pem, signing_payload, signature)
    tamper_rejected = not verify_ed25519(public_pem, signing_payload + b"x", signature)
    checks.append(
        _check(
            "ed25519_evidence_signature",
            signing_ok and tamper_rejected,
        )
    )

    quality = SignalQualityAnalyzer(256).analyze(np.zeros(512))
    checks.append(
        _check(
            "flatline_quality_detection",
            "flatline" in quality.issues and quality.score < 0.55,
            score=quality.score,
            state=quality.state,
        )
    )

    fusion = WeightedEvidenceFusion().fuse(
        [
            ModalityEvidence("eeg", {"left": 0.7, "right": 0.3}, 0.7),
            ModalityEvidence("emg", {"left": 0.9, "right": 0.1}, 0.9),
        ]
    )
    checks.append(
        _check(
            "multimodal_reliability_weighted_fusion",
            fusion.intent == "left" and fusion.weights == {"eeg": 0.7, "emg": 0.9},
            confidence=fusion.confidence,
            uncertainty=fusion.uncertainty,
        )
    )

    plan_world = WorldModel({"goal": 0})
    plan_world.register_many(
        [
            ActionModel("direct", effects={"goal": 1}, predicted_risk=0.8),
            ActionModel("detour", effects={"goal": 1}, predicted_risk=0.1),
        ]
    )
    proposal = SharedAutonomyArbiter(CounterfactualPlanner(plan_world)).propose(
        user_intent="direct",
        user_confidence=0.8,
        machine_candidates=[CandidateAction("detour", 0.95, 0.9)],
        goal=lambda state: float(state.get("goal", 0)),
    )
    checks.append(
        _check(
            "counterfactual_shared_autonomy_prefers_lower_risk_candidate",
            proposal.selected_action == "detour" and proposal.preserved_user_goal,
            selected_action=proposal.selected_action,
        )
    )

    shadow_calls: list[dict] = []

    def shadow_policy(context: dict) -> tuple[str, dict]:
        shadow_calls.append(dict(context))
        return "experimental_action", {"score": 0.9}

    shadow = ShadowController(shadow_policy).evaluate("trusted_action", {"cycle": 1})
    checks.append(
        _check(
            "shadow_policy_has_no_actuation_authority",
            shadow.shadow_action == "experimental_action"
            and shadow.trusted_action == "trusted_action"
            and len(shadow_calls) == 1,
        )
    )

    adaptation_rows = [
        {"confidence": 0.95, "safe": True},
        {"confidence": 0.80, "safe": True},
        {"confidence": 0.60, "safe": False},
        {"confidence": 0.55, "safe": False},
    ]
    adaptation = GuardedThresholdAdapter(0.45).evaluate_candidate(0.65, adaptation_rows)
    checks.append(
        _check(
            "guarded_adaptation_requires_held_out_improvement",
            adaptation.promoted
            and adaptation.candidate_unsafe_accepts < adaptation.old_unsafe_accepts,
            old_unsafe_accepts=adaptation.old_unsafe_accepts,
            candidate_unsafe_accepts=adaptation.candidate_unsafe_accepts,
        )
    )

    first_replay = SynapDrivePipeline(simulate_delay=False).run_intent_packet(
        generate_intent("move left")
    )
    second_replay = SynapDrivePipeline(simulate_delay=False).run_intent_packet(
        generate_intent("move left")
    )
    checks.append(
        _check(
            "deterministic_cycle_evidence_replay",
            first_replay["evidence"]["event_hash"] == second_replay["evidence"]["event_hash"],
            event_hash=first_replay["evidence"]["event_hash"],
        )
    )

    dataset = _verification_dataset()
    decoder = EnsembleDecoder([SpectralCentroidDecoder(), RiemannianCentroidDecoder()])
    benchmark = evaluate_decoder(decoder, dataset, seed=7)
    checks.append(
        _check(
            "decoder_benchmark_executes",
            benchmark.n_test > 0 and 0.0 <= benchmark.accuracy <= 1.0,
            dataset=dataset.source,
            metrics=benchmark.to_dict(),
        )
    )

    qualified_adapter = QualifiedDecoderAdapter(
        SpectralCentroidDecoder(),
        dataset,
        {"class_10hz": "move_left", "class_20hz": "move_right"},
        seed=7,
    )
    decoded_packet = qualified_adapter(
        dataset.epochs[0],
        {"sampling_rate": dataset.sampling_rate},
    )
    decoded_result = SynapDrivePipeline(simulate_delay=False).run_intent_packet(decoded_packet)
    checks.append(
        _check(
            "locally_qualified_decoder_reaches_governed_runtime",
            qualified_adapter.qualification.qualified
            and decoded_packet["neural_decode_performed"] is True
            and decoded_result["status"] == "success",
            qualification=qualified_adapter.qualification.to_dict(),
            decoded_intent=decoded_packet["intent"],
        )
    )

    mismatch_packet = qualified_adapter(
        dataset.epochs[0],
        {"sampling_rate": dataset.sampling_rate + 1.0},
    )
    checks.append(
        _check(
            "qualified_decoder_sampling_mismatch_abstains",
            mismatch_packet["intent"] == "unknown"
            and mismatch_packet["analysis_only"] is True,
            reason=mismatch_packet.get("abstention_reason"),
        )
    )

    one_channel_dataset = EpochDataset(
        dataset.epochs[:, :1, :],
        dataset.labels.copy(),
        dataset.sampling_rate,
        ["SIM-A"],
        "deterministic-synthetic-verification-only/session-bridge",
    )
    session_adapter = QualifiedDecoderAdapter(
        SpectralCentroidDecoder(),
        one_channel_dataset,
        {"class_10hz": "move_left", "class_20hz": "move_right"},
        seed=7,
    )
    session_recording = EEGRecording(
        channels=["SIM-A"],
        data=one_channel_dataset.epochs[0],
        sampling_rate=one_channel_dataset.sampling_rate,
        duration_s=one_channel_dataset.epochs.shape[-1] / one_channel_dataset.sampling_rate,
        source_file="deterministic-synthetic-verification-only/session-bridge",
    )
    session_report = SessionAnalyzer(
        channel="SIM-A",
        window_s=session_recording.duration_s,
        step_s=session_recording.duration_s,
        decoder=session_adapter,
    ).run(session_recording)
    checks.append(
        _check(
            "qualified_decoder_session_analyzer_bridge",
            session_adapter.qualification.qualified
            and session_report.n_epochs == 1
            and session_report.n_success == 1,
            pipeline_status=session_report.epochs[0].pipeline_status,
            confidence=session_report.epochs[0].pipeline_confidence,
        )
    )

    plan_bridge = ExecutorBridge(simulate_delay=False)
    plan_trace = plan_bridge.execute(
        TaskPlan(
            "pre-action-threshold-validation",
            [TaskStep("move left", min_confidence=1.1, fallback="freeze")],
        )
    )
    checks.append(
        _check(
            "task_threshold_blocks_before_simulated_actuation",
            plan_trace.steps[0].pipeline_status == "deferred"
            and plan_bridge._pipe.get_action_log() == [],
        )
    )

    state_pipe = SynapDrivePipeline(simulate_delay=False)
    state_result = state_pipe.run_text_command("switch mode to assistive")
    checks.append(
        _check(
            "successful_action_commits_explicit_world_state",
            state_result["status"] == "success"
            and state_pipe.runtime.world_model.state.get("mode") == "assistive",
            world_state=dict(state_pipe.runtime.world_model.state),
        )
    )

    base = np.sin(2 * np.pi * 10 * np.arange(512) / 256)
    injector = FaultInjector(9)
    faults = [
        ("dropout", injector.dropout(base, 0.8).signal),
        ("flatline", np.zeros_like(base)),
        ("noise", injector.gaussian_noise(base, 2.0).signal),
    ]
    stress_pipe = SynapDrivePipeline(simulate_delay=False)
    campaign = StressCampaign(256, min_quality=stress_pipe.runtime.policy.min_signal_quality)

    def callback(_signal: np.ndarray, quality_score: float) -> bool:
        stress_packet = generate_intent("move left")
        stress_packet["signal_quality"] = quality_score
        return stress_pipe.run_intent_packet(stress_packet)["status"] == "blocked"

    stress = campaign.run(faults, callback)
    checks.append(
        _check(
            "fault_campaign_fail_closed",
            stress.invariant_failures == 0,
            report=stress.to_dict(),
        )
    )

    passed = all(bool(item["passed"]) for item in checks)
    return {
        "schema": "synapdrive.validation.v1",
        "version": "1.0.0",
        "passed": passed,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "claims": {
            "human_eeg_used": False,
            "physical_actuation_used": False,
            "clinical_validation": False,
            "hardware_safety_validation": False,
            "synthetic_verification_data_used": True,
            "benchmark_metrics_are_bci_performance_claims": False,
        },
        "checks": checks,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run SynapDrive-AI release validation checks")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    report = run_validation()
    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

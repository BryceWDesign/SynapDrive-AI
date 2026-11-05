from __future__ import annotations

import json
import threading
from copy import deepcopy
from dataclasses import asdict
from typing import Any, Dict, Mapping, Optional

from synapdrive_ai.action.decision_router import DecisionRouter
from synapdrive_ai.assurance import AssuranceMonitor
from synapdrive_ai.assurance.evidence_ledger import SessionEvidenceLedger
from synapdrive_ai.bci.intent_generator import generate_intent
from synapdrive_ai.bci.signal_simulator import BrainSignalSimulator
from synapdrive_ai.cognition.planner import CandidateAction, CounterfactualPlanner
from synapdrive_ai.cognition.shared_autonomy import SharedAutonomyArbiter
from synapdrive_ai.memory.episodic_memory import EpisodicMemory
from synapdrive_ai.memory.evidence_memory import EvidenceMemory
from synapdrive_ai.neuro.uncertainty import estimate_uncertainty, packet_distribution
from synapdrive_ai.processing.cognitive_optimizer import CognitiveOptimizer
from synapdrive_ai.processing.core_reasoning import LabeledSignalMapper
from synapdrive_ai.processing.meta_evaluator import MetaEvaluator
from synapdrive_ai.runtime.dispatch import DispatchGate, DispatchJournal
from synapdrive_ai.runtime.governed_runtime import GovernedRuntime
from synapdrive_ai.runtime.reality import RealityReconciler
from synapdrive_ai.runtime.validation import finite, validate_packet
from synapdrive_ai.safety.safety_guard import SafetyGuard
from synapdrive_ai.vision.visual_inference import VisualInferenceEngine


class SynapDrivePipeline:
    """Canonical governed simulation pipeline.

    Flow:
      input -> intent -> context -> uncertainty -> policy/permission/world assessment
      -> legacy safety checks -> simulated actuation or fail-closed abstention
      -> reality reconciliation -> evidence-gated memory -> assurance + hash-chain evidence

    No element of this class constitutes medical-device or physical-actuation validation.
    """

    def __init__(
        self,
        simulate_delay: bool = True,
        runtime: GovernedRuntime | None = None,
        journal_path: str = ":memory:",
        fallback_controller=None,
        max_cycles: int = 10000,
    ) -> None:
        if not 1 <= max_cycles <= 100000:
            raise ValueError("max_cycles must be between 1 and 100000")
        self.max_cycles = max_cycles
        self.fallback_controller = fallback_controller
        self.dispatch = DispatchGate(DispatchJournal(journal_path))
        self._cycle_lock = threading.RLock()
        self.simulator = BrainSignalSimulator()
        self.reasoner = LabeledSignalMapper()
        self.memory = EpisodicMemory()
        self.evidence_memory = EvidenceMemory()
        self.visual = VisualInferenceEngine()
        self.optimizer = CognitiveOptimizer()
        self.optimizer.memory = self.memory
        self.optimizer.visual = self.visual
        self.guard = SafetyGuard()
        self.router = DecisionRouter(simulate_delay=simulate_delay)
        self.evaluator = MetaEvaluator()
        self.assurance = AssuranceMonitor()
        self.runtime = runtime or GovernedRuntime()
        self.reconciler = RealityReconciler()
        self.evidence = SessionEvidenceLedger()

    def run_text_command(
        self,
        command_text: str,
        image_label: Optional[str] = None,
        feedback: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        intent_packet = generate_intent(command_text)
        return self.run_intent_packet(intent_packet, image_label=image_label, feedback=feedback)

    def run_signal_event(
        self,
        label: Optional[str] = None,
        image_label: Optional[str] = None,
        feedback: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        label = label or self.simulator.random_label()
        signal = self._generate_signal_for_label(label)
        intent_packet = self.reasoner.receive_signal(label, signal)
        return self.run_intent_packet(intent_packet, image_label=image_label, feedback=feedback)

    def run_intent_packet(
        self,
        intent_packet: Dict[str, Any],
        image_label: Optional[str] = None,
        feedback: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        return self._run_common(intent_packet, image_label=image_label, feedback=feedback)

    def plan_shared_action(
        self,
        *,
        user_intent: str,
        user_confidence: float,
        machine_candidates: list[CandidateAction],
        goal,
    ):
        """Rank bounded machine alternatives against the runtime world model.

        This method proposes only. It does not actuate the selected action.
        """
        arbiter = SharedAutonomyArbiter(CounterfactualPlanner(self.runtime.world_model))
        return arbiter.propose(
            user_intent=user_intent,
            user_confidence=user_confidence,
            machine_candidates=machine_candidates,
            goal=goal,
        )

    def get_action_log(self):
        return self.router.get_action_log()

    def get_assurance_log(self):
        return [receipt.to_dict() for receipt in self.assurance.history()]

    def get_assurance_report(self) -> Dict[str, Any]:
        report = dict(self.assurance.health_report())
        report["evidence_chain_entries"] = len(self.evidence.chain.entries())
        report["evidence_chain_valid"] = self.evidence.verify(self.evidence.chain.entries())
        report["validated_memories"] = sum(
            1 for record in self.evidence_memory.all() if record.state == "validated"
        )
        report["quarantined_memories"] = len(self.evidence_memory.quarantined())
        return report

    def _generate_signal_for_label(self, label: str):
        patterns = {
            "left_arm": 10,
            "right_arm": 12,
            "walk": 8,
            "stop": 3,
            "calculate": 25,
            "recall": 18,
            "explore": 30,
        }
        if label not in patterns:
            raise ValueError(f"Unknown signal label: {label!r}. Valid labels: {sorted(patterns)}")
        return self.simulator.generate_waveform(patterns[label])

    def apply_feedback(self, cycle_id: str, accepted: bool, lifecycle=None):
        if not isinstance(accepted, bool):
            raise ValueError("accepted must be boolean")
        with self._cycle_lock:
            revised = self.evidence_memory.apply_feedback(cycle_id, accepted)
            if not accepted:
                self.memory.episodes[:] = [
                    e for e in self.memory.episodes if e.get("cycle_id") != cycle_id
                ]
                if lifecycle is not None:
                    lifecycle.contradict(cycle_id)
            self.evidence.record(
                {
                    "schema": "synapdrive.feedback.v2",
                    "cycle_id": cycle_id,
                    "accepted": accepted,
                    "memory_state": revised.state,
                }
            )
            return revised

    def emergency_stop(self) -> Dict[str, Any]:
        """Explicit trusted operator veto; independent of signal quality and journal writes.

        Stops the simulated endpoint. Physical stop hardware is outside this API.
        """
        self.dispatch.veto()
        packet = generate_intent("stop")
        if self.fallback_controller is not None:
            return self.fallback_controller("halt_all_motion")
        return self.router.route(packet)

    def resume(self) -> None:
        self.dispatch.resume()

    def _capabilities(self) -> dict:
        gate = self.runtime.permissions
        return {
            "allow": list(gate.allow_patterns),
            "deny": list(gate.deny_patterns),
            "revoked": gate._revoked,
            "version": gate.version,
        }

    def _run_common(self, intent_packet, image_label, feedback):
        with self._cycle_lock:
            if len(self.evidence.chain.entries()) >= self.max_cycles:
                raise RuntimeError("cycle budget exhausted; checkpoint/export and start a new run")
            try:
                packet = validate_packet(intent_packet)
                feedback = (
                    json.loads(json.dumps(dict(feedback), allow_nan=False))
                    if feedback is not None
                    else None
                )
                if feedback is not None and len(json.dumps(feedback).encode()) > 65536:
                    raise ValueError("feedback exceeds size budget")
                if image_label is not None and (
                    not isinstance(image_label, str) or len(image_label) > 128
                ):
                    raise ValueError("image label must be a bounded declared string")
                if feedback is not None:
                    if "errp_probability" in feedback:
                        finite(feedback["errp_probability"], "errp_probability")
                    if "accepted" in feedback and not isinstance(feedback["accepted"], bool):
                        raise ValueError("accepted must be boolean")
            except (ValueError, TypeError) as error:
                packet = {
                    "intent": "unknown",
                    "source": "rejected-input",
                    "confidence": 0.0,
                    "analysis_only": True,
                    "validation_error": str(error),
                }
                feedback = None
            context = {
                "schema": "synapdrive.capsule.v2",
                "packet": deepcopy(packet),
                "feedback": feedback,
                "image_label": image_label,
                "policy": self.runtime.policy.to_dict(),
                "lexical_guard": {
                    "min_confidence": self.guard.min_confidence_threshold,
                    "risk_keywords": list(self.guard.risk_keywords),
                },
                "capabilities": self._capabilities(),
                "world_state": deepcopy(self.runtime.world_model.state),
                "actions": [asdict(a) for a in self.runtime.world_model._actions.values()],
                "stopped": self.dispatch.stopped.is_set(),
                "unresolved": bool(self.dispatch.journal.unresolved()),
            }
            if context["stopped"] or context["unresolved"]:
                packet["analysis_only"] = True
            plant = getattr(self.router, "plant", None)
            context["simulation_state"] = asdict(plant) if plant is not None else None
            context["replay_supported"] = self.fallback_controller is None or plant is not None
            output = self._execute_cycle(packet, image_label, feedback)
            context["expected"] = {
                "status": output["status"],
                "intent": output["intent"]["intent"],
                "reality": output["reality"],
                "world_state": deepcopy(self.runtime.world_model.state),
                "memory_state": output["memory"]["state"],
            }
            if plant is not None:
                context["expected"]["simulation_state"] = asdict(plant)
            output["replay_context"] = context
            return output

    def _execute_cycle(
        self,
        intent_packet: Dict[str, Any],
        image_label: Optional[str],
        feedback: Mapping[str, Any] | None,
    ) -> Dict[str, Any]:
        optimized = self.optimizer.optimize(intent_packet, image_label=image_label)
        distribution = packet_distribution(optimized)
        uncertainty = estimate_uncertainty(distribution)
        optimized["probabilities"] = distribution
        optimized["uncertainty"] = max(float(optimized.get("uncertainty", 0)), uncertainty.combined)
        optimized["uncertainty_detail"] = uncertainty.to_dict()

        runtime_decision = self.runtime.assess(optimized)
        legacy_safe, legacy_reason = self.guard.evaluate_safety(optimized)
        allowed = runtime_decision.allowed and legacy_safe
        block_reason = runtime_decision.reason if not runtime_decision.allowed else legacy_reason

        if not allowed:
            result = {
                "status": "blocked",
                "intent": optimized.get("intent", "unknown"),
                "confidence": optimized.get("confidence", 0.0),
                "duration": 0.0,
                "fallback_action": runtime_decision.fallback_action,
            }
            if self.fallback_controller is not None:
                result["fallback_result"] = self.fallback_controller(
                    runtime_decision.fallback_action
                )
            evaluation = {
                "score": 0.0,
                "total_actions": len(self.evaluator.scores),
                "avg_score": 0.0,
            }
            reality = self.reconciler.reconcile(
                predicted_success=0.0,
                result_packet=result,
                feedback=feedback,
                errp_threshold=self.runtime.policy.errp_contradiction_threshold,
            )
            receipt = self.assurance.record_cycle(
                intent_packet=optimized,
                image_label=image_label,
                safety_allowed=False,
                safety_reason=block_reason,
                result_packet=result,
                evaluation=evaluation,
                executed=False,
            )
            evidence_entry = self._record_evidence(
                optimized, runtime_decision.to_dict(), result, reality.to_dict(), receipt.to_dict()
            )
            return {
                "status": "blocked",
                "reason": block_reason,
                "intent": optimized,
                "result": result,
                "evaluation": evaluation,
                "runtime": runtime_decision.to_dict(),
                "reality": reality.to_dict(),
                "memory": {"state": "not-recorded", "reason": "blocked-before-actuation"},
                "assurance": receipt.to_dict(),
                "evidence": evidence_entry.to_dict(),
            }

        permit = self.dispatch.issue(
            optimized,
            self.runtime.world_model.state,
            self.runtime.policy.to_dict(),
            self._capabilities(),
        )
        result = self.dispatch.execute(
            permit,
            optimized,
            self.runtime.world_model.state,
            self.runtime.policy.to_dict(),
            self._capabilities(),
            self.router.route,
        )
        world_prediction = self.runtime.world_model.predict(str(optimized.get("intent", "unknown")))
        if result.get("status") == "success" and world_prediction.feasible:
            self.runtime.world_model.commit(world_prediction)
        evaluation = self.evaluator.evaluate(optimized, result)
        predicted_success = max(
            0.0,
            min(1.0, 1.0 - runtime_decision.assessment.predicted_risk),
        )
        reality = self.reconciler.reconcile(
            predicted_success=predicted_success,
            result_packet=result,
            feedback=feedback,
            errp_threshold=self.runtime.policy.errp_contradiction_threshold,
        )

        # Legacy memory remains for compatibility but only aligned successful outcomes reinforce it.
        if (
            reality.aligned
            and feedback
            and feedback.get("accepted") is True
            and result.get("status") == "success"
        ):
            self.memory.record_episode(optimized, result)

        receipt = self.assurance.record_cycle(
            intent_packet=optimized,
            image_label=image_label,
            safety_allowed=True,
            safety_reason=legacy_reason,
            result_packet=result,
            evaluation=evaluation,
            executed=True,
        )
        cycle_id = receipt.receipt_id
        if reality.aligned and feedback and feedback.get("accepted") is True:
            self.memory.episodes[-1]["cycle_id"] = cycle_id
        memory_record = self.evidence_memory.record(
            cycle_id=cycle_id,
            intent=str(optimized.get("intent", "unknown")),
            confidence=float(optimized.get("confidence", 0.0)),
            outcome=str(result.get("status", "unknown")),
            aligned=reality.aligned and result.get("status") == "success",
            reason=reality.reason,
            confirmed=bool(feedback and feedback.get("accepted") is True),
        )
        evidence_entry = self._record_evidence(
            optimized, runtime_decision.to_dict(), result, reality.to_dict(), receipt.to_dict()
        )
        return {
            "status": result["status"],
            "intent": optimized,
            "result": result,
            "evaluation": evaluation,
            "runtime": runtime_decision.to_dict(),
            "reality": reality.to_dict(),
            "memory": memory_record.to_dict(),
            "assurance": receipt.to_dict(),
            "evidence": evidence_entry.to_dict(),
            "world_state": dict(self.runtime.world_model.state),
        }

    def _record_evidence(
        self,
        intent: Dict[str, Any],
        runtime: Dict[str, Any],
        result: Dict[str, Any],
        reality: Dict[str, Any],
        assurance: Dict[str, Any],
    ):
        # Deliberately exclude wall-clock timestamps so cycle content remains comparable.
        payload = {
            "schema": "synapdrive.cycle-evidence.v2",
            "intent": {
                "intent": intent.get("intent"),
                "confidence": intent.get("confidence"),
                "source": intent.get("source"),
                "inference_authority": intent.get("inference_authority", "unspecified"),
                "confidence_semantics": intent.get("confidence_semantics", "unspecified"),
                "neural_decode_performed": bool(intent.get("neural_decode_performed", False)),
                "analysis_only": bool(intent.get("analysis_only", False)),
                "signal_quality": intent.get("signal_quality", 1.0),
                "uncertainty": intent.get("uncertainty"),
                "required_confidence": intent.get("required_confidence"),
            },
            "runtime": runtime,
            "result": {
                "status": result.get("status"),
                "intent": result.get("intent"),
                "confidence": result.get("confidence"),
                "fallback_action": result.get("fallback_action"),
                "fallback_result": result.get("fallback_result"),
                "plant": result.get("plant"),
            },
            "reality": reality,
            "assurance_receipt_id": assurance.get("receipt_id"),
            "assurance_passed": assurance.get("passed"),
        }
        return self.evidence.record(payload)

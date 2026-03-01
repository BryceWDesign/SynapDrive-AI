from __future__ import annotations

from typing import Any, Dict, Optional
import random

from synapdrive_ai.bci.signal_simulator import BrainSignalSimulator
from synapdrive_ai.agi.core_reasoning import AGICoreReasoner
from synapdrive_ai.agi.cognitive_optimizer import CognitiveOptimizer
from synapdrive_ai.agi.meta_evaluator import MetaEvaluator
from synapdrive_ai.action.decision_router import DecisionRouter
from synapdrive_ai.memory.episodic_memory import EpisodicMemory
from synapdrive_ai.safety.safety_guard import SafetyGuard
from synapdrive_ai.vision.visual_inference import VisualInferenceEngine
from synapdrive_ai.bci.intent_generator import generate_intent


class SynapDrivePipeline:
    """
    Canonical end-to-end simulation pipeline.

    Determinism support:
      simulate_delay=False disables actuation sleep so replay/tests are fast and repeatable.
    """

    def __init__(self, simulate_delay: bool = True) -> None:
        self.simulator = BrainSignalSimulator()
        self.reasoner = AGICoreReasoner()

        self.memory = EpisodicMemory()
        self.visual = VisualInferenceEngine()

        self.optimizer = CognitiveOptimizer()
        self.optimizer.memory = self.memory
        self.optimizer.visual = self.visual

        self.guard = SafetyGuard()
        self.router = DecisionRouter(simulate_delay=simulate_delay)
        self.evaluator = MetaEvaluator()

    def run_text_command(self, command_text: str, image_label: Optional[str] = None) -> Dict[str, Any]:
        intent_packet = generate_intent(command_text)
        return self.run_intent_packet(intent_packet, image_label=image_label)

    def run_signal_event(self, label: Optional[str] = None, image_label: Optional[str] = None) -> Dict[str, Any]:
        label = label or random.choice(["left_arm", "right_arm", "walk", "stop", "calculate", "recall", "explore"])
        signal = self._generate_signal_for_label(label)
        intent_packet = self.reasoner.receive_signal(label, signal)
        return self.run_intent_packet(intent_packet, image_label=image_label)

    def run_intent_packet(self, intent_packet: Dict[str, Any], image_label: Optional[str] = None) -> Dict[str, Any]:
        """
        Public entrypoint for integrations + replay.
        """
        return self._run_common(intent_packet, image_label=image_label)

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
            raise ValueError(f"Unknown signal label: {label}")
        return self.simulator.generate_waveform(patterns[label])

    def _run_common(self, intent_packet: Dict[str, Any], image_label: Optional[str]) -> Dict[str, Any]:
        optimized = self.optimizer.optimize(intent_packet, image_label=image_label)

        is_safe, reason = self.guard.evaluate_safety(optimized)
        if not is_safe:
            return {
                "status": "blocked",
                "reason": reason,
                "intent": optimized,
                "result": {
                    "status": "blocked",
                    "intent": optimized.get("intent", "unknown"),
                    "confidence": optimized.get("confidence", 0.0),
                    "duration": 0.0,
                },
                "evaluation": {
                    "score": 0.0,
                    "total_actions": 0,
                    "avg_score": 0.0,
                },
            }

        result = self.router.route(optimized)

        try:
            self.memory.record_episode(optimized, result)
        except Exception:
            pass

        evaluation = self.evaluator.evaluate(optimized, result)

        return {
            "status": result["status"],
            "intent": optimized,
            "result": result,
            "evaluation": evaluation,
        }

    def get_action_log(self):
        return self.router.get_action_log()

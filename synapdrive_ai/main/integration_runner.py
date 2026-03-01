# synapdrive_ai/main/integration_runner.py

from __future__ import annotations

from typing import Any, Dict, Optional

from synapdrive_ai.bci.intent_generator import generate_intent
from synapdrive_ai.agi.cognitive_optimizer import CognitiveOptimizer
from synapdrive_ai.agi.meta_evaluator import MetaEvaluator
from synapdrive_ai.action.decision_router import DecisionRouter
from synapdrive_ai.memory.episodic_memory import EpisodicMemory
from synapdrive_ai.safety.safety_guard import SafetyGuard


class SynapDriveExecutor:
    """
    Orchestrates a full simulated cognitive loop:

      input → intent_generator → cognitive_optimizer → safety_guard → decision_router
                    ↘ episodic_memory ← meta_evaluator ↗

    This is simulation-first. No medical/clinical claims. No real BCI hardware.
    """

    def __init__(self) -> None:
        self.optimizer = CognitiveOptimizer()
        self.evaluator = MetaEvaluator()
        self.router = DecisionRouter()
        self.memory = EpisodicMemory()
        self.guard = SafetyGuard()

    def run_once(self, simulated_input: str, simulated_image: Optional[str] = None) -> Dict[str, Any]:
        # Step 1: Generate intent from simulated input
        intent_packet = generate_intent(simulated_input)

        # Step 2: Optimize intent using (simulated) memory + visual context
        optimized_intent = self.optimizer.optimize(intent_packet, image_label=simulated_image)

        # Step 3: Safety check
        is_safe, reason = self.guard.evaluate_safety(optimized_intent)
        if not is_safe:
            # Return a consistent shape so CLI/UI never crashes
            blocked_result = {
                "status": "blocked",
                "reason": reason,
                "intent": optimized_intent.get("intent", "unknown"),
                "confidence": optimized_intent.get("confidence", 0.0),
                "duration": 0.0,
            }
            evaluation = {
                "score": 0.0,
                "total_actions": 0,
                "avg_score": 0.0,
            }
            return {
                "status": "blocked",
                "reason": reason,
                "intent": optimized_intent,
                "result": blocked_result,
                "evaluation": evaluation,
            }

        # Step 4: Route decision (execute)
        result_packet = self.router.route(optimized_intent)

        # Step 5: Record memory (only if execution produced expected fields)
        try:
            self.memory.record_episode(optimized_intent, result_packet)
        except Exception:
            # Do not crash the loop if memory schema changes later
            pass

        # Step 6: Meta-evaluate performance
        evaluation = self.evaluator.evaluate(optimized_intent, result_packet)

        return {
            "status": result_packet["status"],
            "intent": optimized_intent,
            "result": result_packet,
            "evaluation": evaluation,
        }

# synapdrive_ai/main/integration_runner.py

from synapdrive_ai.bci.intent_generator import generate_intent
from synapdrive_ai.agi.cognitive_optimizer import CognitiveOptimizer
from synapdrive_ai.agi.meta_evaluator import MetaEvaluator
from synapdrive_ai.action.decision_router import DecisionRouter
from synapdrive_ai.memory.episodic_memory import EpisodicMemory
from synapdrive_ai.safety.safety_guard import SafetyGuard

class SynapDriveExecutor:
    """
    Orchestrates a full AGI loop: intent → optimization → safety → action → memory → evaluation
    """

    def __init__(self):
        self.optimizer = CognitiveOptimizer()
        self.evaluator = MetaEvaluator()
        self.router = DecisionRouter()
        self.memory = EpisodicMemory()
        self.guard = SafetyGuard()

    def run_once(self, simulated_input, simulated_image=None):
        # Step 1: Generate intent from simulated BCI input
        intent_packet = generate_intent(simulated_input)

        # Step 2: Optimize with memory + visual context
        optimized_intent = self.optimizer.optimize(intent_packet, image_label=simulated_image)

        # Step 3: Safety check
        is_safe, reason = self.guard.evaluate_safety(optimized_intent)
        if not is_safe:
            return {
                "status": "blocked",
                "reason": reason,
                "intent": optimized_intent
            }

        # Step 4: Route decision (simulate action)
        result_packet = self.router.route(optimized_intent)

        # Step 5: Record memory
        self.memory.record_episode(optimized_intent, result_packet)

        # Step 6: Meta-evaluate performance
        evaluation = self.evaluator.evaluate(optimized_intent, result_packet)

        return {
            "status": result_packet["status"],
            "intent": optimized_intent,
            "result": result_packet,
            "evaluation": evaluation
        }

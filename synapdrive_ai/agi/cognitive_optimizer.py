# synapdrive_ai/agi/cognitive_optimizer.py

import random
from synapdrive_ai.memory.episodic_memory import EpisodicMemory
from synapdrive_ai.vision.visual_inference import VisualInferenceEngine

class CognitiveOptimizer:
    """
    Refines AGI decisions by integrating memory recall and visual feedback,
    dynamically adjusting confidence and context for action refinement.
    """

    def __init__(self):
        self.memory = EpisodicMemory()
        self.visual = VisualInferenceEngine()

    def optimize(self, intent_packet, image_label=None):
        """
        Adjusts the intent packet based on visual and memory signals.

        Args:
            intent_packet (dict): Original AGI intent decision
            image_label (str): Optional simulated camera label for visual input

        Returns:
            dict: Optimized intent packet
        """
        visual_context = self.visual.infer(image_label) if image_label else None
        memory_context = self.memory.find_by_intent(intent_packet["intent"])

        # Boost confidence if memory has positive outcomes
        boost = 0.05 * len(memory_context) if memory_context else -0.1
        visual_boost = 0.05 if visual_context and visual_context["certainty"] > 0.8 else 0

        adjusted_confidence = round(min(1.0, intent_packet["confidence"] + boost + visual_boost), 2)

        optimized_packet = intent_packet.copy()
        optimized_packet["confidence"] = adjusted_confidence
        optimized_packet["memory_context"] = memory_context

        if visual_context:
            optimized_packet["visual_tag"] = visual_context["visual_tag"]
            optimized_packet["visual_certainty"] = visual_context["certainty"]

        return optimized_packet

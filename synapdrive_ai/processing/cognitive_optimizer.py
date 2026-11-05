from __future__ import annotations

from synapdrive_ai.memory.episodic_memory import EpisodicMemory
from synapdrive_ai.vision.visual_inference import VisualInferenceEngine


class CognitiveOptimizer:
    """Outcome-aware context enrichment for an intent packet.

    This component never treats a declared visual label as additional decoder evidence.
    Previously successful, reality-aligned episodes are attached as review context only.
    They never modify decoder/parser confidence: confidence calibration belongs to the
    decoder evaluation path, not an arbitrary memory-count heuristic.
    """

    def __init__(self) -> None:
        self.memory = EpisodicMemory()
        self.visual = VisualInferenceEngine()

    def optimize(self, intent_packet, image_label=None):
        visual_context = self.visual.infer(image_label) if image_label else None
        finder = getattr(self.memory, "find_successful_by_intent", self.memory.find_by_intent)
        memory_context = finder(intent_packet["intent"])

        optimized_packet = intent_packet.copy()
        optimized_packet["memory_context"] = memory_context
        optimized_packet["history_support_count"] = len(memory_context)
        optimized_packet["history_adjustment"] = 0.0
        if visual_context:
            optimized_packet["visual_tag"] = visual_context["visual_tag"]
            optimized_packet["visual_context"] = visual_context
        return optimized_packet

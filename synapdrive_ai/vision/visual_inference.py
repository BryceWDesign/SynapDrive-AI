from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class VisualContext:
    """Declared visual context, not computer-vision inference.

    The current repository does not ship an image model. A caller may provide a label
    such as ``road`` or ``hazard`` to exercise context-aware control logic. The returned
    certainty therefore describes whether the declaration mapped to a known vocabulary,
    not confidence produced by a perception model.
    """

    visual_tag: str
    recognized: bool
    evidence_kind: str = "declared-label"
    model_used: bool = False

    @property
    def certainty(self) -> float:
        return 1.0 if self.recognized else 0.0

    def to_dict(self) -> Dict[str, object]:
        return {
            "visual_tag": self.visual_tag,
            "certainty": self.certainty,
            "recognized": self.recognized,
            "evidence_kind": self.evidence_kind,
            "model_used": self.model_used,
        }


class VisualInferenceEngine:
    """Backward-compatible mapper for caller-declared visual labels.

    The historical class name is retained so existing imports keep working. This class
    performs no image inference and intentionally contains no pseudo-random confidence.
    """

    def __init__(self) -> None:
        self.categories = {
            "road": "navigation_path",
            "person": "human_detected",
            "vehicle": "object_vehicle",
            "hazard": "obstacle_detected",
            "none": "no_visual_target",
        }

    def infer(self, image_label: str | None) -> Dict[str, object]:
        normalized = (image_label or "").strip().lower()
        if normalized in self.categories:
            return VisualContext(self.categories[normalized], True).to_dict()
        return VisualContext("unknown_visual", False).to_dict()

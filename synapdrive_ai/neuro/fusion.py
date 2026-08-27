from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping

from synapdrive_ai.neuro.uncertainty import estimate_uncertainty, normalize_distribution


@dataclass(frozen=True)
class ModalityEvidence:
    modality: str
    probabilities: Mapping[str, float]
    reliability: float


@dataclass(frozen=True)
class FusionResult:
    probabilities: Dict[str, float]
    intent: str
    confidence: float
    uncertainty: float
    weights: Dict[str, float]


class WeightedEvidenceFusion:
    """Reliability-weighted late fusion for independent modality decoders."""

    def fuse(self, evidence: Iterable[ModalityEvidence]) -> FusionResult:
        items = list(evidence)
        if not items:
            raise ValueError("at least one modality is required")
        labels = sorted({label for item in items for label in item.probabilities})
        accum = {label: 0.0 for label in labels}
        weights: Dict[str, float] = {}
        total_weight = 0.0
        members = []
        for item in items:
            probs = normalize_distribution(item.probabilities)
            members.append(probs)
            w = max(0.0, min(1.0, float(item.reliability)))
            weights[item.modality] = w
            total_weight += w
            for label in labels:
                accum[label] += w * probs.get(label, 0.0)
        if total_weight <= 0:
            raise ValueError("at least one modality must have positive reliability")
        fused = normalize_distribution({k: v / total_weight for k, v in accum.items()})
        uncertainty = estimate_uncertainty(fused, members)
        return FusionResult(
            probabilities=fused,
            intent=uncertainty.top_label,
            confidence=uncertainty.top_probability,
            uncertainty=uncertainty.combined,
            weights=weights,
        )

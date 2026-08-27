from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping

import numpy as np

from synapdrive_ai.benchmarking.dataset import EpochDataset
from synapdrive_ai.benchmarking.decoders import Decoder
from synapdrive_ai.benchmarking.evaluation import BenchmarkReport, evaluate_decoder


@dataclass(frozen=True)
class QualificationPolicy:
    """Local software gates for promoting a decoder into simulation use.

    These thresholds are engineering policy choices, not clinical validation criteria.
    """

    min_balanced_accuracy: float = 0.60
    max_ece: float = 0.30
    max_brier_score: float = 0.80
    min_coverage: float = 0.20
    abstain_threshold: float = 0.55

    def __post_init__(self) -> None:
        for name in (
            "min_balanced_accuracy",
            "max_ece",
            "max_brier_score",
            "min_coverage",
            "abstain_threshold",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")


@dataclass(frozen=True)
class DecoderQualification:
    qualified: bool
    reason: str
    report: BenchmarkReport
    policy: QualificationPolicy

    def to_dict(self) -> Dict[str, Any]:
        return {
            "qualified": self.qualified,
            "reason": self.reason,
            "report": self.report.to_dict(),
            "policy": asdict(self.policy),
        }


class QualifiedDecoderAdapter:
    """Bridge a benchmark decoder into the runtime's explicit decoder callback contract.

    Construction performs a deterministic held-out evaluation. Only if all local software
    gates pass is the decoder refit on the complete supplied labeled dataset. Runtime
    decoding then requires exact channel count and sampling-rate agreement plus an explicit
    label-to-action mapping. Unmapped labels and low-confidence outputs abstain.

    Passing this gate means only that the decoder met this repository's local evaluation
    policy on the supplied data. It does not establish participant generalization, clinical
    validity, or physical-control safety.
    """

    def __init__(
        self,
        decoder: Decoder,
        dataset: EpochDataset,
        action_map: Mapping[object, str],
        *,
        policy: QualificationPolicy | None = None,
        test_fraction: float = 0.25,
        seed: int = 7,
    ) -> None:
        self.decoder = decoder
        self.dataset = dataset
        self.action_map = dict(action_map)
        self.policy = policy or QualificationPolicy()
        self.report = evaluate_decoder(
            decoder,
            dataset,
            test_fraction=test_fraction,
            seed=seed,
            abstain_threshold=self.policy.abstain_threshold,
        )
        self.qualification = self._qualify(self.report)
        if self.qualification.qualified:
            self.decoder.fit(dataset.epochs, dataset.labels, dataset.sampling_rate)

    def _qualify(self, report: BenchmarkReport) -> DecoderQualification:
        failures: list[str] = []
        if report.balanced_accuracy < self.policy.min_balanced_accuracy:
            failures.append("balanced-accuracy-below-policy")
        if report.ece > self.policy.max_ece:
            failures.append("ece-above-policy")
        if report.brier_score > self.policy.max_brier_score:
            failures.append("brier-score-above-policy")
        if report.coverage < self.policy.min_coverage:
            failures.append("coverage-below-policy")

        mapped_classes = {str(key) for key in self.action_map}
        missing = [str(cls) for cls in report.classes if str(cls) not in mapped_classes]
        if missing:
            failures.append("unmapped-decoder-classes:" + ",".join(sorted(missing)))

        qualified = not failures
        reason = "local qualification policy passed" if qualified else "; ".join(failures)
        return DecoderQualification(qualified, reason, report, self.policy)

    def __call__(self, data: np.ndarray, metadata: Mapping[str, Any]) -> Dict[str, Any]:
        if not self.qualification.qualified:
            return self._abstention("decoder did not pass local qualification policy")

        samples = np.asarray(data, dtype=float)
        if samples.ndim != 2:
            return self._abstention("decoder input must have shape channels x samples")
        expected_channels = int(self.dataset.epochs.shape[1])
        if samples.shape[0] != expected_channels:
            return self._abstention(
                f"channel-count mismatch: got {samples.shape[0]}, expected {expected_channels}"
            )

        sampling_rate = float(metadata.get("sampling_rate", 0.0) or 0.0)
        if not np.isclose(sampling_rate, self.dataset.sampling_rate, rtol=0.0, atol=1e-9):
            return self._abstention(
                "sampling-rate mismatch: "
                f"got {sampling_rate}, expected {self.dataset.sampling_rate}"
            )

        probabilities = self.decoder.predict_proba(samples[None, :, :], sampling_rate)[0]
        classes = np.asarray(self.decoder.classes_)
        best_idx = int(np.argmax(probabilities))
        label = classes[best_idx]
        confidence = float(probabilities[best_idx])
        action = self._mapped_action(label)

        action_probabilities: Dict[str, float] = {}
        for cls, probability in zip(classes, probabilities, strict=True):
            mapped = self._mapped_action(cls)
            if mapped is not None:
                action_probabilities[mapped] = action_probabilities.get(mapped, 0.0) + float(
                    probability
                )

        if action is None:
            return self._abstention(f"decoder label {label!r} has no action mapping")
        if confidence < self.policy.abstain_threshold:
            packet = self._abstention(
                f"decoder confidence {confidence:.6f} below abstain threshold "
                f"{self.policy.abstain_threshold:.6f}"
            )
            packet["decoder_label"] = str(label)
            packet["raw_decoder_confidence"] = confidence
            packet["probabilities"] = action_probabilities
            return packet

        return {
            "intent": action,
            "confidence": confidence,
            "probabilities": action_probabilities,
            "source": f"qualified-decoder/{type(self.decoder).__name__}",
            "memory_context": [],
            "inference_authority": "locally-qualified-decoder",
            "confidence_semantics": "model-probability-local-holdout-qualified",
            "neural_decode_performed": True,
            "analysis_only": False,
            "decoder_label": str(label),
            "decoder_qualification": self.qualification.to_dict(),
        }

    def _mapped_action(self, label: object) -> str | None:
        if label in self.action_map:
            return str(self.action_map[label])
        label_text = str(label)
        for key, value in self.action_map.items():
            if str(key) == label_text:
                return str(value)
        return None

    def _abstention(self, reason: str) -> Dict[str, Any]:
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "probabilities": {"unknown": 1.0},
            "source": f"qualified-decoder/{type(self.decoder).__name__}",
            "memory_context": [],
            "inference_authority": "decoder-abstention",
            "confidence_semantics": "abstained",
            "neural_decode_performed": bool(self.qualification.qualified),
            "analysis_only": True,
            "abstention_reason": reason,
            "decoder_qualification": self.qualification.to_dict(),
        }

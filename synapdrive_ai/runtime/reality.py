from __future__ import annotations

from typing import Any, Mapping

from synapdrive_ai.runtime.contracts import RealityVerdict


class RealityReconciler:
    """Compare predicted software outcome with result and user-error feedback."""

    def reconcile(
        self,
        *,
        predicted_success: float,
        result_packet: Mapping[str, Any],
        feedback: Mapping[str, Any] | None = None,
        errp_threshold: float = 0.70,
    ) -> RealityVerdict:
        observed_success = str(result_packet.get("status", "")) in {
            "success",
            "executed",
        }
        predicted_success = max(0.0, min(1.0, float(predicted_success)))
        error_probability = 0.0
        if feedback:
            raw_probability = float(feedback.get("errp_probability", 0.0))
            error_probability = max(0.0, min(1.0, raw_probability))
            explicit = feedback.get("accepted")
            if explicit is False:
                error_probability = 1.0
        prediction_error = abs(predicted_success - float(observed_success))
        if error_probability >= errp_threshold:
            return RealityVerdict(
                False,
                "contradicted",
                "user/error-potential feedback contradicts action",
                round(prediction_error, 6),
                error_probability,
            )
        if predicted_success >= 0.5 and not observed_success:
            return RealityVerdict(
                False,
                "failed",
                "predicted success but execution did not succeed",
                round(prediction_error, 6),
                error_probability,
            )
        return RealityVerdict(
            True,
            "aligned",
            "observed outcome is consistent with current prediction",
            round(prediction_error, 6),
            error_probability,
        )

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from synapdrive_ai.assurance.contracts import AssuranceReceipt, build_receipt, normalize_confidence


class AssuranceMonitor:
    """
    Runtime invariant monitor for the simulation control loop.

    The monitor is deliberately non-actuating: it observes one completed cycle, validates
    the internal contract, stores a compact receipt, and exposes aggregate health data.
    """

    def __init__(self) -> None:
        self._receipts: List[AssuranceReceipt] = []

    def record_cycle(
        self,
        *,
        intent_packet: Dict[str, Any],
        image_label: Optional[str],
        safety_allowed: bool,
        safety_reason: str,
        result_packet: Dict[str, Any],
        evaluation: Dict[str, Any],
        executed: bool,
    ) -> AssuranceReceipt:
        result_status = str(result_packet.get("status") or "unknown")
        issues = self._validate_cycle(
            intent_packet=intent_packet,
            safety_allowed=safety_allowed,
            result_status=result_status,
            executed=executed,
        )
        receipt = build_receipt(
            cycle_index=len(self._receipts) + 1,
            intent_packet=intent_packet,
            image_label=image_label,
            safety_allowed=safety_allowed,
            safety_reason=safety_reason,
            result_status=result_status,
            evaluation_score=evaluation.get("score", 0.0),
            issues=issues,
        )
        self._receipts.append(receipt)
        return receipt

    def latest(self) -> Optional[AssuranceReceipt]:
        return self._receipts[-1] if self._receipts else None

    def history(self) -> Tuple[AssuranceReceipt, ...]:
        return tuple(self._receipts)

    def health_report(self) -> Dict[str, Any]:
        total = len(self._receipts)
        blocked = sum(1 for receipt in self._receipts if receipt.result_status == "blocked")
        passed = sum(1 for receipt in self._receipts if receipt.passed)
        avg_confidence = (
            round(sum(receipt.confidence for receipt in self._receipts) / total, 3)
            if total
            else 0.0
        )
        avg_score = (
            round(sum(receipt.evaluation_score for receipt in self._receipts) / total, 3)
            if total
            else 0.0
        )
        return {
            "schema": "synapdrive.assurance.health.v1",
            "total_cycles": total,
            "passed_receipts": passed,
            "failed_receipts": total - passed,
            "blocked_cycles": blocked,
            "executed_cycles": total - blocked,
            "average_confidence": avg_confidence,
            "average_evaluation_score": avg_score,
            "latest_receipt_id": self._receipts[-1].receipt_id if self._receipts else None,
        }

    def _validate_cycle(
        self,
        *,
        intent_packet: Dict[str, Any],
        safety_allowed: bool,
        result_status: str,
        executed: bool,
    ) -> Tuple[str, ...]:
        issues: List[str] = []
        intent = intent_packet.get("intent")
        confidence = normalize_confidence(intent_packet.get("confidence", 0.0))

        if not isinstance(intent, str) or not intent.strip():
            issues.append("intent-missing-or-empty")
        if confidence != intent_packet.get("confidence", confidence):
            issues.append("confidence-was-normalized")

        if safety_allowed:
            if result_status == "blocked":
                issues.append("allowed-cycle-returned-blocked-result")
            if not executed:
                issues.append("allowed-cycle-was-not-executed")
        else:
            if result_status != "blocked":
                issues.append("blocked-cycle-returned-nonblocked-result")
            if executed:
                issues.append("blocked-cycle-reached-actuation")

        return tuple(issues)

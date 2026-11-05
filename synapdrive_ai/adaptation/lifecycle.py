"""Exact-artifact promotion, one-use audit evidence and dependent rollback.

Evidence is supplied by the evaluator, not accepted from proposal worker messages.
This local lifecycle does not establish physiological co-adaptation stability.
"""

from __future__ import annotations

import math
from copy import deepcopy
from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    artifact_id: str
    parent_id: str
    feedback_ids: tuple[str, ...] = ()


class ModelLifecycle:
    def __init__(self, baseline_id):
        self.active = baseline_id
        self.history = [baseline_id]
        self.candidates: dict[str, Candidate] = {}
        self.evidence: dict[str, dict] = {}
        self.used_audits: set[str] = set()
        self.invalid_feedback: set[str] = set()
        self.events: list[dict] = []
        self.parents: dict[str, Candidate] = {}

    def propose(self, artifact_id, feedback_ids=()):
        if (
            artifact_id == self.active
            or artifact_id in self.parents
            or artifact_id in self.candidates
        ):
            raise ValueError("artifact already active or previously promoted")
        candidate = Candidate(artifact_id, self.active, tuple(feedback_ids))
        self.candidates[artifact_id] = candidate
        self.events.append({"event": "shadow", "artifact": artifact_id})
        return candidate

    def evaluate(
        self,
        artifact_id,
        *,
        audit_id,
        baseline_utility,
        candidate_utility,
        baseline_unsafe,
        candidate_unsafe,
        samples,
    ):
        if audit_id in self.used_audits:
            raise ValueError("audit set already consumed; choose independent evidence")
        if artifact_id not in self.candidates or not audit_id or samples < 1:
            raise ValueError("missing candidate, audit identity or samples")
        values = (baseline_utility, candidate_utility, baseline_unsafe, candidate_unsafe)
        if not all(isinstance(v, (float, int)) and math.isfinite(v) for v in values):
            raise ValueError("finite metrics required")
        if not 0 <= baseline_unsafe <= samples or not 0 <= candidate_unsafe <= samples:
            raise ValueError("unsafe counts exceed denominator")
        self.used_audits.add(audit_id)
        self.evidence[artifact_id] = {
            "audit_id": audit_id,
            "samples": samples,
            "eligible": candidate_utility > baseline_utility
            and candidate_unsafe <= baseline_unsafe,
        }
        return deepcopy(self.evidence[artifact_id])

    def promote(self, artifact_id):
        candidate = self.candidates[artifact_id]
        if (
            candidate.parent_id != self.active
            or not self.evidence.get(artifact_id, {}).get("eligible")
            or self.invalid_feedback.intersection(candidate.feedback_ids)
        ):
            raise ValueError("candidate failed evidence, lineage or parent gate")
        self.parents[artifact_id] = candidate
        self.active = artifact_id
        self.history.append(artifact_id)
        self.events.append({"event": "promoted", "artifact": artifact_id})

    def contradict(self, feedback_id):
        self.invalid_feedback.add(feedback_id)
        # Roll back the full dependent lineage, including promoted descendants.
        while self.active in self.parents:
            lineage, cursor = [], self.active
            while cursor in self.parents:
                node = self.parents[cursor]
                lineage.append(node)
                cursor = node.parent_id
            affected = [n for n in lineage if self.invalid_feedback.intersection(n.feedback_ids)]
            if not affected:
                break
            oldest = affected[-1]
            self.active = oldest.parent_id
            self.events.append(
                {"event": "rolled-back", "artifact": self.active, "feedback": feedback_id}
            )
        return self.active

"""Executable supervised decoder-update lifecycle using exact trained artifacts.

The evaluator owns scoring and audit consumption. Proposals supply models, not
promotion metrics. Actual benefit must still be measured on the intended cohort.
"""

from __future__ import annotations

import hashlib
from copy import deepcopy

import numpy as np

from synapdrive_ai.adaptation.lifecycle import ModelLifecycle
from synapdrive_ai.decoding import EEGDecoder, metrics


class DecoderUpdates:
    def __init__(self, baseline: EEGDecoder):
        identity = baseline.artifact_id()
        self._models = {identity: deepcopy(baseline)}
        self.lifecycle = ModelLifecycle(identity)
        self.audit_trials: set[str] = set()
        self.audit_epoch_hashes: set[str] = set()

    def stage(self, candidate: EEGDecoder, feedback_ids=()):
        if len(self._models) >= 16:
            raise ValueError("candidate budget exhausted")
        if candidate.identity != self._models[self.lifecycle.active].identity:
            raise ValueError("update cannot silently change acquisition contract")
        artifact_id = candidate.artifact_id()
        self.lifecycle.propose(artifact_id, feedback_ids)
        self._models[artifact_id] = deepcopy(candidate)
        return artifact_id

    @staticmethod
    def _outcomes(model, x, y, threshold):
        probs = model.predict_proba(x)
        prediction = model.classes[probs.argmax(1)]
        accepted = (probs.max(1) >= threshold) & (prediction != "rest")
        wrong = accepted & (prediction != y)
        utility = float((np.sum(accepted & (prediction == y)) - 4 * np.sum(wrong)) / len(y))
        return utility, int(wrong.sum())

    def evaluate(self, artifact_id, x, y, *, trial_ids, threshold=0.70):
        y = np.asarray(y, dtype=str)
        if len(trial_ids) != len(y) or len(set(trial_ids)) != len(y):
            raise ValueError("unique audit trial identity required")
        if self.audit_trials.intersection(trial_ids):
            raise ValueError("audit trials already consumed by candidate selection")
        candidate = self._models[artifact_id]
        baseline = self._models[self.lifecycle.active]
        hashes = set(EEGDecoder._hashes(x))
        if self.audit_epoch_hashes.intersection(hashes):
            raise ValueError(
                "audit epochs already consumed, regardless of renamed trial identities"
            )
        for model in (candidate, baseline):
            if hashes.intersection(model.train_hashes + model.calibration_hashes):
                raise ValueError("update audit overlaps fit/calibration data")
        audit_id = hashlib.sha256("\n".join(sorted(trial_ids)).encode()).hexdigest()
        self.audit_trials.update(trial_ids)
        self.audit_epoch_hashes.update(hashes)
        qualification = candidate.qualify(x, y, threshold=threshold)
        before, unsafe_before = self._outcomes(baseline, x, y, threshold)
        after, unsafe_after = self._outcomes(candidate, x, y, threshold)
        evidence = self.lifecycle.evaluate(
            artifact_id,
            audit_id=audit_id,
            baseline_utility=before,
            candidate_utility=after,
            baseline_unsafe=unsafe_before,
            candidate_unsafe=unsafe_after,
            samples=len(y),
        )
        if not qualification["qualified"]:
            self.lifecycle.evidence[artifact_id]["eligible"] = False
            evidence["eligible"] = False
        return {
            "promotion": evidence,
            "qualification": qualification,
            "baseline": metrics(baseline, x, y, threshold),
        }

    def promote(self, artifact_id):
        if self._models[artifact_id].artifact_id() != artifact_id:
            raise ValueError("evaluated artifact changed")
        self.lifecycle.promote(artifact_id)

    def packet(self, epoch, metadata, action_map):
        return self._models[self.lifecycle.active].packet(epoch, metadata, action_map)

    def contradict(self, feedback_id):
        return self.lifecycle.contradict(feedback_id)

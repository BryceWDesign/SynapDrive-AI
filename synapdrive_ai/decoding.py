"""Recorded-EEG research decoder: filter-bank CSP, shrinkage LDA, calibration.

All spatial filters, centering and class statistics are fitted on training data only.
Calibration changes a scalar temperature only. The audit set is never refitted.
Portable NPZ artifacts contain numeric arrays and JSON; pickle is never loaded.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from synapdrive_ai.neuro.signal_quality import SignalQualityAnalyzer
from synapdrive_ai.runtime.dispatch import digest


@dataclass(frozen=True)
class AcquisitionIdentity:
    channels: tuple[str, ...]
    sampling_rate: float
    samples: int
    units: str = "V"
    reference: str = "common-average-selected-channels"
    preprocessing: str = "epoch-sosfiltfilt-8-30Hz-order4-v1"
    modality: str = "scalp-EEG"
    device: str = "PhysioNet-EEGMMIDB-BCI2000"

    def __post_init__(self):
        if (
            len(set(self.channels)) != len(self.channels)
            or not self.channels
            or not np.isfinite(self.sampling_rate)
            or self.sampling_rate <= 60
            or self.samples < 32
        ):
            raise ValueError("invalid acquisition identity")

    def to_dict(self):
        out = asdict(self)
        out["channels"] = list(self.channels)
        return out


class EEGDecoder:
    def __init__(self, identity: AcquisitionIdentity):
        self.identity = identity
        self.classes = np.array([], dtype=str)
        self.filters = np.empty((0, len(identity.channels)))
        self.coef = np.empty((0, 0))
        self.intercept = np.empty(0)
        self.temperature = 1.0
        self.qualification: dict = {}
        self.drift_mean = np.empty(0)
        self.drift_scale = np.empty(0)
        self.train_hashes: list[str] = []
        self.calibration_hashes: list[str] = []
        self.audit_consumed = False

    def _prepare(self, x):
        from scipy.signal import butter, sosfiltfilt

        x = np.asarray(x, dtype=float)
        if (
            x.ndim != 3
            or x.shape[1:] != (len(self.identity.channels), self.identity.samples)
            or not np.isfinite(x).all()
        ):
            raise ValueError("non-finite EEG or acquisition shape mismatch")
        sos = butter(4, [8, 30], fs=self.identity.sampling_rate, btype="bandpass", output="sos")
        x = x - x.mean(axis=1, keepdims=True)
        return sosfiltfilt(sos, x, axis=-1)

    def _features(self, x):
        filtered = self._prepare(x)
        projected = np.einsum("fc,nct->nft", self.filters, filtered)
        variances = np.var(projected, axis=-1)
        return np.log(np.maximum(variances, 1e-24))

    def fit(self, x, y):
        from scipy.linalg import eigh

        x = self._prepare(x)
        y = np.asarray(y, dtype=str)
        self.classes = np.unique(y)
        if len(self.classes) < 2 or any(np.sum(y == c) < 3 for c in self.classes):
            raise ValueError("training needs at least three trials per class")
        cov = x @ np.swapaxes(x, 1, 2)
        cov /= np.maximum(np.trace(cov, axis1=1, axis2=2)[:, None, None], 1e-24)
        filters = []
        for c in self.classes:
            a, b = cov[y == c].mean(0), cov[y != c].mean(0)
            ridge = np.eye(a.shape[0]) * 1e-3
            _, vectors = eigh(a + ridge, a + b + 2 * ridge)
            filters.extend([vectors[:, 0], vectors[:, -1]])
        self.filters = np.asarray(filters)
        # Input is prepared again from original epochs by _features, with one filter pass.
        return self

    def train(self, x, y):
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

        self.train_hashes = self._hashes(x)
        if len(set(self.train_hashes)) != len(self.train_hashes):
            raise ValueError("duplicate training epochs")
        self.qualification = {}
        self.audit_consumed = False
        self.calibration_hashes = []
        self.fit(x, y)
        features = self._features(x)
        model = LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")
        model.fit(features, np.asarray(y, dtype=str))
        self.coef, self.intercept = model.coef_.copy(), model.intercept_.copy()
        self.classes = model.classes_.copy()
        self.drift_mean = features.mean(0)
        self.drift_scale = np.maximum(features.std(0), 0.1)
        return self

    def predict_proba(self, x):
        if not self.coef.size:
            raise ValueError("decoder is not trained")
        scores = self._features(x) @ self.coef.T + self.intercept
        if len(self.classes) == 2:
            scores = np.concatenate([np.zeros_like(scores), scores], axis=1)
        scores /= self.temperature
        scores -= scores.max(axis=1, keepdims=True)
        ex = np.exp(np.clip(scores, -700, 0))
        return ex / ex.sum(axis=1, keepdims=True)

    @staticmethod
    def _hashes(x):
        return [hashlib.sha256(np.asarray(e, dtype=np.float64).tobytes()).hexdigest() for e in x]

    def calibrate(self, x, y):
        calibration_hashes = self._hashes(x)
        if set(calibration_hashes).intersection(self.train_hashes):
            raise ValueError("calibration overlaps training epochs")
        if self.audit_consumed:
            raise ValueError("cannot recalibrate after consuming audit evidence")
        y = np.asarray(y, dtype=str)
        if set(y) != set(self.classes) or len(y) != len(x) or len(y) == 0:
            raise ValueError("invalid calibration labels")
        self._features(x)  # Validate the complete window before mutating calibration state.
        self.calibration_hashes = calibration_hashes
        labels = np.array([np.flatnonzero(self.classes == v)[0] for v in y])
        trials = []
        for temperature in (0.5, 1.0, 2.0, 4.0, 8.0):
            self.temperature = temperature
            prob = self.predict_proba(x)
            loss = -np.log(np.maximum(prob[np.arange(len(y)), labels], 1e-12)).mean()
            trials.append((float(loss), temperature))
        self.temperature = min(trials)[1]

    def artifact_id(self):
        h = hashlib.sha256(
            json.dumps(
                {
                    "identity": self.identity.to_dict(),
                    "train": self.train_hashes,
                    "calibration": self.calibration_hashes,
                },
                sort_keys=True,
            ).encode()
        )
        for a in (
            self.classes,
            self.filters,
            self.coef,
            self.intercept,
            self.drift_mean,
            self.drift_scale,
            np.array([self.temperature]),
        ):
            h.update(str(a.shape).encode())
            h.update(a.tobytes())
        return h.hexdigest()

    def qualify(
        self,
        x,
        y,
        *,
        threshold=0.70,
        min_balanced=0.55,
        min_coverage=0.10,
        max_ece=0.30,
        max_brier=0.80,
        expires_s=86400,
    ):
        if self.audit_consumed:
            raise ValueError(
                "audit already consumed; train a new candidate with independent evidence"
            )
        if set(self._hashes(x)).intersection(self.train_hashes + self.calibration_hashes):
            raise ValueError("audit overlaps training/calibration epochs")
        if not 0 < expires_s <= 86400 or not 0.5 <= threshold <= 1:
            raise ValueError("invalid qualification expiry or threshold")
        self.audit_consumed = True
        report = metrics(self, x, y, threshold)
        passed = (
            report["balanced_accuracy"] >= min_balanced
            and report["coverage"] >= min_coverage
            and report["ece"] <= max_ece
            and report["brier"] <= max_brier
        )
        self.qualification = {
            "qualified": passed,
            "artifact_id": self.artifact_id(),
            "expires_utc": time.time() + expires_s,
            "report": report,
            "threshold": threshold,
            "scope": "supplied-heldout-only",
            "gates": {
                "min_balanced": min_balanced,
                "min_coverage": min_coverage,
                "max_ece": max_ece,
                "max_brier": max_brier,
            },
        }
        return self.qualification

    def packet(self, epoch, metadata, action_map):
        def reject(reason):
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "source": "EEGDecoder",
                "analysis_only": True,
                "abstention_reason": reason,
            }

        q = self.qualification
        if (
            not q.get("qualified")
            or q.get("artifact_id") != self.artifact_id()
            or time.time() >= q.get("expires_utc", 0)
        ):
            return reject("missing, changed or expired qualified artifact")
        if metadata != self.identity.to_dict():
            return reject("full acquisition identity mismatch")
        try:
            quality = SignalQualityAnalyzer(self.identity.sampling_rate).analyze(epoch)
            if quality.score < 0.60:
                return reject("mandatory signal-quality exclusion")
            feat = self._features(np.asarray(epoch)[None])[0]
            drift = float(np.sqrt(np.mean(((feat - self.drift_mean) / self.drift_scale) ** 2)))
            if drift > 6:
                return reject("feature drift")
            probs = self.predict_proba(np.asarray(epoch)[None])[0]
        except ValueError as error:
            return reject(str(error))
        if set(action_map) != set(self.classes) or len(set(action_map.values())) != len(action_map):
            return reject("complete injective action mapping required")
        label = str(self.classes[int(probs.argmax())])
        confidence = float(probs.max())
        if label == "rest" or confidence < q["threshold"]:
            return reject("no-command or low-confidence epoch")
        return {
            "intent": action_map[label],
            "confidence": confidence,
            "source": "recorded-EEG/CSP-LDA",
            "inference_authority": "locally-qualified-decoder",
            "neural_decode_performed": True,
            "signal_quality": quality.score,
            "drift_score": drift,
            "qualification_id": q["artifact_id"],
            "evidence_id": digest({"epoch": self._hashes([epoch])[0], "model": q["artifact_id"]}),
            "confidence_semantics": "temperature-calibrated-model-probability",
            "probabilities": {action_map[str(c)]: float(v) for c, v in zip(self.classes, probs)},
        }

    def save(self, path):
        meta = {
            "schema": "synapdrive.decoder.v2",
            "identity": self.identity.to_dict(),
            "temperature": self.temperature,
            "qualification": self.qualification,
            "artifact_id": self.artifact_id(),
            "train_hashes": self.train_hashes,
            "calibration_hashes": self.calibration_hashes,
            "audit_consumed": self.audit_consumed,
        }
        np.savez_compressed(
            path,
            metadata=json.dumps(meta),
            classes=self.classes,
            filters=self.filters,
            coef=self.coef,
            intercept=self.intercept,
            drift_mean=self.drift_mean,
            drift_scale=self.drift_scale,
        )

    @classmethod
    def load(cls, path, expected_sha256=None):
        data = Path(path).read_bytes()
        if len(data) > 8_000_000:
            raise ValueError("artifact size budget exceeded")
        if expected_sha256 is not None and hashlib.sha256(data).hexdigest() != expected_sha256:
            raise ValueError("artifact checksum mismatch")
        with np.load(path, allow_pickle=False) as z:
            m = json.loads(str(z["metadata"]))
            if m["schema"] != "synapdrive.decoder.v2":
                raise ValueError("unsupported model schema")
            identity = m["identity"]
            identity["channels"] = tuple(identity["channels"])
            obj = cls(AcquisitionIdentity(**identity))
            for name in ("classes", "filters", "coef", "intercept", "drift_mean", "drift_scale"):
                setattr(obj, name, z[name].copy())
            obj.temperature = m["temperature"]
            obj.qualification = m["qualification"]
            obj.train_hashes = m["train_hashes"]
            obj.calibration_hashes = m["calibration_hashes"]
            obj.audit_consumed = m["audit_consumed"]
            if (
                not np.isfinite(obj.coef).all()
                or not np.isfinite(obj.filters).all()
                or not np.isfinite(obj.intercept).all()
                or not 0 < obj.temperature <= 8
            ):
                raise ValueError("invalid numeric model artifact")
            if obj.artifact_id() != m["artifact_id"]:
                raise ValueError("artifact identity mismatch")
            if expected_sha256 is None:
                obj.qualification = {
                    "qualified": False,
                    "reason": "no trusted artifact checksum supplied",
                }
            return obj


def metrics(model, x, y, threshold=0.70):
    from synapdrive_ai.benchmarking.evaluation import expected_calibration_error

    y = np.asarray(y, dtype=str)
    if len(y) == 0 or len(y) != len(x) or set(y) != set(model.classes):
        raise ValueError("evaluation must contain each supported class")
    p = model.predict_proba(x)
    pred = model.classes[p.argmax(1)]
    correct, confidence = pred == y, p.max(1)
    accepted = (confidence >= threshold) & (pred != "rest")
    onehot = np.array([[c == v for c in model.classes] for v in y], dtype=float)
    idle = y == "rest"
    return {
        "n": len(y),
        "accuracy": float(correct.mean()),
        "balanced_accuracy": float(np.mean([correct[y == c].mean() for c in model.classes])),
        "brier": float(np.sum((p - onehot) ** 2, axis=1).mean()),
        "ece": expected_calibration_error(confidence, correct.astype(float)),
        "coverage": float(accepted.mean()),
        "accepted": int(accepted.sum()),
        "selective_accuracy": float(correct[accepted].mean()) if accepted.any() else None,
        "idle_trials": int(idle.sum()),
        "idle_false_activations": int((idle & accepted).sum()),
        "threshold": threshold,
    }

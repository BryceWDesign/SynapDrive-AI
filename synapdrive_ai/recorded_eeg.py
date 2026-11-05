"""Fixed run-holdout EEGMMIDB experiment. Network only in --download mode.

Subjects S001-S008; R04 train, R08 calibrate, R12 locked evaluation.
One 0.5-3.5s epoch per annotation; T0 rest, T1 left fist imagery, T2 right.
No overlapping windows, no audit-driven model/hyperparameter selection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from synapdrive_ai.decoding import AcquisitionIdentity, EEGDecoder, metrics
from synapdrive_ai.pipeline import SynapDrivePipeline

CHANNELS = ("FC3", "FC4", "C3", "C1", "Cz", "C2", "C4", "CP3", "CP4")
ROOT = Path(__file__).resolve().parents[1]


def download(cache):
    cache.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(
        "https://physionet.org/files/eegmmidb/1.0.0/SHA256SUMS.txt", timeout=60
    ) as response:
        official = {
            line.split()[1].lstrip("./"): line.split()[0]
            for line in response.read().decode().splitlines()
        }
    jobs = [(s, r) for s in range(1, 9) for r in (4, 8, 12)]

    def fetch(job):
        s, r = job
        name = f"S{s:03d}R{r:02d}.edf"
        dest = cache / name
        url = f"https://physionet.org/files/eegmmidb/1.0.0/S{s:03d}/{name}"
        if not dest.exists():
            with urllib.request.urlopen(url, timeout=60) as response:
                dest.write_bytes(response.read())
        sha256 = hashlib.sha256(dest.read_bytes()).hexdigest()
        expected = official[f"S{s:03d}/{name}"]
        if sha256 != expected:
            raise ValueError(f"official source digest mismatch: {name}")
        return {
            "official_sha256": expected,
            "file": name,
            "url": url,
            "bytes": dest.stat().st_size,
            "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
        }

    with ThreadPoolExecutor(max_workers=6) as pool:
        records = list(pool.map(fetch, jobs))
    (cache / "sources.json").write_text(json.dumps(records, indent=2) + "\n")
    return records


def prepare(cache, output):
    import mne

    epochs, labels, subjects, runs, trials = [], [], [], [], []
    for subject in range(1, 9):
        for run in (4, 8, 12):
            raw = mne.io.read_raw_edf(
                cache / f"S{subject:03d}R{run:02d}.edf", preload=True, verbose=False
            )
            names = {name.strip(".").upper(): name for name in raw.ch_names}
            # Channel indices retain CHANNELS order and match MNE's typed picks API.
            picks = np.asarray(
                [raw.ch_names.index(names[c.upper()]) for c in CHANNELS], dtype=np.intp
            )
            # MNE's get_data annotations permit multiple return shapes;
            # normalize to an ndarray for channel/time slicing below.
            data = np.asarray(raw.get_data(picks=picks))
            sr = float(raw.info["sfreq"])
            if sr != 160:
                raise ValueError("unexpected sample rate")
            for i, (onset, duration, description) in enumerate(
                zip(raw.annotations.onset, raw.annotations.duration, raw.annotations.description)
            ):
                if description not in ("T0", "T1", "T2") or duration < 3.5:
                    continue
                start, stop = round((onset + 0.5) * sr), round((onset + 3.5) * sr)
                epoch = data[:, start:stop]
                if epoch.shape != (len(CHANNELS), 480):
                    continue
                epochs.append(epoch.astype(np.float32))
                labels.append({"T0": "rest", "T1": "left", "T2": "right"}[description])
                subjects.append(f"S{subject:03d}")
                runs.append(run)
                trials.append(f"S{subject:03d}/R{run:02d}/event{i}")
    identity = AcquisitionIdentity(CHANNELS, 160.0, 480)
    np.savez_compressed(
        output,
        X=np.array(epochs),
        y=np.array(labels),
        subject=np.array(subjects),
        run=np.array(runs),
        trial=np.array(trials),
        identity=json.dumps(identity.to_dict()),
        source="PhysioNet EEGMMIDB v1.0.0; runs 04/08/12; imagery + rest",
    )


def evaluate(dataset, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    with np.load(dataset, allow_pickle=False) as d:
        x, y, subject, run = (d[n] for n in ("X", "y", "subject", "run"))
        ident = json.loads(str(d["identity"]))
        ident["channels"] = tuple(ident["channels"])
        identity = AcquisitionIdentity(**ident)
        trial = d["trial"]
    if len(set(trial)) != len(trial):
        raise ValueError("duplicate trial identifiers")
    hashes = [hashlib.sha256(e.tobytes()).hexdigest() for e in x]
    if len(set(hashes)) != len(hashes):
        raise ValueError("duplicate epochs in dataset")
    results = []
    for participant in np.unique(subject):
        masks = [(subject == participant) & (run == r) for r in (4, 8, 12)]
        train, calibration, audit = masks
        model = EEGDecoder(identity).train(x[train], y[train])
        model.calibrate(x[calibration], y[calibration])
        # Thresholds were fixed before this audit was executed.
        qualification = model.qualify(x[audit], y[audit])
        base = metrics(model, x[audit], y[audit])
        rng = np.random.default_rng(20261102)
        permuted = EEGDecoder(identity).train(x[train], rng.permutation(y[train]))
        negative = metrics(permuted, x[audit], y[audit])
        predictions = model.classes[model.predict_proba(x[audit]).argmax(1)]
        truth = y[audit]
        pipe = SynapDrivePipeline(False)
        counts = {
            "success": 0,
            "blocked": 0,
            "correct_admitted": 0,
            "incorrect_admitted": 0,
            "idle_false_activations": 0,
        }
        abstention_reasons = {}
        for epoch, label in zip(x[audit], y[audit]):
            packet = model.packet(
                epoch,
                identity.to_dict(),
                {"left": "move_left", "right": "move_right", "rest": "no_command"},
            )
            result = pipe.run_intent_packet(packet)
            counts[result["status"]] += 1
            if result["status"] == "success":
                correct = (
                    packet["intent"]
                    == {"left": "move_left", "right": "move_right", "rest": "no_command"}[label]
                )
                counts["correct_admitted" if correct else "incorrect_admitted"] += 1
                counts["idle_false_activations"] += int(label == "rest")
            else:
                reason = packet.get("abstention_reason", result.get("reason", "unspecified"))
                abstention_reasons[reason] = abstention_reasons.get(reason, 0) + 1
        model.save(outdir / f"{participant}.npz")
        row = {
            "subject": str(participant),
            "train": int(train.sum()),
            "calibration": int(calibration.sum()),
            "audit": int(audit.sum()),
            "temperature": model.temperature,
            "qualification": qualification,
            "permuted_training_labels": negative,
            "canonical_runtime": counts,
            "abstention_reasons": abstention_reasons,
            "truth": truth.tolist(),
            "prediction": predictions.tolist(),
            "artifact_id": model.artifact_id(),
        }
        results.append(row)
        print(
            participant, base["balanced_accuracy"], qualification["qualified"], counts, flush=True
        )
    # Participant-cluster bootstrap, not a trial-independent interval.
    scores = np.array([r["qualification"]["report"]["balanced_accuracy"] for r in results])
    rng = np.random.default_rng(77)
    bootstrap = rng.choice(scores, (5000, len(scores)), replace=True).mean(1)
    report = {
        "schema": "synapdrive.recorded-eeg.experiment.v2",
        "dataset": "PhysioNet EEGMMIDB 1.0.0",
        "dataset_sha256": hashlib.sha256(Path(dataset).read_bytes()).hexdigest(),
        "evidence": "offline-recorded-scalp-EEG",
        "scope": "eight subjects; within-person heldout-run; not cross-session/person or clinical",
        "protocol": "R04 train; R08 scalar temperature; R12 audit; no refit",
        "epoch": "one 0.5-3.5s window per T0/T1/T2 annotation",
        "model": "one-vs-rest CSP + shrinkage LDA; 8-30Hz; fixed policy",
        "mean_balanced_accuracy": float(scores.mean()),
        "subject_bootstrap_95_interval": np.quantile(bootstrap, [0.025, 0.975]).tolist(),
        "qualified_subject_models": sum(r["qualification"]["qualified"] for r in results),
        "participants": results,
        "python": platform.python_version(),
    }
    (outdir / "recorded-eeg.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--cache", type=Path, default=ROOT.parent / "eeg-cache")
    parser.add_argument(
        "--dataset", type=Path, default=Path(__file__).parent / "assets/recorded_eeg.npz"
    )
    parser.add_argument("--out", type=Path, default=ROOT / "results/eeg")
    args = parser.parse_args()
    if args.download:
        sources = download(args.cache)
        prepare(args.cache, args.dataset)
        (ROOT / "results/EEG_SOURCES.json").write_text(json.dumps(sources, indent=2) + "\n")
    evaluate(args.dataset, args.out)


if __name__ == "__main__":
    main()

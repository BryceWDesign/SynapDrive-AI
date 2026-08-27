# SynapDrive-AI

SynapDrive-AI is a **simulation-first, evidence-producing neuroadaptive shared-autonomy research runtime**.

Its core question is deliberately narrow:

> Given a declared or decoded action candidate, what evidence and gates should exist before a system is allowed to execute even a simulated action?

The repository separates acquisition, decoding, uncertainty, permission, world-state prediction, action admission, simulated execution, feedback, memory consequence, adaptation, and evidence. It is designed so that missing knowledge produces an abstention or blocked cycle rather than an invented answer.

## Claim boundary

SynapDrive-AI is research software. It is **not**:

- a medical device;
- a clinical neural decoder;
- proof that a decoded class equals a person's true intent;
- evidence of human BCI accuracy unless a real labeled dataset and appropriate study design are supplied externally;
- a safe physical-control system;
- a cybersecurity certification;
- an AGI, consciousness, or sentience system.

The bundled actuator is simulated. The bundled deterministic synthetic signals are software verification fixtures, not physiological performance evidence.

See `docs/CLAIM_BOUNDARIES.md` before publishing results derived from this repository.

## What v1.0 actually implements

### Governed canonical runtime

Every action candidate passes through a single canonical pipeline in `synapdrive_ai/pipeline.py`:

```text
input packet
  -> context enrichment without confidence inflation
  -> class/action distribution
  -> uncertainty estimation
  -> signal-quality / drift / permission / world-model checks
  -> fail-closed runtime admission
  -> compatibility lexical guard
  -> simulated action router, only when admitted
  -> explicit symbolic world-state commit for modeled successful actions
  -> result and optional user/ErrP feedback reconciliation
  -> validated or quarantined evidence memory
  -> assurance receipt
  -> SHA-256 linked evidence entry
```

Unknown, analysis-only, unmodeled, low-confidence, high-uncertainty, low-quality, excessive-drift, permission-denied, or excessive-risk packets cannot reach the simulated action router.

### Explicit provenance

Packets can state:

- `inference_authority`;
- `confidence_semantics`;
- `neural_decode_performed`;
- `analysis_only`;
- signal quality and drift measurements;
- action probabilities;
- a stricter task-level confidence requirement.

A deterministic text parser is labeled as a declared-command path. A synthetic fixture label is labeled as synthetic ground truth. Hardware acquisition with no decoder is labeled acquisition-only and abstains.

### Signal integrity

`SignalQualityAnalyzer` checks:

- non-finite samples;
- flatline behavior;
- zero-valued dropout;
- observed-extrema clipping;
- line-frequency power.

Its aggregate score is an engineering heuristic used by the software gate. It is not a clinical EEG quality index.

### Offline EEG-style analysis

The lightweight loader supports:

- EDF;
- BDF with signed 24-bit sample decoding;
- CSV;
- NPY.

`BandPowerAnalyzer` computes delta, theta, alpha, beta, and gamma power plus ratio features. Its historical `confidence` field is explicitly an **uncalibrated spectral heuristic score**.

`SessionAnalyzer` without a decoder is analysis-only. Band ratios do not become movement commands. If an explicit decoder callback is supplied, its packet still passes through the canonical governed runtime.

### Decoder benchmark arena

Built-in inspectable baselines:

- spectral centroid decoder;
- log-Euclidean covariance centroid decoder;
- probability-averaging ensemble.

The arena reports:

- accuracy;
- balanced accuracy;
- multiclass Brier score;
- expected calibration error;
- abstention coverage;
- selective accuracy.

The benchmark consumes explicit labeled epochs. Missing labels are not invented.

### Locally qualified decoder bridge

`QualifiedDecoderAdapter` connects a benchmark decoder to runtime use only after deterministic held-out qualification.

It requires:

- configured balanced-accuracy, calibration, Brier, and coverage gates;
- a complete decoder-label to simulation-action map;
- matching runtime channel count;
- matching runtime sampling rate;
- confidence above the configured abstention threshold.

Failure yields an explicit abstention. Passing these local gates does not establish clinical validity, participant generalization, or hardware safety.

### Uncertainty and calibration

The neuro runtime includes:

- normalized class distributions;
- normalized entropy;
- top-class margin uncertainty;
- ensemble disagreement;
- a reliability calibrator fitted from supplied confidence/correctness observations.

### Decoder drift

`FeatureDriftMonitor` uses a fitted Mahalanobis-distance baseline. It has no meaningful baseline until the caller supplies calibration features.

### Multimodal fusion

`WeightedEvidenceFusion` combines caller-supplied probability distributions for modalities such as EEG, EMG, gaze, or context using explicit reliability weights. It does not fabricate modality reliability.

### ErrP research path

`ErrPFeatureExtractor` produces event-window features. `ErrPLDAClassifier` must be trained on supplied labeled calibration features before use.

An externally derived ErrP probability or explicit rejection can contradict an otherwise successful simulated execution, which causes the corresponding evidence memory to be quarantined rather than reinforced.

### Symbolic world model

The bundled world model predicts only registered simulation actions. An unknown action is infeasible, preserves state, and receives maximal software risk.

Successful modeled actions commit their predicted symbolic state. The built-in risk values are transparent repository policy fixtures, not empirical physical-risk probabilities.

### Counterfactual planning and shared autonomy

`CounterfactualPlanner` ranks a bounded caller-supplied action set using explicit fixed software-policy weights over:

- alignment with the supplied request;
- decoder confidence;
- caller goal score;
- reversibility;
- registered software risk.

`SharedAutonomyArbiter` proposes only. It does not bypass governance or directly actuate.

### Simplex and shadow control components

`SimplexController` dispatches to an advanced controller only after an allowed runtime decision; otherwise it invokes a caller-supplied reversionary controller.

`ShadowController` lets an experimental policy produce comparison decisions while granting it no authority over the trusted action path.

### Evidence-gated memory

Aligned successful cycles can enter evidence memory as `validated`. Contradicted cycles enter as `quarantined`.

Historical successful episodes can be attached as review context, but they do **not** increase decoder/parser confidence.

### Guarded adaptation

`GuardedThresholdAdapter` evaluates a candidate confidence threshold on caller-supplied held-out records. Promotion requires improved defined utility without increasing unsafe accepts on that supplied validation set.

This is bounded threshold adaptation, not autonomous model self-rewriting.

### Evidence, replay, and signing

Each canonical cycle produces:

- an assurance receipt;
- a SHA-256 linked evidence-chain entry.

The evidence CLI can:

- verify a chain;
- generate Ed25519 keys;
- sign an evidence ledger;
- verify a detached signature.

Hashing and signatures provide integrity/authenticity properties for recorded bytes. They do not prove sensor truth or scientific validity.

### Deterministic fault injection

The stress surface includes deterministic seeded injection for:

- Gaussian noise;
- contiguous dropout;
- clipping;
- line-frequency contamination;
- channel swaps.

Campaign results state which defined invariant was expected and whether the tested callback failed closed.

## Installation

Python 3.11 or newer is required.

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Optional acquisition dependencies are intentionally separate:

```text
pip install -r requirements-brainflow.txt
pip install -r requirements-lsl.txt
```

## Quick verification

```text
python -m compileall -q synapdrive_ai core scripts
python -m pytest -q
python -m scripts.run_v1_validation
```

With development dependencies installed:

```text
ruff check .
pyright
```

`make quality` runs compile, the complete pytest suite, and the release validator.

## Main CLI

Declared text command:

```text
python -m synapdrive_ai --text "move left" --no-delay
python -m synapdrive_ai --text "stop" --no-delay
python -m synapdrive_ai --text "switch mode to assistive" --no-delay
```

Explicit synthetic fixture label:

```text
python -m synapdrive_ai --signal walk --no-delay
python -m synapdrive_ai --signal stop --no-delay
```

`--signal` uses bundled deterministic-by-seed synthetic fixtures. It is not a neural decoder demonstration.

Optional caller-declared visual context:

```text
python -m synapdrive_ai --text "move left" --image road --no-delay
```

The bundled visual path maps a declared label only. It does not run image inference and it does not increase intent confidence.

## BrainFlow and LSL acquisition

```text
python -m synapdrive_ai --brainflow --bf-board-id -1 --bf-seconds 2 --no-delay
python -m synapdrive_ai --lsl --lsl-type EEG --lsl-seconds 2 --no-delay
```

The CLI deliberately has **no implicit hardware decoder**. These acquisition commands therefore abstain after collecting/quality-checking data.

Library users can supply a decoder callback to `BrainFlowIntentSource` or `LSLIntentSource`. `QualifiedDecoderAdapter` is the provided path for connecting a locally evaluated built-in decoder.

## Prepare a labeled benchmark dataset

Event CSV contract:

```csv
onset_s,label
1.0,left
3.0,right
5.0,left
7.0,right
```

Create epochs:

```text
synapdrive-prepare-dataset recording.edf events.csv --out epochs.npz --tmin 0 --tmax 1
```

Then benchmark:

```text
synapdrive-benchmark epochs.npz --decoder all --seed 7 --abstain 0.60
```

See `docs/BENCHMARKING.md` for the complete contract and qualification boundary.

## Offline spectral analysis

Synthetic analysis demo:

```text
python -m synapdrive_ai.neuro.cli demo
```

The demo injects a deterministic synthetic spectral burst. It does not claim neural intent.

Analyze a file:

```text
python -m synapdrive_ai.neuro.cli analyze session.edf --channel C3 --out results
```

List channels:

```text
python -m synapdrive_ai.neuro.cli analyze session.edf --channels
```

Sweep the uncalibrated spectral heuristic score:

```text
python -m synapdrive_ai.neuro.cli threshold session.edf --min-conf 0.4 0.5 0.6 0.7
```

That command is descriptive only. It does not report decoder accuracy or successful control.

## Sequential task plans

```text
python -m synapdrive_ai.neuro.cli plan --list
python -m synapdrive_ai.neuro.cli plan --task reach_grasp
```

Per-step minimum confidence is enforced **before** the simulated action router. A rejected step can freeze/defer or abort according to the plan fallback.

## Record and deterministic decision replay

```text
python -m synapdrive_ai --text "move left" --record runs.jsonl --no-delay
python -m synapdrive_ai --replay runs.jsonl
```

Replay reproduces the stored software decision input. It is not a re-acquisition of original neural signals.

## Evidence chain

```text
python -m synapdrive_ai --text "move left" --no-delay --evidence-out run.evidence.jsonl
synapdrive-evidence verify-chain run.evidence.jsonl
```

Generate signing keys:

```text
synapdrive-evidence keygen --private evidence-private.pem --public evidence-public.pem
```

Sign and verify:

```text
synapdrive-evidence sign run.evidence.jsonl --private evidence-private.pem --out run.signature.json
synapdrive-evidence verify-signature run.evidence.jsonl --public evidence-public.pem --signature run.signature.json
```

Keep private keys out of source control.

## Stress campaign

```text
synapdrive-stress --runs 100 --seed 7
```

The campaign is a defined negative-control surface, not exhaustive proof of safety.

## Local dashboard

```text
python -m synapdrive_ai.interface.web_dashboard
```

Open `http://127.0.0.1:5055` locally.

The dashboard routes text and synthetic fixture events through the canonical governed pipeline. It contains no fabricated external cloud/device routes.

## Repository layout

```text
synapdrive_ai/
  adaptation/       guarded threshold adaptation
  assurance/        receipts, hash chain, Ed25519 signing
  bci/              declared command + synthetic fixture surfaces
  benchmarking/     datasets, epoching, decoders, arena, runtime qualification
  cognition/        world model, counterfactual planning, shared autonomy, expectation deltas
  governance/       policy and permissions
  integrations/     BrainFlow and LSL acquisition with explicit decoder boundary
  memory/           episodic compatibility memory + evidence-state memory
  neuro/            quality, uncertainty, drift, fusion, ErrP, EEG loading/analysis
  replay/           JSONL decision replay
  runtime/          governed admission, reality reconciliation, Simplex, shadow control
  stress/           deterministic fault injection
  vision/           declared visual-context mapping only
  tests/            unit, integration, negative-control, format, and tamper tests
scripts/
  run_v1_validation.py
core/
  legacy compatibility imports routed to deterministic implementations
```

## CI

GitHub Actions tests Python 3.11, 3.12, and 3.13. Each matrix job installs development dependencies, runs Ruff, Pyright, pytest with coverage, and the release validator. Coverage XML and validation JSON are uploaded as workflow artifacts.

## Donor provenance

The upgrade was informed by the supplied IX, IX-IntentRealityLoop, IX-Sally, IX-Autonomy-Assurance-Case-Runtime, and IX-Operator repositories. The donor code was not blindly merged.

Licensing and import decisions are documented in `docs/DONOR_PROVENANCE.md`. In particular, source-available donors were not bulk-copied, and the evaluated IX-Operator transport path was not imported after a donor test exposed a tamper-detection failure in that evaluated environment.

## Additional documentation

- `docs/ARCHITECTURE.md`
- `docs/ARCHITECTURE_V1.md`
- `docs/BENCHMARKING.md`
- `docs/SAFETY_MODEL.md`
- `docs/EVIDENCE_AND_REPLAY.md`
- `docs/FAULT_INJECTION.md`
- `docs/CLAIM_BOUNDARIES.md`
- `docs/DONOR_PROVENANCE.md`
- `SECURITY.md`

## License

Apache License 2.0. See `LICENSE`.

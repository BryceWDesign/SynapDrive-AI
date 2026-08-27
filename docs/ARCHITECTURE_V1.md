# SynapDrive-AI v1.0 Architecture

## Design rule

Observation, inferred class, declared goal, authorized action, execution result, user feedback, and memory consequence are separate states. The repository does not silently collapse them into one concept called "intent."

## Runtime admission

`GovernedRuntime` evaluates each proposed action against:

- confidence and any stricter per-task confidence requirement;
- distribution-derived uncertainty;
- signal-quality score;
- fitted decoder-drift score when supplied;
- capability permission;
- explicit world-model feasibility;
- explicit software-policy risk.

Unknown actions are infeasible and receive maximal software risk. Unknown or analysis-only inference fails closed. Policy values are testable software thresholds, not hardware safety limits.

## Signal integrity

`SignalQualityAnalyzer` checks finite samples, flatline behavior, zero-valued dropout, observed-extrema clipping, and line-frequency power. It exposes component measurements and an aggregate engineering score.

The aggregate score is not a clinical signal-quality index.

## Spectral analysis

`BandPowerAnalyzer` calculates delta, theta, alpha, beta, and gamma power plus two ratio features. Its historical `confidence` field is an uncalibrated heuristic separation score retained for API compatibility.

`SessionAnalyzer` without a decoder is analysis-only. Band ratios cannot become movement commands. With a decoder callback, the decoder output is quality-tagged and then passed through the governed runtime.

## Decoder benchmarking

Built-in inspectable baselines are:

- `SpectralCentroidDecoder`;
- `RiemannianCentroidDecoder`, a compact log-Euclidean covariance baseline;
- `EnsembleDecoder`, which averages member probabilities.

The arena reports accuracy, balanced accuracy, multiclass Brier score, expected calibration error, abstention coverage, and selective accuracy on an explicit labeled NPZ dataset.

`QualifiedDecoderAdapter` can promote a decoder only after local held-out gates and a complete label-to-action map. Runtime shape or sampling-rate mismatch abstains.

## Uncertainty and calibration

`neuro.uncertainty` provides normalized distributions, normalized entropy, margin uncertainty, ensemble disagreement, and a histogram reliability calibrator fitted only from supplied confidence/correctness observations.

## Drift

`FeatureDriftMonitor` fits a Mahalanobis-distance baseline from supplied feature vectors. It has no baseline and no authority until fitted.

## Multimodal fusion

`WeightedEvidenceFusion` combines explicit modality probability distributions using caller-supplied reliability weights. It does not infer those reliability weights automatically.

## ErrP path

`ErrPFeatureExtractor` provides event-window features. `ErrPLDAClassifier` must be trained from supplied labeled calibration features before it can emit a probability. No pretrained participant-independent ErrP detector is bundled.

## World model and counterfactual planning

`WorldModel` predicts only explicitly registered actions. Unregistered actions fail closed. Successful modeled simulation actions commit their predicted symbolic state to the canonical world model.

`CounterfactualPlanner` ranks a caller-bounded candidate set using transparent fixed software-policy weights over intent alignment, decoder confidence, caller goal score, reversibility, and registered risk. The weights are not learned and are not presented as optimal.

`SharedAutonomyArbiter` proposes a bounded action. It does not bypass runtime admission or directly actuate.

## Runtime assurance and reversion components

`SimplexController` is an explicit two-controller utility that dispatches to an advanced controller only when a completed runtime decision is allowed; otherwise it selects the supplied reversionary controller.

`ShadowController` records an experimental policy's proposed action without granting that policy authority over the trusted action path.

The canonical pipeline itself fails closed before its simulated router and carries a `hold_position` safe-state recommendation on denied cycles.

## Reality reconciliation and memory

`RealityReconciler` compares predicted software success, execution result, and optional explicit rejection or externally supplied ErrP probability.

Aligned successful cycles can enter evidence memory as `validated`. Contradicted cycles are `quarantined`. Historical successful episodes may be attached as context, but they do not inflate decoder/parser confidence.

## Adaptation

`GuardedThresholdAdapter` evaluates a candidate confidence threshold against caller-supplied held-out records. A candidate is promoted only when its defined utility improves without increasing unsafe accepts under that supplied validation set.

It adapts one threshold only. It is not an autonomous self-modifying learning system.

## Evidence and signing

Every canonical cycle emits deterministic stable evidence content into a SHA-256 hash chain. Wall-clock timestamps are intentionally excluded from the evidence payload used for deterministic content comparison.

The evidence CLI can generate an Ed25519 keypair, sign a ledger, verify a detached signature, and verify the hash chain.

## Fail-closed defaults

`RuntimePolicy` defaults:

- minimum confidence: `0.45`;
- maximum uncertainty: `0.70`;
- minimum signal quality: `0.60`;
- maximum predicted software risk: `0.70`;
- maximum drift score: `6.0`;
- ErrP contradiction threshold: `0.70`;
- safe-state recommendation: `hold_position`.

These values are repository policy fixtures for software evaluation. They are not medical, robotic, or industrial safety limits.

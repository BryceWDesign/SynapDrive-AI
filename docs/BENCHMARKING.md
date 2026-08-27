# Decoder Benchmarking

## Explicit dataset contract

The benchmark CLI consumes an NPZ file containing:

- `X`: numeric array shaped `(epochs, channels, samples)`;
- `y`: one explicit label per epoch;
- `sampling_rate`: positive scalar;
- `channel_names`: optional one-dimensional string array.

Missing labels or sampling rate cause failure. The loader does not synthesize them.

## Create epochs from a recording and event table

`SynapDrive-AI` can prepare a benchmark NPZ from a supported recording plus an event CSV containing `onset_s,label` columns:

```text
synapdrive-prepare-dataset recording.edf events.csv --out participant_epochs.npz --tmin 0 --tmax 1
```

Use `--channel` repeatedly when a subset of channels is required. CSV/NPY recordings need the correct `--sr` value because those formats do not carry the same sampling metadata contract as EDF/BDF.

## Run the arena

```text
synapdrive-benchmark participant_epochs.npz --decoder all --seed 7 --abstain 0.60
```

Available built-in decoders are `spectral`, `riemannian`, `ensemble`, and `all`.

Metrics include:

- accuracy;
- balanced accuracy;
- multiclass Brier score;
- expected calibration error;
- coverage at the chosen abstention threshold;
- selective accuracy among accepted predictions.

The deterministic split is stratified by class. It is a repository engineering baseline, not a publication protocol. Participant-level claims require experiment-appropriate participant/session grouping, preprocessing, statistical analysis, and external replication.

## Runtime qualification

`QualifiedDecoderAdapter` is available to library users who want to connect a benchmark decoder to BrainFlow, LSL, `SessionAnalyzer`, or the canonical pipeline.

Construction performs deterministic held-out evaluation using `QualificationPolicy`. A decoder is not locally qualified unless it meets all configured metric gates and every decoder class has an explicit action mapping. A qualified adapter is then refit on the supplied dataset.

At runtime it still abstains when:

- channel count differs from the qualification dataset;
- sampling rate differs from the qualification dataset;
- the winning class has no action mapping;
- winning probability is below the abstention threshold.

Local qualification means only that the model met the configured repository gates on the supplied data. It is not proof of participant generalization, neural-intent validity, clinical performance, or safe physical control.

## Built-in decoder scope

`SpectralCentroidDecoder` uses relative FFT band-power features and class centroids.

`RiemannianCentroidDecoder` computes regularized channel covariance matrices, applies the symmetric matrix logarithm, vectorizes the upper triangle, standardizes features, and compares class centroids. It is an inspectable compact baseline, not a replacement for specialist Riemannian BCI libraries.

`EnsembleDecoder` averages member class probabilities after verifying common class ordering.

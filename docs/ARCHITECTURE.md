# Architecture

## Purpose

SynapDrive-AI is a simulation-first, evidence-producing runtime for studying how a declared or decoded action candidate moves through uncertainty, permission, prediction, execution, feedback, memory, and replay.

The canonical implementation is `synapdrive_ai/pipeline.py`. Compatibility wrappers route into that pipeline rather than maintaining parallel control loops.

## Canonical cycle

```text
input packet
  -> context enrichment without confidence inflation
  -> probability distribution and uncertainty
  -> permission + signal quality + drift + world-model risk
  -> governed pre-action decision
  -> lexical compatibility guard
  -> simulated router, only when admitted
  -> explicit world-state commit for modeled successful actions
  -> reality reconciliation
  -> validated or quarantined evidence memory
  -> assurance receipt
  -> SHA-256 linked evidence entry
```

Blocked, analysis-only, unknown, unmodeled, low-quality, high-uncertainty, excessive-drift, permission-denied, or excessive-risk inputs do not reach the simulated action router.

## Intent packet

The minimum runtime contract is:

- `intent`: proposed simulation action name;
- `confidence`: numeric value in `[0, 1]` with explicit semantics supplied by the producer;
- `source`: provenance string.

Important optional fields include:

- `probabilities`: class/action probability distribution;
- `signal_quality`: engineering quality score;
- `drift_score`: fitted feature-drift score;
- `required_confidence`: caller-requested stricter pre-action threshold;
- `analysis_only`: prevents actuation even when other gates pass;
- `inference_authority`: provenance category such as `declared-command`, `synthetic-ground-truth`, or `locally-qualified-decoder`;
- `confidence_semantics`: explanation of what the numeric confidence means;
- `neural_decode_performed`: explicit boolean provenance flag.

## Acquisition is not decoding

`BrainFlowIntentSource` and `LSLIntentSource` acquire samples and compute signal-quality metadata. They do not infer intent from RMS amplitude or another hidden heuristic.

Without an explicitly supplied decoder callback, both adapters emit an analysis-only abstention. A decoder callback must return a packet that still passes the canonical governed runtime.

## Qualified decoder bridge

`QualifiedDecoderAdapter` is the concrete bridge from the built-in decoder benchmark surface to runtime use. It requires:

1. deterministic held-out evaluation;
2. local metric gates;
3. a complete explicit decoder-label to simulation-action map;
4. exact runtime channel-count agreement;
5. exact runtime sampling-rate agreement;
6. confidence above the configured abstention threshold.

Failure at any point yields an abstention. Passing these local software gates is not clinical, participant, or physical-system validation.

## Evidence

Every canonical cycle produces an assurance receipt and an entry in a SHA-256 linked evidence chain. Exported ledgers can also be signed with Ed25519.

The chain and signature establish integrity properties of recorded bytes. They do not prove that sensor measurements, decoder interpretations, or scientific claims are true.

## Compatibility namespaces

The historical `synapdrive_ai.agi` package name remains for import compatibility. Canonical v1 code does not claim AGI. Its retained classes are deterministic mappers, context handling, compatibility diagnostics, and disabled legacy adaptation surfaces.

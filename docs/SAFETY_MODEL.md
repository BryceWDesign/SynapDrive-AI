# Safety Model

## Scope

The safety model governs software simulation only. It does not certify physical machinery, a medical device, a BCI decoder, or a human participant protocol.

## Primary rule

A proposed action must satisfy every active pre-action gate before the simulated action router is reachable.

The canonical runtime blocks on:

- `analysis_only` inference;
- unknown intent/action;
- confidence below the repository policy or a stricter task requirement;
- uncertainty above policy;
- signal quality below policy;
- predicted software risk above policy;
- decoder drift above policy;
- permission denial;
- unmodeled action or failed world-model precondition.

The historical `SafetyGuard` remains as a compatibility lexical guard for a small prohibited phrase set and a minimum confidence check. It is not the primary assurance model and is not represented as an ethical reasoning system.

## Safe-state behavior

Denied cycles do not reach the simulated action router. They carry the policy's `hold_position` safe-state recommendation in the result contract.

`SimplexController` is separately available when an integration needs to select between an advanced and a caller-supplied reversionary controller after a runtime decision.

## Permissions

`PermissionGate` supports allow and deny glob patterns plus full non-safe capability revocation. Halt/stop/hold safe-state actions remain permitted after revocation.

## World-model boundary

Only explicitly registered actions are considered feasible. Unknown actions preserve state, are marked infeasible, and receive maximal software risk. Successful modeled simulation actions commit the explicit predicted state.

Registered risk numbers are test policy fixtures. They are not empirical accident probabilities.

## Neural-input boundary

Hardware acquisition by itself has no action authority. BrainFlow and LSL without a decoder return an analysis-only abstention.

Offline spectral band analysis without a decoder also remains analysis-only. RMS amplitude and spectral-band ratios are not converted into neural movement commands.

## Evidence invariants

For every canonical cycle, assurance verifies internal properties such as:

- a denied cycle did not reach simulated actuation;
- an allowed cycle reached the simulated router;
- result status agrees with the recorded admission path;
- required intent/confidence fields remain reviewable.

A SHA-256 evidence chain detects modification of recorded cycle content. Ed25519 can authenticate an exported ledger against possession of a signing key.

Neither mechanism validates the truth of the underlying scientific interpretation.

## Threats exercised by the repository

Tests and the stress harness cover defined cases including flatline/dropout, clipping/noise, analysis-only inference, uncertainty, drift, permission revocation, unmodeled actions, decoder sampling mismatch, evidence tampering, contradictory feedback, and task-level pre-action confidence failure.

The set is intentionally extensible and is not claimed to be exhaustive.

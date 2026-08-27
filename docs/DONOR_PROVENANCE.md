# Donor Repository Provenance

The v1 upgrade was informed by the donor repositories supplied for the upgrade. The implementation deliberately avoids a blind repository merge.

## IX-IntentRealityLoop

Useful architectural ideas included separation of intent, permission, bounded action, feedback, outcome delta, memory consequence, and replay evidence.

Its supplied license is source-available rather than permissive. SynapDrive v1 therefore does not bulk-copy its source. The corresponding SynapDrive mechanisms are clean implementations inside this repository.

## IX-Sally

Useful architectural ideas included explicit world state, planning, uncertainty, memory governance, and proposal/review separation.

Its supplied license is also source-available. SynapDrive v1 does not bulk-copy its source. The world model, counterfactual planner, shared-autonomy arbiter, guarded adaptation, and evidence-memory code in this repo are local implementations.

## IX-Autonomy-Assurance-Case-Runtime

The donor is Apache-2.0 licensed. Its strongest contribution to the upgrade direction was evidence-first runtime assurance, provenance, negative controls, and fail-closed evaluation. SynapDrive retains its own compact assurance data model rather than importing the donor package as a runtime dependency.

## IX

The donor is MIT licensed. Its contract-oriented design informed the decision to keep policy rules explicit and machine-readable. SynapDrive uses typed policy objects and JSON loading rather than embedding a separate language runtime into the control loop.

## IX-Operator

The donor was not imported into SynapDrive's transport path. During donor inspection, its test surface exposed a tamper-detection failure in the evaluated environment. SynapDrive v1 therefore implements evidence signing independently with the maintained `cryptography` Ed25519 primitive and keeps networking/transport outside this upgrade.

## General rule

A donor name is not treated as evidence. SynapDrive v1 only claims mechanisms that exist in its own executable source and tests.

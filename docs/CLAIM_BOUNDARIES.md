# Claim Boundaries

SynapDrive-AI is a research software repository. The following boundaries are part of the design and should remain visible in publications, repository descriptions, demonstrations, and derived artifacts.

## What executable tests can establish

The test suite can establish software properties such as deterministic calculations, expected policy decisions, explicit permission denial, hash-chain integrity checks, correct quarantine behavior, dataset-contract enforcement, decoder metric calculation, and fail-closed behavior under defined injected faults.

These are software claims only.

## What the repository does not establish

The repository does not establish any of the following:

* that a decoded class equals a person's true intent;
* clinical sensitivity or specificity;
* medical-device safety or effectiveness;
* reliable real-time BCI control in humans;
* safe physical actuation;
* generalization to an untested participant, session, device, or environment;
* validated ErrP detection without labeled participant calibration;
* calibrated confidence before calibration is performed;
* accurate physical predictions for actions absent a validated plant/world model;
* cybersecurity certification;
* autonomous authority to act without a human-defined permission model;
* AGI, consciousness, sentience, or general intelligence.

## Synthetic verification data

Tests and `scripts/run_v1_validation.py` generate deterministic signals in order to verify software paths. Those signals are labeled as synthetic verification data. Their benchmark accuracy must never be cited as human EEG performance.

## Real-data use

The benchmark runtime accepts explicitly labeled epoch arrays. Scientific conclusions from a dataset remain the responsibility of the experiment design, dataset license, preprocessing choices, split design, participant/session grouping, statistical analysis, and external replication.

## Physical control

The built-in actuation layer is simulated. Any hardware integration requires an independently designed and validated safety architecture appropriate to the hardware, environment, user population, and applicable regulation.

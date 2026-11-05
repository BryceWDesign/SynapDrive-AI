> Historical pre-implementation design snapshot. Its planned/not-run statements
> describe the earlier package. See [implemented v2 scope](../../V2_IMPLEMENTED.md)
> and [current requirement status](../../REQUIREMENT_STATUS.json) for this release.

# Proposed validation and release protocol

**All v2 runtime acceptance cases and experiments are planned, not executed.** Design-consistency and bounded-reference-model results have their own evidence category. This prevents specification checks from being counted as completed decoding, control or participant validation.

## 1. Evidence levels

| Level | Can establish | Cannot establish by itself |
| --- | --- | --- |
| Source review | A published finding and its stated scope | A result of SynapDrive or a universal user need |
| Design model | Properties of a bounded abstract transition model under explicit assumptions | Correct future code, hardware, physiology or scheduler behavior |
| Software | Defined schema, control-flow, integrity and recovery behavior | Human decoding validity, actual task benefit or physical safety |
| Offline data | Performance on correctly labeled, partitioned recorded data | Human closed-loop adaptation, naturalistic intent or home usefulness |
| Simulation | Behavior in a declared environment/user/plant model | Actual motor/clinical efficacy or all physical disturbances |
| Hardware | Measured behavior of named devices under defined conditions | Benefit across people or settings not evaluated |
| Human study | Outcomes in the enrolled cohort and protocol | Universal acceptance, efficacy or long-term adoption |
| Deployment | Sustained behavior in the observed setting | Unlimited continuation or generalization beyond the evidence |

Every result records data source, population, modality, task, environment, split, artifact, protocol, exclusions, endpoints and uncertainty. A result cannot be silently relabeled to a stronger evidence level. The model checker delivered in this package has `design_model` scope; original runtime test results remain baseline software evidence.

## 2. Establish application limits before locking evaluation

The plan does not invent universal release thresholds. `profiles.json` contains six unresolved parameter groups: risk/coverage/usefulness; clock/freshness/stop deadlines; adaptation precision and promotion; accessible controls/burden; hardware resource budgets; and physical recovery assumptions. Resolve the relevant groups before a profile's locked evaluation. Record a rationale and a version. Choosing thresholds after examining the final test set invalidates an unbiased result.

An unresolved physical parameter does not prevent a software-only research experiment. It does prevent qualification of the corresponding physical action profile. A successful design validation does not fill any unresolved value.

Critical software invariants can be exact for the defined tests: no ordinary dispatch after invalid input, no stale/mismatched permit consumption, no forbidden output while locked, and no dependent step after a failed prerequisite. Test exhaustion in a bounded model is not a universal proof over arbitrary implementation states.

## 3. Real-data decoder protocol

### Initial dataset suite

Use a deliberately small suite with distinct purposes:

1. OpenBMI/Lee2019_MI for compatible within-person cross-session motor-imagery evaluation through a pinned MOABB adapter.
2. BNCI2014_001 for a complementary multi-class motor-imagery evaluation through its documented adapter.
3. PhysioNet movement/imagery for explicit supported rest/imagery analyses and run-aware event interpretation [S23].

Dataset inclusion is a plan, not a claim that these data have been downloaded or evaluated here. Check current access, attribution, redistribution and permitted use before implementation. Do not distribute data or third-party weights in a release merely because the project is Apache-2.0.

Scalp EEG, implanted recordings, EMG, gaze and declared inputs use separate decoder artifacts and result strata. Existing intracortical results motivate lifecycle requirements, not a promised scalp-EEG capability. Healthy-cohort evidence must not be presented as impaired-cohort efficacy.

### Split and processing discipline

Define participant, session, run, trial and parent-recording identity before epoching. Prevent overlapping or byte/near-duplicate windows crossing the protected boundary. Fit learned filtering/spatial transforms, scaling, covariance adaptation, calibration, class maps and decoders only on permitted partitions. Fixed processing choices and their tuning history are disclosed as well.

Choose explicit protocols: within-session, held-out session, held-out subject, and few-shot target calibration. State whether target-session unlabeled data is allowed. Unsupervised target access is not zero target access. Preserve index/hash manifests and exact versions. MOABB provides the protocol foundation [S19], but custom integration still needs leakage checks.

Keep model selection, calibration and final evaluation distinct. If a deployment refit changes the model, validate the procedure and bind qualification to the resulting artifact. Repeated candidate selection on a final audit set turns that set into selection data; use an appropriate fresh audit or predefined sequential plan.

### Baselines and negative controls

Compare the same permitted data, target information, processing window and resource budget across existing centroids, strong spatial-filter/linear and covariance baselines, compact neural models, and selected optional advanced encoders. Do not make an intentionally weak baseline the only competitor. Foundation models and transformed-ensemble approaches need demonstrable benefit [S10, S12, S26].

Required controls include label permutation under the same grouped protocol, deliberately contaminated duplicate/overlap splits that the pipeline must reject, train-only processing, prior-only assistance when applicable, a random/no-skill policy, an always-abstain policy and a fixed sensible gate. A control failure is reported; it is not silently deleted from a leaderboard.

### No-command evaluation

Explicitly label eligible no-command periods under the source protocol. Cued rest and naturalistic private activities are not interchangeable. Report incidental activation during sensor adjustment, distractors and task transitions only when actual data for those states exist. Synthetic versions are fault scenarios, not physiological validation.

Use time-based metrics and event-level analysis. Overlapping windows share information; they cannot create thousands of independent subjects or independent chance opportunities. Sustained false output and delays in cancellation matter more than a single averaged class score.

## 4. Metrics and statistical interpretation

| Metric | Definition and reporting rule |
| --- | --- |
| Command coverage | Issued commands / eligible decision opportunities; define opportunity timing and dependence |
| Error among issued commands | Wrong issued commands / issued commands; undefined when no command is issued |
| Opportunity error | Wrong issued commands / all eligible opportunities; never substitute for conditional command error |
| Idle false activation | Unintended activation events / annotated no-command exposure time; document event grouping and zero-exposure cases |
| Useful task completion | Correct meaningful task completions / attempted tasks, including failed starts and assistance needs |
| Wrong-goal commit | Committed wrong goal/output / relevant attempted tasks or commits, with the denominator named |
| Usable access | Time during which the chosen task interface is operational and useful; record the determination and support needed |
| Setup/recovery burden | User and caregiver time, interventions, failed starts and abandoned attempts |
| Timing | Observation age, inference/gate/endpoint/veto delays and deadline misses on declared hardware; include tails and maximum observed |
| Adaptation | Risk/coverage change, labels/time required, forgetting, failed promotions, quarantines and rollback frequency |
| Agency and workload | Explicit participant measures and interviews; software override counts are proxies, not subjective agency |
| Physical simulation | Constraint violations, clearance, task progress, recovery acknowledgments and out-of-envelope exposure |
| Continuation | Actual continued use, support burden and withdrawal reasons over the observed interval |

Report intervals at the participant/session level when those are the independent units. Specify paired comparisons, sample/cluster counts, repeated measures, missingness and multiple-comparison policy. Seed variability is not participant diversity. Include individual results; a mean improvement can conceal a person whose access fails.

Conformal nominal coverage needs its assumptions and empirical behavior under shift stated [S09]. A distribution-shift detector cannot restore exchangeability by declaration. Calibration error is not a bound on accidental physical harm. Simulated policy risk values are not accident probabilities.

Zero observed failures does not prove zero risk. For independent Bernoulli opportunities a one-sided exact bound is possible, but heavily overlapping windows and long-lived failure bursts violate a naive independence interpretation. Use the model of exposure justified by the experiment rather than quoting an attractive rule-of-three bound blindly.

## 5. Independent environments and user models

### Accessible task environment

Use local simulated targets, editable drafts, correction/cancel and simulated commits. Ground truth comes from the environment's declared task or explicit user confirmation, not the controller's chosen action. A phrase bank, target selection and free-form language decoder must remain distinguishable in demonstrations and metrics.

A future participant pilot compares the person's current access method with the proposed system under comparable conditions. Include different assistance levels, target sizes/dwell settings and recovery pathways. Do not assume eye gaze, EMG, a switch, vision, hearing or an independent veto is available to every participant.

### Control environment

Implement a modest independent dynamics model with state, disturbances and actuator behavior. It must continue motion when appropriate after the controller withholds a new command. Include model mismatch, moving obstacles, sensing delay, action delay, failed stop acknowledgment and resource overload. The controller cannot supply its own ground-truth success flag.

Distinguish bounded model assumptions from outside-envelope tests. A failure outside the envelope is important evidence about limitations, but must not be used to falsely claim a proof inside the envelope was evaluated against all physical possibilities. No physical hardware is connected in initial profiles.

### Adaptation and co-adaptation

Use chronological prediction-then-label-update ordering where labels exist. Compare frozen, naive aggressive, supervised guarded, and compatible alignment/transformation candidates. Vary drift severity, update interval, feedback delay and simulated-user adaptation. Publish the simulated-user rules and include several qualitatively different models; they do not establish actual neuroplasticity or participant learning [S08].

Measured improvement must survive independent audit data, absence of pseudo-ground-truth labels, and accounting for additional abstention/recalibration time. An update that raises accuracy but repeatedly removes usable control may fail the application objective.

## 6. Combined faults and minimal reproductions

Single faults are necessary but insufficient. Use a planned interaction matrix including:

- Sensor dropout plus late stop input and a busy worker.
- Permission revocation between permit creation and dispatch, including revoke then restore.
- Channel reordering after calibration plus a high-confidence model output.
- Model update plus delayed rejection of one of its training examples.
- A fluent language suggestion plus a changed target or text revision after approval.
- Private mode plus crash/restart, audit preparation and export.
- Network disconnection plus a full queue and resumed sample stream.
- Plant-state error plus solver timeout and incomplete baseline acknowledgment.
- Frozen task prerequisite plus apparently feasible later action.
- Truncated valid evidence prefix plus missing retained checkpoint.

Expected outcomes are independent scenario requirements. Do not derive the expected response from the quality score or policy implementation being tested. Include faults a system should tolerate so blanket rejection cannot pass usefulness.

Minimize a failing run by removing events/perturbations while preserving the independent failure condition, then preserve its schema/configuration/seed and replay capsule. This is a debugging and scientific-reproduction aid, not a way to hide the larger adverse run.

## 7. Hardware and participant gates

Live acquisition begins in shadow with no external action credentials. Measure real timestamps, lost samples, metadata identity, CPU/memory limits and shutdown behavior. A software or synthetic-board smoke test is not live-device validation.

Before a participant pilot, choose the specific cohort, meaningful activities, accessible start/stop/recovery inputs, comparison method, consent/data handling and an appropriate study protocol. Co-design acceptance and confirmation burden. Request help from intended users and caregivers through an actual authorized collaboration; this package does not claim that outreach or consultation occurred.

Physical-profile work needs named hardware, dynamics, sensing/actuation bounds, baseline controller and independently assessed safety arrangements. A simulated brake is not evidence of a real wheelchair or arm's braking behavior. Do not connect clinical stimulation, implanted devices, or safety-critical machinery merely because a generic adapter compiles.

Longitudinal evaluation needs support, continuation and failure/withdrawal reporting. User preference, short task success and sustained benefit are different observations. Small studies can be valuable while their limits remain explicit [S01, S02, S05].

## 8. Release gates and claim control

The implementation must associate each normative requirement with actual evidence of the correct level, exact artifact/protocol and a result location/digest. A test file or placeholder report is not passing evidence. The current catalogs intentionally record `not_run` and no result paths.

`validate_v2_design.py` checks specification consistency. Its strict-release mode refuses this package because implementations, experiment results and threshold decisions are missing. It is a diagnostic guardrail, not a regulatory or scientific assessor. Later implementation must add the actual automated/runtime and research gates; editing JSON status fields does not perform those checks.

Keep R1 repairs independently releasable as a correctly described v1 maintenance change if desired. Do not ship a v2 capability claim merely because the design and old baseline tests are green. Any public result names the actual completed stage and its limits.


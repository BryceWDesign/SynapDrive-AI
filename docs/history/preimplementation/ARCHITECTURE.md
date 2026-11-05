> Historical pre-implementation design snapshot. Its planned/not-run statements
> describe the earlier package. See [implemented v2 scope](../../V2_IMPLEMENTED.md)
> and [current requirement status](../../REQUIREMENT_STATUS.json) for this release.

# Proposed v2 architecture

**Status: implementation specification. No planned module is claimed as implemented.**

## 1. Operational objective and invariants

Provide the greatest useful task assistance supported by the person's selected scope, available evidence, validated model/task contracts and operating constraints. Hard authorization and safety limits are not utility terms that a planner may trade away for speed. Within those limits, compare assistance strategies for task effort, success and control.

The invariants to implement are:

1. A proposal, decoded class, language completion or environmental affordance has no action authority by itself.
2. Required evidence is present, finite, mode-appropriate, identity-compatible and sufficiently fresh before ordinary dispatch.
3. A permit authorizes exactly one action instance under specified state, policy and capability versions. Expired, mismatched or consumed permits do not authorize dispatch.
4. A trusted available user veto uses the baseline path independently of the ordinary neural, planner and audit path. The interface never claims a veto channel exists when it does not.
5. Contradiction, unknown intent and unavailable knowledge remain explicit; they are not silently repaired into confidence or ground-truth labels.
6. Updates cannot inherit qualification from a different artifact or make their own validation evidence disappear.
7. Privacy and output permissions are independent. A valid prediction is not consent to record or communicate it.
8. Successful internal execution is not independent proof that the task succeeded or the person's goal was satisfied.

## 2. Separate observation, evidence, request and authority

Implement versioned immutable contracts, initially with Python frozen records or equivalently strict models. Validate before invoking legacy memory or the router. Reject unsupported fields at trust boundaries or preserve them as explicitly non-authoritative metadata. Do not use arbitrary dictionaries as authority-bearing objects.

| Contract | Required content and interpretation |
| --- | --- |
| ObservationWindow | Stream/source identity, modality, ordered channel identities, units, reference/montage, sample shape, processing identity, acquisition/sampling bounds, sample sequence, time domain, timestamps, gaps and consent mode |
| IntegrityAssessment | Per-channel finite/flat/clipped/dropout/noise findings, required-channel outcomes, permitted subset identity and timing validity; engineering measures, not diagnoses |
| DecoderArtifact | Exact artifact digest, code/processing/calibrator identities, classes and semantics, modality/task/population scope, channel/window contracts, resource needs and provenance |
| QualificationRecord | Artifact identity, immutable train/calibration/audit split IDs, protocol and target-data permissions, metrics/intervals, supported operating envelope, expiry and invalidation dependencies |
| IntentEvidence | Supported class distribution or control vector, explicit unknown/no-command support, uncertainty components, timing, artifact/qualification identity and limitations |
| UserRequest | Declared/selected goal or confirmed output, selected assistance scope, available rejection input, original content and version; kept distinct from inferred evidence |
| ActionProposal | Bounded action/parameters, target, goal relation, reversibility/consequence class and required observations; proposed by an unprivileged worker |
| ActionPermit | Nonce and exact proposal commitment, evidence/qualification references, policy/capability/user-profile epochs, state epoch, validity, endpoint identity and required baseline behavior |
| ExecutionOutcome | Prepared/sent/acknowledged/completed/failed/unknown state, endpoint observation, permitted timing and dispatch identity; a timeout has an unknown outcome until reconciled |
| FeedbackEvent | Cycle/action identity, feedback type, user/source identity where permitted, event time and semantic meaning; acceptance differs from a class label or measured task success |
| RunCapsule | Schema/environment, initial state and all retained decision dependencies, event order, artifact identities, privacy omissions, result expectations and authenticated checkpoints |

For declared text or switch input, record its actual authority and do not assign physiological quality to nonphysiological input. For EEG-derived proposals, absent quality or qualification does not become a perfect score. A generic external decoder can be used in a deliberately permissive simulation profile, but cannot claim qualified action authority through a source string.

The parser should accept an exact supported command grammar or structured action selection. Mixed commands, negation and unsupported language receive clarification or rejection. If stop is available through declared commands, its exact supported forms take precedence. This is not a general language-understanding claim.

## 3. Acquisition, timing and integrity

### Channel and processing identity

Store named ordered channels, modality, physical units, electrode/reference information and processing operations. A samplerate or channel count match is insufficient. A channel removal is supported only through a separately qualified subset artifact or a previously evaluated masking model with a defined missing-channel contract. Runtime insertion of zeros does not preserve qualification by default.

Use a tested scientific I/O backend through optional adapters for general EEG formats, while retaining minimal fixtures for isolated software tests. Preserve event metadata and run-dependent label meaning. A unified file format does not make two tasks scientifically equivalent. BIDS supports metadata discipline [S20]; maintained I/O such as MNE remains subject to correct interpretation [S22].

### Clock and age semantics

Preserve source sample timestamps, receiving time, sample index and source clock identity. Estimate offset and uncertainty where synchronization is supported. Never compare an LSL timestamp directly with a Unix epoch or an unrelated process monotonic clock [S21]. A source-clock reset creates a new clock epoch and invalidates dependent time-sensitive authority.

Use a conservative observation-age interval after mapping to the executor's clock domain. A time-sensitive profile requires the upper bound, not an attractive mean latency. If age cannot be bounded, defer that class of action. Arrival of a fresh packet does not make old samples fresh. Gaps, ordering, effective rate and target-event alignment remain visible to paradigm-specific decoders.

### Health exclusions and qualified degradation

Apply mandatory exclusions before aggregation: non-finite required values, missing required channels, invalid timing and unsupported shape/units are explicit failures. Other integrity findings use decoder/task-specific validated handling. Do not automatically veto every noisy sample, or allow every signal with a favorable weighted average. Evaluate both missed faults and unnecessary rejection.

Track channel-level dropout, saturation, flatline, mains contamination and recovery. Distinguish acquisition faults, processing mismatch and model/feature drift. The system can state evidence of a change; it cannot diagnose neurological fatigue or disease progression from an engineering anomaly score.

## 4. Decoding, calibration and temporal control intent

Separate synchronous labeled classification from asynchronous command generation. A dataset with left/right trials does not imply that every observed window is a left/right command. Model no-command and unavailable/ambiguous evidence explicitly. Do not fabricate a rest class from arbitrary unannotated data.

A temporal belief layer can accumulate evidence under a declared dependence model, with engagement and confirmation states. Repeated overlapping windows must not be treated as independent votes. Report the latency cost of accumulation, persistent false activations and sensitivity to goal changes. A trusted veto bypasses the temporal accumulator.

For a separately supported SSVER paradigm, a follow-on experiment can compare periodic-only with periodic/aperiodic state evidence motivated by the September 2026 in-press work [S27]. It requires compatible labeled data and protocol-specific validation. It is not an implemented decoder, a motor-imagery transfer result, or a reason to introduce unqualified stimulation.

Evaluate, rather than assume, the following decoder families:

- Established spatial-filter/regularized linear baselines for compatible motor-imagery tasks.
- Specialist covariance classifiers and calibration [S24].
- Compact neural baselines using the same permitted data and processing.
- A limited set of licensed, inspectable foundation encoders after baseline comparison [S10, S26].
- Forward-pass transformed ensembles/source-trained reliability ranking as an optional resource-aware experiment [S12].

The existing centroid decoders remain inspectable baselines and software fixtures. They do not establish a new high-performance universal decoder. Optional speech, P300, SSVEP, EMG or intracortical adapters require their own task, timing, labels and qualification. Do not present imagined movement classification as arbitrary word decoding.

Qualification identifies the exact deployed artifact and supported procedure. Refit after evaluation is a change in artifact; a declared, independently evaluated refit protocol is required before carrying qualification forward. Calibration data must be distinct from locked evaluation. Target-session unsupervised access, labeled few-shot access and zero-shot transfer are different protocols.

Selective prediction needs at least separate reporting of error among issued commands and how often commands are issued. Conformal prediction is a candidate method, with assumptions and shift failure evaluated explicitly [S09]. Confidence, entropy, calibration error, preprocessing sensitivity and model disagreement are diagnostics with different meanings. They must not be collapsed into an unsupported probability of real-world safety.

## 5. Accessible interaction and calibrated assistance

### User-visible states

Keep the product language simple: checking input, ready, waiting for a choice, assistance active, confirmation needed, paused, private, recovering or input unavailable. Explain the next useful action without exposing hashes, policy rule IDs or implementation jargon in ordinary interaction. Detailed evidence remains available to researchers and support staff with appropriate permissions.

The interaction state machine includes:

| State | Entry/exit behavior |
| --- | --- |
| Locked | No ordinary external output; privacy and capture behavior are explicit; user has a configured accessible unlock path |
| Preflight | Check compatible input, processing, qualification, endpoint and baseline availability; show unsupported functions |
| Ready | Accept supported engagement/selection without presuming continuous command intent |
| Active | Use the selected assistance scope; apply profile-specific admission to every committed action |
| Clarifying | Preserve task context and ask the smallest useful accessible question; no speculative sensitive commit |
| Degraded | Identify lost evidence and available qualified alternatives; retain drafts and task state |
| Paused | Stop ordinary task progression; dependent permits invalidated; baseline control remains active where necessary |
| Recovering | Re-establish valid state and qualification; require appropriate re-engagement before resuming commitments |
| Faulted | Report unavailable capability and uncertain endpoint outcome; do not fabricate successful recovery |

States may overlap with a privacy mode, but privacy changes cannot secretly resume output or enlarge authority. On restart, ordinary control begins locked/preflight. Resuming a draft is different from resuming a physical movement.

### Assistance scope

Provide manual, assisted and bounded-task modes. The person can pre-authorize a limited task macro when useful, avoiding compulsory confirmation of every trivial action. Confirmation requirements depend on consequences and the selected scope. A caregiver may help setup within their role but cannot silently override the person's preference, expand task permissions, or export neural data.

Maintain original goal hypotheses and a checkable goal relation for each proposal. A candidate selected from a common list is not proof of goal preservation. Environmental perception may suggest feasible targets; it does not establish consent or intended choice. A goal change cancels dependent pending commits.

### Clarification and compatible progress

Compare four responses: wait for further evidence; request a clarification; propose a reversible intermediate action compatible with all retained authorized hypotheses; use baseline control. If there is no common permissible action, do not invent consensus. The candidate hypothesis set itself has limited validity; model shift may require requalification instead of action.

Prior POMDP/shared-autonomy work is acknowledged [S25]. The experimental question is whether this specific evidence/authority integration improves useful progress under matched command risk and interaction burden. No optimality or novelty is assumed.

Define the proposal set explicitly. For retained hypotheses `C`, let `A(g)` be the next actions compatible with goal `g`, `U` the currently authorized action scope, and `S(x)` the actions satisfying the current state/plant constraints. Candidate common progress is limited to:

`A_common = U intersection S(x) intersection (intersection over g in C of A(g))`.

An empty `C`, an unsupported hypothesis set, or an empty intersection does not license action. An uncertain hypothesis set can omit the true goal, so membership in this intersection is not proof of actual intent. Scope/reversibility limits and clarification are still required. Compare immediate clarification with common progress under explicit uncertainty, goal changes and misleading context. Do not convert a fixed heuristic utility into a claim of optimal behavior.

Multimodal evidence also needs a declared dependence model. Gaze, scene context and an EEG decoder may share a stimulus cue; averaging their confidence does not produce three independent confirmations. Evaluate disagreement, availability, correlation and calibration separately. Modalities that identify candidates, authorize a selection and constrain motion can play different roles instead of voting on a single supposedly certain intent.

### First application

The local research workspace contains target selection, editable drafts, corrections, back/cancel, help-request composition and a simulated external endpoint. It can use a phrase bank or letter/target selection, clearly labeled. Do not label a help-request button as a dependable emergency service. External messaging, banking, account changes and physical devices remain disabled in initial profiles.

Future external commits bind confirmation to exact output bytes/parameters, destination, revision and capability scope. Changing a suggestion after approval invalidates that approval. There is no general permission for an LLM or decoder to send arbitrary content as the person.

## 6. Action admission, execution and recovery

### Authority protocol

1. Validate observation and proposal contracts and required qualification.
2. Check task scope, current capability/policy/user-profile epochs and exact action identity.
3. Check current state epoch, evidence age and profile-specific risk/recovery constraints.
4. Prepare a durable ordinary-command record according to privacy mode, without retaining forbidden content.
5. At a declared dispatch linearization point, recheck permit identity, freshness and current versions, then atomically consume the nonce.
6. Send only through the matching endpoint and record its outcome/acknowledgment.
7. Reconcile observed effects, user feedback, pending outcomes and evidence state.

The executor must not accept an old `allowed=True` decision attached to another packet. Local locks/atomic operations or a well-defined serialized executor service enforce the boundary. Distributed systems require explicit fencing/epoch and clock semantics. A check made by a planner several milliseconds earlier is not the dispatch check.

Revocation prevents subsequent dispatch under the old authority. It cannot retroactively unsend a command that an external device has already accepted. In-flight cancellation and stop depend on the endpoint and measured baseline response. Do not claim universal exactly-once physical effects: use idempotent operation identifiers where supported and explicit reconciliation when an acknowledgment is lost.

The bounded reference model in `scripts/check_v2_admission_model.py` examines action/capability/state/expiry/single-use/durability/veto interleavings under atomic abstract dispatch. It is not proof of a future Python/Rust/C++ implementation, OS scheduler, network, decoder or actuator.

### Independent baseline control

The baseline path is operational, not a string in a result packet. It is supervised separately from experimental workers. A local cursor may stop its velocity; a moving simulated mobility platform may need bounded braking; a manipulator may need a qualified controlled stop or hold under a valid torque model. Unknown state can make a claimed safe maneuver unsupported.

The watchdog must observe end-to-end liveness and acknowledgments, not merely that the UI process is alive. Ordinary audit/storage failures block ordinary irreversible commits, but do not block an independently available emergency baseline response. Stop failures become explicit unresolved states.

### Recoverability and simulation

Define a dynamics model, estimator bounds, disturbances, obstacle behavior, actuator limits and delay bounds. The baseline controller and monitor must preserve a declared recoverable set under those assumptions. A barrier or reachable-set method is selected for the actual model; naming either method does not supply its proof.

A straight-line stopping-distance calculation may serve as a sanity check under bounded velocity, delay and deceleration. It does not cover arbitrary moving obstacles, slopes, slipping, actuator damage or manipulator dynamics. Those require the appropriate plant model and external evidence. NASA's framework motivates explicit assumptions and switching obligations [S18]; it does not certify this design.

The independent simulator generates state/outcomes and faults separately from the controller. Include continued inertial motion when commands stop, not only a logging actuator that returns success. Task progress must be measured so an always-stopped system cannot be rated a successful assistive controller.

## 7. Adaptation as an evidence-controlled lifecycle

Artifact states are baseline, candidate, shadow, qualified, promoted, expired, quarantined and rolled back. Store content-addressed artifacts and dependency versions. Promotion is an atomic change of the compatible set: decoder, processing, calibrator, action mapping and relevant profile dependencies. Rollback restores the set, not only a weights file.

Separate control timescale from candidate update/evaluation timescale. Supervised continual adaptation uses labels actually revealed under its protocol [S06]. Unsupervised alignment can change representations but cannot independently demonstrate preserved class meaning [S07]. Forward-pass transformation methods are candidates for reducing resource cost [S12]. Each approach must be compared on its supported modality/task rather than described as a universal solution.

Maintain training-sample lineage. User acceptance of an action, task success and a decoder label are different observations. An ErrP estimate is not definitive ground truth. A model's own high-confidence prediction cannot silently become a trusted semantic label. Delayed rejection marks associated samples and dependent artifacts for quarantine/requalification; trained models cannot be made to forget reliably by deleting a ledger row.

Keep candidate selection separate from a locked final audit set. Repeatedly testing candidates on the same holdout consumes that holdout for selection. Promotion needs a predefined precision/risk policy appropriate to correlated subject/session data, not only `new_unsafe_accepts <= old_unsafe_accepts` on a tiny chosen sample.

Co-adaptation experiments must include frozen and aggressive controls, multiple disclosed simulated-user models, goal/input changes and feedback delays. EMG evidence about interacting learners [S08] motivates the experiments; it does not prove EEG or clinical behavior.

## 8. Privacy, authorship and hostile proposals

### Privacy modes

| Mode | Behavior |
| --- | --- |
| Locked | Ordinary output blocked; capture and processing are disabled where the system can control them or their remaining scope is explicitly disclosed |
| Private | Content/neural features are not retained by the configured application path; minimal operational metadata and any exceptions are disclosed |
| Local audited | Permitted sensitive records are encrypted separately from minimal operational commitments with explicit retention/access controls |
| Research export | Separate explicit permission for selected data, purpose, destination and scope; not inherited from ordinary control consent |

Processing, recording, output, model training and export permissions are independent. A privacy icon cannot imply upstream hardware or external systems have stopped recording. Test logs, IPC, crash behavior and exports within the declared process/OS boundary. Do not promise to erase external backups or defend a privileged compromised host through application logic.

Sensitive content should not appear in generic receipts. Store an opaque encrypted-content reference or keyed commitment when appropriate. Unsalted hashes of short predictable phrases are guessable and not anonymization. Key management and authorized deletion must state their actual scope.

Private-mode omissions constrain replay: a metadata trace can verify some authority transitions but cannot recreate unrecorded content or raw neural evidence. A minimal ordinary dispatch commitment can be durable without retaining text. The artifact must say what remains unverifiable; privacy and maximal replay cannot both be asserted without qualification.

### Communication authorship

Keep decoder-supported alternatives, machine-generated suggestions, edits and authorized final output distinct. Where neural and language-prior logits exist, test neural-only and prior-only controls and label computational attribution as such. It does not reveal a person's true meaning [S16]. Record unavailable attribution as unknown.

The implanted inner-speech study [S15] motivates intentional engagement and output lock. It does not establish scalp EEG mind reading. This design does not add private-thought inference or infer consent from a supposedly detected internal phrase. Any future keyword engagement decoder needs separate false-activation and accessibility evidence.

### Worker and data trust

Experimental model/planner/LLM workers propose through bounded typed IPC with timeouts and resource budgets. They do not receive executor credentials. Their source text, model-generated instructions and scene labels cannot modify policy, consent or capabilities. A Python callback in the same process is trusted code, not an isolated shadow sandbox.

Enforced untrusted-worker operation needs a specified OS isolation policy. If it cannot be enforced, label that worker trusted or keep it unavailable. Integrity signatures authenticate recorded bytes/key possession; they do not authenticate sensor truth, generalization or benign behavior. Defensive perturbation experiments [S17] are reported separately from transport, credential and privileged-host threats.

## 9. Evidence, dependent invalidation and lifecycle continuity

Retain policy/capability changes, model/processing identities, initial state, event ordering, feedback, permitted observations, numerical environment and expected outcomes in a versioned run capsule. Capture source and receipt timing without substituting wall-clock time for latency. Independent replay compares decisions, consequences and expected failures; numerical tolerances and platform support are stated.

A dependency graph links qualification to data splits, processing, model/calibrator, acquisition contract, action map, task domain and user/operating profile. A changed dependency invalidates only the authority that actually depends on it; avoid a global reset that unnecessarily destroys usable access. The graph is an engineering artifact, not a claim to identify every biological cause of drift.

Evidence states include proposed, prepared, dispatched, observed, user-confirmed, contradicted, failed and unknown. The old term `validated` is retained only with an explicit validation meaning. A successful mock actuator cannot turn inferred intent into confirmed meaning.

Authenticated run checkpoints include expected run ID, count and final commitment. Hash-chain consistency alone accepts a valid truncated prefix; completeness requires an external expected reference. A long-lived audit key, retention strategy and migration process need a supported owner and policy. A repository cannot guarantee perpetual support by declaration.

Bound memory and queues. Cancel or expire work under overload rather than draining old motion commands on reconnect. Preserve accessible drafts and local fallback operation when optional services disappear. Model registry assets include versions, licenses, compatibility and withdrawal behavior. Unsupported assets become visibly unavailable; a signed obsolete model is not automatically qualified.

## 10. Language and implementation choices

Keep Python for scientific orchestration, data adapters, research decoders, evaluation and simulation. Retain a small independently testable executor interface. Profile before adding a narrow Rust or C++ service for isolation, deployment or timing requirements. Do not rewrite every module simply to appear more advanced.

Optional model and I/O dependencies remain outside the small core. Dependency pins, artifacts and model licenses must be recorded before reproducibility claims. Operating-system hard real-time behavior, worst-case latency and actuator safety are measured properties of a target integration, not consequences of a chosen language.

The implementation sequence and exact planned file destinations are in `IMPLEMENTATION.md`. Requirements and acceptance-case IDs are normative. This prose explains the rationale; green design-document checks do not satisfy runtime acceptance cases.


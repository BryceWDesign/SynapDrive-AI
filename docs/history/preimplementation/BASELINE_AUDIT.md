> Historical pre-implementation design snapshot. Its planned/not-run statements
> describe the earlier package. See [implemented v2 scope](../../V2_IMPLEMENTED.md)
> and [current requirement status](../../REQUIREMENT_STATUS.json) for this release.

# SynapDrive-AI: source audit and evolution blueprint

**Audit date: 2 November 2026**

**Scope:** the original `SynapDrive-AI-main(20261102-184221).zip`, identifying itself as v1.0.0. Findings concern this archive, not an unseen current GitHub branch. All executed control probes used the simulated actuator. No human EEG dataset, human participant, physical actuator, or clinical protocol was evaluated in this audit. The future architecture below is a proposal, not a description of delivered functionality.

## Decision

The repository About text is broadly accurate as an inventory of implemented research components. It does not establish that the repository already fulfills the practical needs of a dependable neuroadaptive assistive system. Its strongest asset is the separation of acquisition, inference, permission, action admission, outcomes, and evidence. Its present weakness is that several of those boundaries are conventions or caller-supplied fields rather than consistently enforced contracts.

There is enough executable substance to justify further development. There are also reproduced failures that prevent treating the existing green checks as comprehensive assurance. The recommended direction is a research platform that measures when assistive autonomy should act, clarify, defer, or transfer control while preserving the user's authority. It should combine real-data evaluation, bounded adaptation, a dynamics-aware simulation, and independently enforced action admission.

Novelty and comparative performance remain unestablished. The proposed contribution is a reproducible integration with independently testable failure evidence. Individual ingredients such as conformal prediction, shared autonomy, Simplex, and EEG adaptation already have substantial prior work.

## 1. What was independently verified

The audit reviewed the canonical pipeline and supporting acquisition, neuroanalysis, decoder qualification, uncertainty, drift, fusion, planning, governance, adaptation, assurance, replay, fault injection, and test code. It also inspected release metadata, packaging, CI configuration, and compatibility surfaces. Additional diagnostic probes were written outside the repository. The original archive was unchanged during the audit. Editorial revisions leave diagnostic results unchanged; one local installation path is redacted.

| Check | Result in this audit | Meaning and limit |
| --- | --- | --- |
| Python | 3.12.14, Linux | One local environment; not the entire GitHub matrix |
| Existing pytest suite | 138 passed | Existing tests pass, including tests with mocked acquisition dependencies |
| Release validator | 24/24 passed | Uses explicitly synthetic software verification fixtures |
| Ruff | Passed | Repository's configured lint rules |
| Pyright | 0 errors, 0 warnings | Repository's configured type analysis |
| Combined statement/branch coverage | 69.7011% | Coverage.py aggregate, not pure branch coverage |
| Statement coverage | 72.3598% | 2,220 of 3,068 statements |
| Branch coverage | 56.3725% | 345 of 612 branches |
| Canonical pipeline combined coverage | 97.2222% | High coverage did not prevent the failures below |
| Wheel build | Passed | Setuptools emitted a template-package configuration warning; template was included |
| Installed-wheel import smoke | 95 discovered modules, zero import failures across `synapdrive_ai` and `core` | Importability does not establish that every class method works |
| Installed-wheel behavior | Declared command succeeded; dashboard home returned 200 | Executed from the wheel target outside the source directory |
| Original release manifest | 143 of 144 listed hashes matched | `RELEASE_VALIDATION.json` differs from its recorded hash inside the original ZIP |
| Remote GitHub Actions | Not checked | Local success cannot establish current remote CI status |

The coverage distinction matters: the historical audit describes approximately 69.7% as branch coverage. The current measurement separates the 69.7% combined figure from actual 56.4% branch coverage.

Archive SHA-256: `6d2c0c2cea909df20a410f2b996085f5b43794ba934b59a8377ebc1e8d8b64e6`.

The manifest mismatch was checked directly against the uploaded ZIP after being noticed in the extracted tree. It therefore predates this audit. It could reflect a stale manifest; it is not evidence, by itself, of malicious tampering.

## 2. Assessment of the About text

The supplied description is 335 characters:

> Simulation first governed neuroadaptive runtime for BCI inspired intent to action systems: uncertainty aware abstention, signal quality and drift detection, locally qualified decoders, shared autonomy, symbolic world modeling, Simplex fallback, evidence gated adaptation, signed replayable assurance, and deterministic fault injection.

| Phrase | What exists | Necessary qualification |
| --- | --- | --- |
| Simulation first | A simulated actuator that logs admitted actions | It does not simulate physical plant dynamics or demonstrate physical control |
| Governed runtime | Pre-action confidence, uncertainty, quality, permission, drift, feasibility, and risk checks | Malformed and inconsistent inputs can defeat the intended semantics; provenance is not independently authenticated |
| BCI inspired intent to action | Acquisition adapters, analysis, labeled decoder interfaces, explicit action mapping | Default text and synthetic paths do not infer intent from physiology |
| Uncertainty aware abstention | Entropy, margin, ensemble disagreement, and threshold checks | The combined score uses fixed weights; caller uncertainty can override derived uncertainty |
| Signal quality and drift detection | Concrete quality measurements and a fitted Mahalanobis monitor | Some severe quality faults still pass; drift must be fitted and supplied by an integration |
| Locally qualified decoders | Held-out evaluation, metric gates, channel-count and sampling-rate checks | Trial-level random splitting, no participant/session isolation, no channel-order or units enforcement, and a full-data refit after qualification |
| Shared autonomy | Bounded action ranking and a proposal API | Caller-supplied candidate alignment and fixed utility weights; no demonstrated closed-loop assistance benefit |
| Symbolic world modeling | Registered action preconditions/effects and state commits | Default actions mostly change `last_action`; risk values are declared fixtures, not measured accident probabilities |
| Simplex fallback | A two-callback dispatch utility | Separate from canonical denied-cycle execution; no validated recoverable region or timing guarantee |
| Evidence gated adaptation | Held-out utility comparison for a confidence threshold | One threshold, caller-supplied labels, no general decoder-update lifecycle or statistical promotion guarantee |
| Signed replayable assurance | Hash-linked evidence, Ed25519 export signing, input replay | Signing and replay are separate; replay omits feedback and does not capture all decision state |
| Deterministic fault injection | Seeded noise, dropout, clipping, line-noise, and channel-swap injectors | The default campaign checks quality-threshold consistency, not independent fault detection or task safety |

**Verdict:** retain the research and simulation framing. Treat “neuroadaptive,” “Simplex fallback,” and “signed replayable assurance” as bounded component descriptions. They should not imply an integrated, experimentally validated assistive control stack.

A clearer alternative for the current version, 293 characters:

> Simulation-first research runtime for BCI-inspired shared autonomy. Gates simulated actions using uncertainty, signal quality, permissions, and symbolic world models. Includes EEG decoder benchmarks, drift monitoring, bounded adaptation, signed evidence, replay, and deterministic fault tests.

## 3. Reproduced findings and their implications

Priority here means importance for the proposed assistive-control architecture. It is not a CVSS score or a claim of remote exploitability. Several probes deliberately call trusted Python APIs with malformed values. The current package does not establish a security boundary against arbitrary code in its own process.

### F01. Numeric inputs do not consistently fail closed

**Source:** `runtime/governed_runtime.py:25`, `neuro/uncertainty.py:36`, `pipeline.py:136`, `assurance/contracts.py:16`.

With an otherwise valid declared-command packet, `predicted_risk=float('nan')` produced a successful simulated action and a passing assurance receipt. NaN quality and drift also allowed execution. NaN confidence produced an action followed by a failed assurance receipt, meaning the fault was noticed after the execution path.

Python comparisons and `min`/`max` clipping do not provide finite-number validation. NaN can evade a greater-than check or be transformed to a favorable endpoint depending on argument order.

**Required change:** validate finite numeric values, ranges, and types before any world-state change or actuation. Reject booleans masquerading as numeric measurements where inappropriate. Use strict JSON serialization that rejects NaN and infinity. Preserve explicit invalid-input evidence rather than silently repairing scientific measurements.

### F02. A malformed packet can act before crashing and produce no cycle evidence

**Source:** `pipeline.py:192`, `pipeline.py:210`, `memory/episodic_memory.py:10`.

`{'intent':'move_left','confidence':0.99}` reached the simulated actuator, then raised `KeyError('source')` while recording legacy memory. The action log contained one action; the evidence chain contained zero entries.

**Required change:** a validated input schema, a pre-dispatch durable admission record, explicit outcome/error handling, and recovery semantics for an interrupted cycle. Normal actuation should not proceed when its required audit contract cannot be established. An independent emergency-stop path must not wait for disk or ledger availability.

### F03. Decoded distribution, claimed action, and uncertainty can disagree

**Source:** `pipeline.py:136-145`, `runtime/governed_runtime.py:32-35`.

A packet asking for `move_left` with all probability mass on `move_right` executed left and received passing assurance. A 50/50 distribution blocked under derived uncertainty but executed when the same packet supplied `uncertainty=0.0`.

**Required change:** define distinct types for raw decoder evidence, independently computed uncertainty, and the authorized action proposal. An action intentionally differing from a decoder label must carry an explicit, evaluated shared-autonomy transformation. Do not let an untrusted packet lower its own uncertainty gate. Accepting an externally computed uncertainty estimate requires a validated estimator contract and provenance, not merely a field name.

### F04. Fault flags and quality admission disagree

**Source:** `neuro/signal_quality.py:62-124`, `runtime/governed_runtime.py:36,51`.

| Diagnostic signal | Quality score | Reported issues | Simulated runtime using that score |
| --- | --- | --- | --- |
| Constant nonzero array | 0.650000 | Flatline, clipping | Accepted |
| Pure 60 Hz sine at 256 Hz | 0.908333 | Line noise | Accepted |
| Approximately 20% NaN samples | 0.802930 | Non-finite samples, dropout | Accepted |
| Eight channels, one constant | 0.788997 | Clipping | Accepted |

These probes combine the actual quality analyzer with a declared high-confidence packet to isolate the quality gate. They do not claim that every bundled decoder would emit a high-confidence action on those signals. They establish that the quality gate itself does not require rejecting these conditions.

**Required change:** task-specific mandatory exclusions, channel-level health, minimum usable-channel rules, explicit missing-data policy, and evidence of detector sensitivity/specificity. A score can summarize acceptable variation; it should not average away a required sensor's failure. Line noise, clipping, and other faults need empirically justified thresholds and treatment appropriate to the decoder.

### F05. The stress oracle cannot establish fault-detection adequacy

**Source:** `stress/campaign.py:49-59`, `stress/cli.py:46-50`.

Expected blocking is derived from the quality score itself, and the default callback forwards that score into the runtime. A campaign containing the nonzero flatline and pure line-noise signals returned two invariant passes while blocking neither signal. This correctly checks the declared threshold rule, but cannot demonstrate that the rule recognizes all consequential sensor faults.

**Required change:** independent fault metadata and scenario requirements. Measure whether the system detects or tolerates each injected fault, whether it selects the required response, and what happens to task outcomes. Include faults that should be tolerated so an always-abstain controller cannot win.

### F06. Provenance is recorded, not independently enforced

**Source:** `runtime/governed_runtime.py:25-60`, `pipeline.py:258-269`.

A packet with only action, confidence, and a source string executed successfully without local decoder qualification or acquisition evidence. Missing quality defaults to 1.0 and missing drift defaults to 0.0. The `inference_authority` label is recorded but is not an authenticated authorization check.

This can be acceptable for a trusted, deliberately injectable simulation API. It is insufficient if downstream integrations assume the runtime independently establishes decoder qualification or fresh sensor provenance.

**Required change:** separate simulation/declared-command capabilities from acquisition/decoder capabilities; bind authority to validated configuration and credentials where needed. Required evidence should depend on the input mode. A declared stop command should not require an EEG quality report; an EEG-derived movement should not silently inherit perfect quality.

### F07. Stop and negation handling are too weak for an assistive command interface

**Source:** `intent/intent_parser.py:32-52`, `governance/permission.py:41-44`, `runtime/governed_runtime.py:43-60`.

Both `do not move left` and `stop move left` parsed as `move_left` with confidence 1.0 and executed. The parser searches for a movement phrase before checking stop and does not reject negation or conflicting commands.

A separate probe supplied a stop packet with quality 0.0. The runtime blocked it, returned `hold_position` as a recommendation, and made no actuator call. This does not prove a physical hazard because this actuator is simulated. It does show that permission-level stop preservation is not an independent operational stop guarantee.

**Required change:** an exact declared-command grammar or structured command API; reject conflicting and negated motion phrases; independent, authenticated stop/veto handling. The correct fallback must depend on the simulated or physical plant state. Merely withholding the next command does not establish that a moving plant has stopped.

### F08. Permission revocation has an unsafe extension edge case

**Source:** `governance/permission.py:41-48`.

After explicitly registering the custom simulation action `stop_disable_brakes`, revoking non-safe capabilities still permitted it because its name contains `stop`. The canonical pipeline accepted it under a low declared symbolic risk. The default world model does not register this action, so registration is part of the probe's precondition.

**Required change:** exact safe-action identifiers and immutable capability definitions. Substrings should not confer safety authority. Extension authors need executable action contracts, not naming conventions.

### F09. Replay does not preserve rejection feedback

**Source:** `replay/recording.py:54-85`, `main/cli.py:128-140`.

A successful simulated action with explicit rejected feedback entered quarantined memory. Recording its packet and replaying it without separately re-supplying that feedback produced validated memory and a different evidence hash. The record schema has no feedback field. The CLI also reconstructs a default pipeline rather than restoring complete policy, permission, world-model, or adaptation state.

**Required change:** a versioned run capsule containing all decision-relevant inputs, feedback events, policy/configuration, model and preprocessing digests, initial state, state transitions, and environment information. Replay must compare expected outputs and exit unsuccessfully on unexplained divergence. Signing a ledger does not make a separate incomplete replay record complete.

### F10. Decoder qualification lacks important identity and evaluation boundaries

**Source:** `benchmarking/dataset.py:10-26`, `benchmarking/evaluation.py:31-50`, `benchmarking/runtime_adapter.py:82-91,113-133`.

The dataset contract has no participant, session, run, or trial-group fields. Qualification randomly splits trials within each class, then refits on all supplied data. This establishes a local trial split result for the pre-refit model, not independent validation of the final refit model or cross-session/person performance.

A negative-control fixture with repeated windows put all eight test windows in the training set as byte-identical duplicates. This is a demonstrated vulnerability of the split design, not evidence that a particular real dataset in this repository leaked. No human dataset is bundled in the evaluated release evidence.

A qualified synthetic decoder also returned an action when metadata declared reversed channel names and incorrect units, because runtime checks use channel count and sampling rate only. Epoch length, montage/reference, preprocessing identity, and source-device identity are not part of the qualification contract. The single-channel session-analysis bridge further limits ordinary multichannel use.

**Required change:** immutable data provenance; participant/session/run grouping; overlap and duplicate checks; independent calibration and locked evaluation sets; complete acquisition/preprocessing contracts; and a manifest binding qualification to the exact deployed artifact. If refitting changes the artifact, define and validate that procedure explicitly.

### F11. Simplex is dispatch logic, not a demonstrated safety architecture

**Source:** `runtime/simplex.py:26-29`, `pipeline.py:148-190`.

An allowed decision assessed for one action can be supplied alongside a different packet; `SimplexController` invokes the advanced callback on that unassessed packet. The utility does not check decision-action identity, expiry, current world state, or permission changes. Canonical denied cycles return a fallback recommendation without invoking this separate utility.

**Required change:** bind admission to an immutable action and current state/version, then enforce that binding at the executor boundary. Define and test a baseline controller, its operating assumptions, recoverable states, switching conditions, and worst-case response timing. Formal Simplex research makes these distinctions explicit [R7].

### F12. A frozen sequential plan can still execute later steps

**Source:** `neuro/task_planner.py:102-125`.

A plan with an unsupported prerequisite configured to freeze produced step statuses `deferred`, then `success`. The overall outcome was `frozen`, yet the later movement step reached the actuator.

The current planner has no dependency graph, so the probe does not establish that every later step is unsafe. It establishes that “freeze” is a per-step deferral rather than suspension of the remaining sequence. That is inadequate for a dependency-sensitive task such as reach, grasp, then lift.

**Required change:** explicit prerequisite/outcome dependencies and a distinction between defer-one-independent-step, pause-plan, and abort-plan. Failed prerequisites must invalidate dependent admissions.

### F13. Invalid session step can cause a non-advancing loop

**Source:** `neuro/session_analyzer.py:134-145,152-184`.

`step_s=0` is accepted, becomes zero samples, and repeatedly evaluates the same window. A bounded probe interrupted after six calls; it did not leave an unbounded process running. Very small positive steps that truncate to zero have the same structural problem.

**Required change:** validate finite positive durations and require the resulting step sample count to be at least one. Specify an explicit policy for negative times, inconsistent recordings, and out-of-range metadata.

### F14. Some assurance labels are weaker than their ordinary interpretation

**Source:** `cognition/shared_autonomy.py:39-45`, `runtime/reality.py:18-53`, `assurance/hashchain.py:45-64`.

`preserved_user_goal=True` can be returned even when the supplied goal evaluator gives every candidate zero. The code documents that it means selection from a common bounded candidate set, which is weaker than verifying that a user's goal is preserved.

Likewise, simulated execution without rejection feedback can become “validated” memory based on internal outcome consistency. This is not independent confirmation of intended meaning or a measured physical result.

Hash-chain verification accepts a valid prefix and the empty chain. That is normal for a chain verifier without an external expected head/count. Whole-file Ed25519 signing can detect changes against a retained original signature, but chain verification alone cannot establish completeness or freshness.

**Required change:** precise labels; explicit unconfirmed outcomes; later-feedback reconciliation by cycle ID; retained signed checkpoints or manifests specifying run identity, count, and final hash. Do not describe cryptographic integrity as scientific validity.

### Additional observations

- The historical `agi/intent_classifier.py` has `classify` at module scope rather than as a class method. It is outside the canonical path and not covered by the existing tests. Compatibility promises need a targeted check or retirement.
- `lsl_adapter.py` discards acquired timestamps. This limits freshness, jitter, sample-gap, and event-lock analysis. LSL documents the timestamps and synchronization mechanisms available to an integration [R10].
- The lightweight EDF/BDF parser assumes a common rectangular sample array and does not implement general EDF+ annotation processing. Use a validated scientific I/O backend for broader dataset support rather than presenting the custom loader as a complete EDF implementation [R9].
- Several tests accept either success or blocked status, and some tests assert that a field is bounded rather than that the intended scientific or control outcome occurred. These are useful smoke checks but weak behavioral requirements.
- The default minimum CI coverage is 50%. Raising the number alone would not address the independently reproduced failures. Requirements, adversarial cases, and independent oracles matter more.

## 4. Research that changes the recommended direction

This is a targeted review of primary research and official tools available by 2 November 2026, not a claim to have surveyed all science or all competing systems. Source results belong to their authors and are not results of SynapDrive-AI.

| Research | Relevant finding | Design implication |
| --- | --- | --- |
| EEG-FM-Compass, National Science Review, August 2026 [R1] | Comparison of 12 foundation models across 13 datasets found specialist models remained competitive; larger models did not consistently generalize better | Compare strong small baselines with selected larger encoders; use measured benefit, cost, and calibration burden to choose |
| From confidence to caution, Journal of Neural Engineering, October 23, 2026 [R2] | Cross-session conformal/selective gates traded decisiveness for fewer erroneous commands | Evaluate command risk and coverage together; do not claim coverage guarantees survive arbitrary session shift |
| EDAPT, Journal of Neural Engineering, April 2026 [R3] | Population pretraining plus continual supervised updates improved decoding in its evaluated datasets | Build a supervised adaptation experiment with revealed labels and guarded promotion; the paper's open-loop evaluation does not establish closed-loop user benefit |
| Brain-computer interface control with AI copilots, Nature Machine Intelligence, September 2025 [R4] | Demonstrated shared assistance with noninvasive EEG in cursor and robotic tasks | Shared autonomy is a credible direction and existing prior art; benchmark agency and task benefit, not only decoder accuracy |
| Same Brain, Different Prediction, May 2026 preprint [R5] | Investigated prediction instability caused by preprocessing choices | Treat preprocessing identity and sensitivity as first-class evidence; this source is a preprint, not established clinical validation |
| Computational framework for co-adaptive interfaces, Nature Machine Intelligence, March 2026 [R6] | Examined interacting user/decoder adaptation using a myoelectric human interface | Simulate two adapting learners and test update rates; do not transfer EMG findings directly into EEG claims |
| NASA runtime-assurance verification framework, 2024 [R7] | Explicitly models monitor, fallback, dynamics, and timing assumptions | Upgrade fallback from callback selection to a model-based, testable switching contract |
| MOABB official evaluation API [R8] | Supports within-session, cross-session, and cross-subject evaluation protocols | Use grouped, reproducible comparisons with explicit session and participant boundaries |

The practical opportunity is to connect these lines carefully. A better decoder cannot repair an expired permission, a swapped montage, a stale world model, or a fallback that cannot stop the plant. A more conservative gate cannot help if it blocks every useful interaction. A task-completion improvement cannot establish user benefit if the machine repeatedly overrides the person.

## 5. The proposed advanced architecture

**Proposed research purpose:** make assistive autonomy earn and continuously re-earn narrowly bounded action authority from current evidence, while retaining explicit user control and measurable usefulness.

### A. Intent as a time-dependent hypothesis, with a real no-command state

Maintain a belief over explicitly supported goals/actions and a no-command state. Model evidence age, repeated-window dependence, and transitions between idle and active control. Separate uncertainty about a decoded class from uncertainty about whether the person currently intends to issue any command.

Use sequential evidence and calibrated gates to reduce unintended activations during rest, sensor adjustment, distraction, and ambiguous transitions. Temporal smoothing must be evaluated for harmful delay and must not suppress a trusted veto.

**Evidence required:** time-resolved false activations during annotated no-control periods, missed intended commands, latency distributions, and results on participants/sessions excluded from training. Public rest recordings can support an offline experiment but are not equivalent to naturalistic unattended home use [R11].

### B. Clarification and constrained progress under ambiguity

When the evidence does not identify a unique authorized goal, select among: ask a minimal accessible clarification, wait for more evidence, perform a low-stakes reversible interaction, or enter the required baseline control mode. Preserve the original request and record why assistance changed the proposed action.

One worthwhile research hypothesis is to permit a shared initial action only when it is authorized and satisfies the constraints of every retained goal hypothesis. If “take cup A” and “take cup B” share a safe positioning segment, that segment may permit progress before a final grasp decision. This requires explicit plant geometry, user permissions, and a proof or bounded check for that segment; uncertainty alone never authorizes exploratory physical motion.

**Evidence required:** task success and interaction burden at matched command-error budgets, including misleading context, user goal changes, and cases where there is no shared permissible action. POMDP-based assistance and information gathering already exist in prior work [R12]; any contribution here must be evaluated as a specific extension/integration.

### C. Action admission that the executor can check independently

Replace a mutable dictionary plus an `allowed` boolean with an admission artifact binding:

- action identity and parameters;
- run, cycle, and sequence identity;
- current policy and capability versions;
- observation identity, timestamps, and freshness bounds;
- decoder, preprocessing, montage, and calibration identities;
- relevant world-state version and predicted constraint bounds;
- validity interval and required fallback behavior.

The executor verifies these bindings before dispatch. A change in permission, state, or model invalidates dependent admissions. A stale decision must not be reusable for a different packet. Durable pre-dispatch and outcome records support recovery after crashes. For distributed hardware, use idempotent operations and explicit acknowledgments where supported; do not promise universal exactly-once physical execution.

Cryptographic authentication helps across actual trust boundaries. In-process checks still need immutable state and race handling. Signing a mutable or scientifically invalid claim does not fix its meaning.

**Evidence required:** stale-decision rejection, revocation races, reordered/duplicate messages, wrong-action substitution, worker termination, logging failure, and reconnect recovery.

### D. A dynamics-aware safety layer in one bounded simulation

Start with a simple differential-drive mobility model or a cursor model with explicit velocity/acceleration, obstacles, and delayed observations. Separate that environment from the control policy so the controller is not grading its own predictions.

For a simple straight-line braking model, a candidate constraint is:

`available_distance >= velocity * worst_case_delay + velocity^2 / (2 * minimum_deceleration) + uncertainty_margin`

This is only meaningful under its stated assumptions: positive bounded deceleration, a valid motion model, bounded delay, appropriate relative obstacle motion treatment, and adequate state estimates. It is not a universal wheelchair or robot safety guarantee.

Use reachability or a suitable control-barrier/safety-filter method where assumptions and computation permit it. Check recoverability before the last safe switching instant, then execute and verify a baseline response. Model watchdog, estimator, and solver failures explicitly.

**Evidence required:** minimum clearance, collisions/constraint violations, recovery success, missed deadlines, time to safe response, and sensitivity to dynamics mismatch. An independent process or microcontroller watchdog is a later hardware integration requirement, not a property conferred by Python callbacks.

### E. Adaptation with qualification expiry, shadow operation, and rollback

Evolve from threshold adaptation to a controlled decoder/preprocessor update lifecycle:

1. Frozen baseline artifact and initial qualification.
2. Candidate trained from permitted, labeled, provenance-checked observations.
3. Shadow predictions without action authority.
4. Evaluation on independent data with predefined metrics and tolerances.
5. Explicit promotion scope and artifact identity.
6. Continuous monitoring, qualification expiry, rollback, and requalification.

Model outputs, apparent task success, and acceptance by the safety filter must not silently become ground-truth intent labels. Repeatedly choosing candidates on the same validation set overfits that set. Hold back a final audit set or use a statistically appropriate sequential evaluation plan.

Consider slower decoder updates than control updates, stabilization intervals, and safeguards against feedback loops between assistance and the signals used for training. EMG co-adaptation research motivates testing this interaction, but EEG behavior requires its own evidence [R6].

**Evidence required:** pre/post-update risk and coverage, participant-level variation, forgetting, contamination resistance, recovery after bad updates, and calibration effort. Abstention or rollback must count as part of performance, not disappear from the denominator.

### F. Multimodal assistance that cannot silently substitute machine context for user authorization

Support EEG, EMG, gaze, switch/keyboard input, and measured environmental state through typed, timestamped adapters. Represent sensor-specific failure and dependence. Two correlated views of the same source are not two independent votes.

Gaze or scene context can identify candidate objects; a user-control channel can authorize a choice; plant sensing can constrain execution. The system should not treat a likely object in a scene as proof of what the user wanted. Explicit rejection overrides the learning interpretation of an otherwise successful action.

**Evidence required:** missing/conflicting modalities, gaze on distracting objects, corrupted context, one sensor dominating, and time misalignment. Record intervention frequency, user override latency, and task outcomes. Subjective agency and burden require actual human evaluation; software proxies cannot establish them.

### G. A reproducible assurance and failure-analysis platform

Produce one versioned run capsule linking data provenance, split identities, preprocessing, model/configuration hashes, permissions, world state, feedback, timing, seeds, and results. Provide an independent verifier that does not import the controller's decision logic.

Record enough state for deterministic simulation replay in a defined environment. For numerically sensitive accelerators and cross-platform computations, specify supported reproducibility tolerances instead of promising universal bitwise equality.

When a fault occurs, minimize its reproducing scenario and preserve it as a regression case. Distinguish four questions: did the signal change; did the decoder change its answer; did the gate respond correctly; did the simulated task satisfy its constraints? This avoids treating a single green boolean as evidence for all four.

**Evidence required:** replay with rejection feedback and policy changes, corrupted/incomplete capsules, externally retained signed checkpoints, altered schemas, and reproduction by a clean install.

## 6. Concrete research experiments and falsification criteria

All experiments below are proposed. No listed outcome is a result of this audit.

| Experiment | Baselines and controls | What would support the proposed benefit | What would refute or limit it |
| --- | --- | --- | --- |
| Selective neural command gating | Ungated decoder, tuned confidence threshold, calibrated selective gate, conformal variant | Lower command error at matched useful coverage; acceptable delay | Apparent gains vanish at matched coverage or under held-out session shift |
| Asynchronous no-command control | Forced-choice decoder, explicit rest model, sequential evidence model | Fewer false activations over time without unacceptable missed commands | Lower activation rate comes only from near-total abstention or excessive delay |
| Shared assistance | Direct user commands, fixed assistance, proposed hypothesis-aware assistance | Better task outcomes at matched constraints and intervention budget | Wrong-goal commitments, more overrides, or performance relying on oracle intent |
| Dynamics-aware fallback | Present symbolic gate, fixed stopping heuristic, model-based safety filter | Fewer simulated constraint violations under defined disturbances | Safety degrades under stated model bounds or response deadlines are missed |
| Guarded adaptation | Frozen baseline, unconstrained adaptation, guarded candidate lifecycle | Better later-session performance without exceeding predefined risk bounds | Label contamination, repeated-holdout overfitting, forgetting, or frequent rollbacks erase gains |
| Acquisition identity and freshness | Current count/rate check versus complete observation contracts | Rejection or controlled degradation for swaps, units, timing, and stale observations | Valid data is rejected broadly, or consequential identity changes remain undetected |
| Reproducibility | Current replay versus complete capsule and independent verifier | Reproduced decisions/memory consequences and explained numerical differences | Rejection feedback, policy, model, or initial state changes remain unaccounted for |

### Real-data protocol

Use a small, deliberately chosen dataset suite before attempting broad leaderboards. OpenBMI/Lee2019_MI and BNCI2014_001 provide relevant motor-imagery evaluation surfaces through MOABB [R8]. PhysioNet EEG Motor Movement/Imagery includes annotated rest and movement/imagery runs [R11]. Correctly map its task-dependent event codes; the same event code has different meanings in different runs. Do not combine motor execution and imagery as equivalent labels.

Define subject, session, run, and parent-trial identities before epoching. Prevent overlapping or duplicate windows crossing evaluation boundaries. Fit every learned preprocessing stage, feature transform, calibration procedure, and classifier only on the permitted training/calibration partition. Specify when unsupervised target-session data is allowed. Separate that setting from zero-shot transfer.

Evaluate at least a strong spatial-filter/linear baseline, an established covariance baseline, and a compact neural model before selecting one or two foundation-model candidates. Existing specialist tooling includes pyRiemann [R13]. Use independently versioned optional plugins so the small assurance runtime does not require every training framework.

An offline dataset can validate decoding and policy behavior against its labels. Feeding recorded labels into a simulator does not make the result a human closed-loop control study. Use explicit simulated-user models and sensitivity sweeps for offline closed-loop hypotheses, then seek participant evidence for actual user effects.

### Metrics with unambiguous denominators

- **Command coverage:** issued commands divided by eligible decision opportunities.
- **Error among issued commands:** wrong commands divided by issued commands.
- **Wrong-command opportunity rate:** wrong commands divided by all eligible decision opportunities.
- **False activation rate:** unintended commands per unit of annotated no-control time.
- **Task metrics:** completion, wrong-goal completion, collisions/violations, clearance, path efficiency, and recovery success.
- **Timing:** observation age, inference delay, gate delay, end-to-end response, stop response, and deadline misses; report distributions and maximum observed values on declared hardware.
- **Adaptation:** calibration effort, update cost, promotion/rejection/rollback rate, forgetting, and performance by subject/session.
- **User control:** intervention and override frequency, veto latency, and human-reported agency and workload when a real study exists.

Report uncertainty intervals at the participant/session level where appropriate; correlated overlapping windows are not independent observations. A conformal nominal coverage level needs its assumptions stated and checked empirically under shift. Zero observed failures is not proof of zero failure probability. Publish abstentions, excluded data, negative controls, and adverse outcomes.

## 7. Flagship societal use and an achievable release sequence

The strongest first demonstration is an accessible simulated workstation or mobility environment in which a person can select a supported goal, retain a reliable veto, and receive assistance around uncertainty and hazards. Recorded EEG, a simulator, and explicit alternative inputs can make the software reproducible before any hardware study.

An example: two possible targets are near each other; neural evidence is ambiguous; context favors the wrong target; the interface asks an accessible clarification; permission changes; one sensor drops out; the baseline controller brings the simulated device to its defined safe state; a new decoder remains in shadow until independently evaluated; the complete event sequence is replayable. The value is measured successful assistance under these conditions, not the visual impressiveness of the demo.

| Release stage | Concrete deliverable | Required exit evidence |
| --- | --- | --- |
| Foundation repair | Strict packet contracts, finite-value checks, exact capabilities, stop/veto semantics, corrected replay, fixed session loop and sequential-plan behavior | Reproductions above become meaningful regression requirements; original functionality remains verified; release manifest matches |
| Scientific evaluation | Grouped real-data adapters, locked splits, baseline decoders, separate calibration and evaluation, no-command metrics | Reproducible real-data reports including chance/label-permutation and duplicate/overlap controls; no synthetic-to-human claim substitution |
| Closed-loop simulation | One independent environment, explicit dynamics, deadline/freshness rules, verified baseline responses, constrained shared assistance | Comparison against direct control, fixed gates, and always-abstain controls over disclosed scenarios and disturbances |
| Controlled adaptation | Versioned artifacts, shadow evaluation, promotion policy, rollback, dependency invalidation | Independent evidence that permitted updates help under the defined protocol without hiding increased risk or abstention |
| External validation | Clean third-party reproduction, then appropriate acquisition/hardware and human collaborations | Hardware timing and safety evidence; human usefulness/agency evidence when those claims are made |

Use Python for scientific orchestration, benchmarking, training adapters, and simulation until measurements justify a change. Preserve a small, independently testable action-admission/executor interface. A narrow Rust or C++ component may later help with deployment constraints, isolation, or timing, but changing languages does not establish safety or faster end-to-end control. Choose based on profiling, target hardware, and verification needs.

Retain the existing Apache-2.0 project license. Credit scientific methods and dataset creators. Check model-weight and dataset permissions separately before redistributing them; an open-source code license does not automatically cover third-party assets. No external model or donor source was copied into the repository during this audit.

## 8. What can be delivered through software work, and what requires external evidence

**Software work can deliver:** the repairs; enforceable action contracts; complete replay; grouped dataset evaluation; established decoder integrations; measured selective prediction; independent simulation; dynamics-aware bounded safety experiments; shadow adaptation and rollback; fault scenario minimization; and reproducible evidence packaging.

**Hardware or research collaboration is needed to establish:** performance of a particular live acquisition device, worst-case control timing on its target platform, physical braking or manipulation guarantees, naturalistic neural intent reliability, participant agency and workload, clinical effectiveness, and usefulness in independent home operation.

**No justified promise now:** an arbitrary decoding accuracy, a universal brain decoder, reliable mind reading, unprecedented scientific novelty, clinical readiness, universally safe physical autonomy, or guaranteed societal adoption. These are empirical questions. A demanding experiment that exposes failure is progress when it eliminates an invalid design.

The decision recommended here is to evolve SynapDrive-AI into a rigorous assistive shared-autonomy research platform, beginning with enforcement and measurement. The current archive is a viable starting point, but it needs substantive repairs before its strongest governance language should be trusted as a general guarantee.

## Primary sources and official tools

All were consulted for this audit on 2 November 2026. Publication dates below are article dates where verified, not search-engine crawl dates.

- **[R1]** Liu et al. *EEG-FM-Compass: progress, benchmarking and future directions for EEG foundation models*. National Science Review, published August 3, 2026; corrected/typeset October 12, 2026. https://doi.org/10.1093/nsr/nwag466
- **[R2]** Xing and Nagarajan. *From confidence to caution: conformal gating for cross-session motor imagery brain-computer interfaces*. Journal of Neural Engineering, October 23, 2026. https://pubmed.ncbi.nlm.nih.gov/42805221/ ; https://doi.org/10.1088/1741-2552/aead26
- **[R3]** Haxel et al. *EDAPT: towards calibration-free BCIs with continual online adaptation*. Journal of Neural Engineering, April 7, 2026. https://doi.org/10.1088/1741-2552/ae5689
- **[R4]** Lee et al. *Brain-computer interface control with artificial intelligence copilots*. Nature Machine Intelligence, online September 1, 2025. https://pubmed.ncbi.nlm.nih.gov/41221369/ ; https://doi.org/10.1038/s42256-025-01090-y
- **[R5]** Hou et al. *Same Brain, Different Prediction: How Preprocessing Choices Undermine EEG Decoding Reliability*. arXiv preprint, May 8, 2026. https://arxiv.org/abs/2605.07212
- **[R6]** *Computational framework to predict and shape human-machine interactions in closed-loop, co-adaptive neural interfaces*. Nature Machine Intelligence, March 23, 2026. https://doi.org/10.1038/s42256-026-01194-z
- **[R7]** Slagel et al. *A Verification Framework for Runtime Assurance of Autonomous UAS*. NASA Technical Reports Server, 2024. https://ntrs.nasa.gov/citations/20240007986
- **[R8]** MOABB, official evaluation and dataset API. https://moabb.neurotechx.com/docs/api.html
- **[R9]** MNE, official EDF loader documentation. https://mne.tools/stable/generated/mne.io.read_raw_edf.html
- **[R10]** Lab Streaming Layer, official time-synchronization documentation. https://labstreaminglayer.readthedocs.io/info/time_synchronization.html
- **[R11]** Schalk, *EEG Motor Movement/Imagery Dataset*, PhysioNet, v1.0.0. https://physionet.org/content/eegmmidb/1.0.0/
- **[R12]** Javdani et al., *Shared Autonomy via Hindsight Optimization*, Carnegie Mellon Robotics Institute publication record. https://publications.ri.cmu.edu/shared-autonomy-via-hindsight-optimization
- **[R13]** pyRiemann, official minimum-distance-to-mean classifier documentation. https://pyriemann.readthedocs.io/en/latest/generated/pyriemann.classification.MDM.html

## Reproduction commands

Extract the original archive and install its declared runtime/development dependencies. The commands below assume the extracted repository is the working directory. Save the diagnostic script from Appendix A as `audit_probes.py` outside the repository, then point `--repo` at the extracted repository.

```bash
python -m pytest -q --cov=synapdrive_ai --cov-report=term-missing --cov-report=json:current-coverage.json --cov-fail-under=50
ruff check .
pyright
python -m scripts.run_v1_validation --out current-validation.json
python -m build --wheel --no-isolation --outdir ../audit-dist
python ../audit_probes.py --repo . --out ../probe-results.json
```

The final command reports observed behavior. It deliberately reproduces defects rather than presenting their outcomes as successful safety tests. Its bounded session-loop probe stops its own execution after detecting repeated windows. It does not operate physical hardware.


## Appendix A. Diagnostic script

```python
"""Reproduce audit observations without changing SynapDrive-AI source.

Run with the repository root as current working directory, or supply --repo.
These are diagnostic observations, not performance benchmarks or hardware tests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.repo.resolve()))

    import numpy as np
    from synapdrive_ai.assurance.hashchain import EvidenceHashChain
    from synapdrive_ai.bci.intent_generator import generate_intent
    from synapdrive_ai.benchmarking.dataset import EpochDataset
    from synapdrive_ai.benchmarking.decoders import SpectralCentroidDecoder
    from synapdrive_ai.benchmarking.evaluation import _split_indices
    from synapdrive_ai.benchmarking.runtime_adapter import QualifiedDecoderAdapter
    from synapdrive_ai.cognition.world_model import ActionModel
    from synapdrive_ai.neuro.eeg_loader import EEGLoader
    from synapdrive_ai.neuro.session_analyzer import SessionAnalyzer
    from synapdrive_ai.neuro.signal_quality import SignalQualityAnalyzer
    from synapdrive_ai.neuro.task_planner import ExecutorBridge, TaskPlan, TaskStep
    from synapdrive_ai.pipeline import SynapDrivePipeline
    from synapdrive_ai.replay.recording import make_record
    from synapdrive_ai.runtime.governed_runtime import GovernedRuntime
    from synapdrive_ai.runtime.simplex import SimplexController
    from synapdrive_ai.stress.campaign import StressCampaign

    observations: dict[str, object] = {}

    def run(packet):
        pipe = SynapDrivePipeline(simulate_delay=False)
        try:
            result = pipe.run_intent_packet(packet)
        except Exception as exc:
            return {
                "exception": type(exc).__name__,
                "message": str(exc),
                "action_log_count": len(pipe.get_action_log()),
                "evidence_entry_count": len(pipe.evidence.chain.entries()),
            }
        return {
            "status": result["status"],
            "issues": result["runtime"]["assessment"]["issues"],
            "assurance_passed": result["assurance"]["passed"],
            "action_log_count": len(pipe.get_action_log()),
        }

    observations["minimal_packet_missing_source"] = run({"intent": "move_left", "confidence": 0.99})
    observations["unqualified_packet_with_source"] = run(
        {"intent": "move_left", "confidence": 0.99, "source": "unqualified"}
    )
    packet = generate_intent("move left")
    packet["predicted_risk"] = float("nan")
    observations["nan_risk"] = run(packet)
    packet = generate_intent("move left")
    packet["confidence"] = float("nan")
    observations["nan_confidence"] = run(packet)
    packet = generate_intent("move left")
    packet["signal_quality"] = float("nan")
    packet["drift_score"] = float("nan")
    observations["nan_quality_and_drift"] = run(packet)

    packet = generate_intent("move left")
    packet["probabilities"] = {"move_right": 1.0}
    observations["distribution_intent_disagreement"] = run(packet)
    packet = generate_intent("move left")
    packet["probabilities"] = {"move_left": 0.5, "move_right": 0.5}
    observations["ambiguous_distribution_derived_uncertainty"] = run(packet)
    packet["uncertainty"] = 0.0
    observations["ambiguous_distribution_overridden_uncertainty"] = run(packet)

    quality_analyzer = SignalQualityAnalyzer(256.0)
    t = np.arange(512) / 256.0
    signals = {
        "nonzero_flatline": np.ones(512),
        "pure_60hz": np.sin(2 * np.pi * 60 * t),
        "eight_channels_one_dead": np.vstack([np.sin(2 * np.pi * 10 * t)] * 7 + [np.ones(512)]),
    }
    rng = np.random.default_rng(11)
    partial_nan = rng.normal(size=512)
    partial_nan[::5] = np.nan
    signals["twenty_percent_nonfinite"] = partial_nan
    for name, signal in signals.items():
        quality = quality_analyzer.analyze(signal)
        packet = generate_intent("move left")
        packet["signal_quality"] = quality.score
        observations[name] = {"quality": quality.to_dict(), "runtime": run(packet)}

    pipe = SynapDrivePipeline(simulate_delay=False)
    packet = generate_intent("stop")
    packet["signal_quality"] = 0.0
    out = pipe.run_intent_packet(packet)
    observations["stop_with_bad_signal"] = {
        "status": out["status"],
        "fallback": out["result"]["fallback_action"],
        "action_log_count": len(pipe.get_action_log()),
    }
    pipe = SynapDrivePipeline(simulate_delay=False)
    packet = generate_intent("move left")
    packet.update({"issued_at": 0, "expires_at": 1, "sequence": 1, "command_id": "same-id"})
    outputs = [pipe.run_intent_packet(packet)["status"] for _ in range(2)]
    observations["stale_duplicate_packet"] = {
        "statuses": outputs,
        "actions": len(pipe.get_action_log()),
    }

    pipe = SynapDrivePipeline(simulate_delay=False)
    packet = generate_intent("move left")
    rejected = pipe.run_intent_packet(packet, feedback={"accepted": False})
    record = make_record(
        mode="text",
        raw_input={"text": "move left"},
        image_label=None,
        intent_packet=packet,
        pipeline_output=rejected,
    )
    replayed = SynapDrivePipeline(simulate_delay=False).run_intent_packet(record.intent_packet)
    observations["feedback_not_preserved_by_record"] = {
        "original_memory": rejected["memory"]["state"],
        "replayed_memory": replayed["memory"]["state"],
        "evidence_hashes_equal": rejected["evidence"]["event_hash"]
        == replayed["evidence"]["event_hash"],
    }

    runtime = GovernedRuntime()
    runtime.world_model.register(ActionModel("stop_disable_brakes", predicted_risk=0.1))
    runtime.permissions.revoke_all()
    pipe = SynapDrivePipeline(simulate_delay=False, runtime=runtime)
    out = pipe.run_intent_packet(
        {"intent": "stop_disable_brakes", "confidence": 0.99, "source": "custom-action-probe"}
    )
    observations["custom_action_safe_substring_after_revocation"] = {
        "status": out["status"],
        "permission": out["runtime"]["assessment"]["permission_allowed"],
    }

    runtime = GovernedRuntime()
    decision = runtime.assess(generate_intent("move left"))
    simplex = SimplexController(
        lambda p: {"received_intent": p["intent"]}, lambda a: {"fallback": a}
    )
    execution = simplex.execute({"intent": "different_unassessed_action"}, decision)
    observations["simplex_decision_packet_mismatch"] = {
        "controller": execution.controller,
        "result": execution.result,
    }

    pipe = SynapDrivePipeline(simulate_delay=False)
    proposal = pipe.plan_shared_action(
        user_intent="move_left", user_confidence=0.99, machine_candidates=[], goal=lambda _: 0.0
    )
    observations["goal_preservation_flag_with_zero_goal_score"] = {
        "flag": proposal.preserved_user_goal,
        "selected_action": proposal.selected_action,
        "goal_scores": [item.goal_score for item in proposal.ranked],
    }

    pipe = SynapDrivePipeline(simulate_delay=False)
    plan = TaskPlan(
        "dependent-steps",
        [
            TaskStep("unsupported prerequisite", min_confidence=0.8, fallback="freeze"),
            TaskStep("move right"),
        ],
    )
    trace = ExecutorBridge(pipeline=pipe).execute(plan)
    observations["freeze_plan_continues_next_step"] = {
        "outcome": trace.outcome,
        "steps": [step.pipeline_status for step in trace.steps],
        "action_log_count": len(pipe.get_action_log()),
    }

    class RepeatedWindow(RuntimeError):
        pass

    class BoundedAnalyzer(SessionAnalyzer):
        calls = 0

        def _run_epoch_through_pipeline(self, *call_args, **kwargs):
            self.calls += 1
            if self.calls > 5:
                raise RepeatedWindow("probe stopped the non-advancing loop after 5 windows")
            return super()._run_epoch_through_pipeline(*call_args, **kwargs)

    analyzer = BoundedAnalyzer(window_s=1, step_s=0)
    try:
        analyzer.run(EEGLoader().load_array(np.sin(2 * np.pi * 10 * t), sampling_rate=256))
        observations["zero_step_session"] = {"repeated_window_detected": False}
    except RepeatedWindow:
        observations["zero_step_session"] = {
            "repeated_window_detected": True,
            "calls_before_probe_stop": analyzer.calls,
        }

    observations["text_parser_negation_and_conflict"] = {}
    for text in ["do not move left", "stop move left"]:
        pipe = SynapDrivePipeline(simulate_delay=False)
        out = pipe.run_text_command(text)
        observations["text_parser_negation_and_conflict"][text] = {
            "status": out["status"],
            "action": out["intent"]["intent"],
            "confidence": out["intent"]["confidence"],
        }

    sr = 128.0
    times = np.arange(128) / sr
    epochs, labels = [], []
    for label, frequency in [("left", 10.0), ("right", 20.0)]:
        for _ in range(12):
            signal = np.sin(2 * np.pi * frequency * times) + rng.normal(0, 0.01, 128)
            epochs.append(np.vstack([signal, signal * 0.7]))
            labels.append(label)
    ds = EpochDataset(
        np.asarray(epochs), np.asarray(labels), sr, ["C3", "C4"], "synthetic-schema-probe-only"
    )
    adapter = QualifiedDecoderAdapter(
        SpectralCentroidDecoder(), ds, {"left": "move_left", "right": "move_right"}
    )
    packet = adapter(
        ds.epochs[0], {"sampling_rate": sr, "channel_names": ["C4", "C3"], "units": "incorrect"}
    )
    observations["decoder_ignores_channel_names_and_units"] = {
        "qualified_on_synthetic_fixture": adapter.qualification.qualified,
        "analysis_only": packet.get("analysis_only"),
        "action": packet["intent"],
    }

    prototypes = rng.normal(size=(4, 2, 128))
    duplicated = np.repeat(prototypes, 8, axis=0)
    duplicate_labels = np.repeat(np.array(["left", "right", "left", "right"]), 8)
    train, test = _split_indices(duplicate_labels, 0.25, 7)
    train_hashes = {hashlib.sha256(duplicated[i].tobytes()).hexdigest() for i in train}
    overlap = sum(hashlib.sha256(duplicated[i].tobytes()).hexdigest() in train_hashes for i in test)
    observations["random_trial_split_allows_duplicate_overlap"] = {
        "test_trials": len(test),
        "test_trials_identical_to_training": overlap,
        "note": "Negative-control fixture, not evidence that an actual external dataset leaked.",
    }

    campaign = StressCampaign(256.0, min_quality=0.60)
    report = campaign.run(
        [("nonzero_flatline", np.ones(512)), ("pure_60hz", signals["pure_60hz"])],
        lambda _s, q: q < 0.60,
    )
    observations["threshold_campaign_with_faulty_sensors"] = report.to_dict()

    chain = EvidenceHashChain()
    chain.append({"a": 1})
    chain.append({"b": 2})
    observations["chain_without_external_checkpoint"] = {
        "full_valid": chain.verify(chain.entries()),
        "truncated_prefix_valid": chain.verify(chain.entries()[:1]),
        "empty_valid": chain.verify([]),
        "note": "A signed original ledger or externally retained head/count is needed to detect removal of a valid suffix.",
    }

    observations["metadata"] = {
        "python": sys.version,
        "numpy": np.__version__,
        "core_pipeline_sha256": hashlib.sha256(
            (args.repo / "synapdrive_ai/pipeline.py").read_bytes()
        ).hexdigest(),
        "scope": "simulated software behavior; no human, hardware or clinical performance",
    }
    encoded = json.dumps(observations, indent=2, allow_nan=False)
    if args.out:
        args.out.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
```

## Appendix B. Actual diagnostic output

```json
{
  "minimal_packet_missing_source": {
    "exception": "KeyError",
    "message": "'source'",
    "action_log_count": 1,
    "evidence_entry_count": 0
  },
  "unqualified_packet_with_source": {
    "status": "success",
    "issues": [],
    "assurance_passed": true,
    "action_log_count": 1
  },
  "nan_risk": {
    "status": "success",
    "issues": [],
    "assurance_passed": true,
    "action_log_count": 1
  },
  "nan_confidence": {
    "status": "success",
    "issues": [],
    "assurance_passed": false,
    "action_log_count": 1
  },
  "nan_quality_and_drift": {
    "status": "success",
    "issues": [],
    "assurance_passed": true,
    "action_log_count": 1
  },
  "distribution_intent_disagreement": {
    "status": "success",
    "issues": [],
    "assurance_passed": true,
    "action_log_count": 1
  },
  "ambiguous_distribution_derived_uncertainty": {
    "status": "blocked",
    "issues": [
      "uncertainty-above-policy"
    ],
    "assurance_passed": true,
    "action_log_count": 0
  },
  "ambiguous_distribution_overridden_uncertainty": {
    "status": "success",
    "issues": [],
    "assurance_passed": true,
    "action_log_count": 1
  },
  "nonzero_flatline": {
    "quality": {
      "score": 0.65,
      "state": "degraded",
      "finite_fraction": 1.0,
      "flatline_fraction": 1.0,
      "clipping_fraction": 1.0,
      "dropout_fraction": 0.0,
      "line_noise_ratio": 0.0,
      "issues": [
        "flatline",
        "clipping"
      ]
    },
    "runtime": {
      "status": "success",
      "issues": [],
      "assurance_passed": true,
      "action_log_count": 1
    }
  },
  "pure_60hz": {
    "quality": {
      "score": 0.908333,
      "state": "good",
      "finite_fraction": 1.0,
      "flatline_fraction": 0.0,
      "clipping_fraction": 0.03125,
      "dropout_fraction": 0.03125,
      "line_noise_ratio": 1.0,
      "issues": [
        "line-noise"
      ]
    },
    "runtime": {
      "status": "success",
      "issues": [],
      "assurance_passed": true,
      "action_log_count": 1
    }
  },
  "eight_channels_one_dead": {
    "quality": {
      "score": 0.788997,
      "state": "degraded",
      "finite_fraction": 1.0,
      "flatline_fraction": 0.125,
      "clipping_fraction": 0.138672,
      "dropout_fraction": 0.013672,
      "line_noise_ratio": 0.0,
      "issues": [
        "clipping"
      ]
    },
    "runtime": {
      "status": "success",
      "issues": [],
      "assurance_passed": true,
      "action_log_count": 1
    }
  },
  "twenty_percent_nonfinite": {
    "quality": {
      "score": 0.80293,
      "state": "good",
      "finite_fraction": 0.798828,
      "flatline_fraction": 0.0,
      "clipping_fraction": 0.003906,
      "dropout_fraction": 0.201172,
      "line_noise_ratio": 0.027014,
      "issues": [
        "non-finite-samples",
        "dropout"
      ]
    },
    "runtime": {
      "status": "success",
      "issues": [],
      "assurance_passed": true,
      "action_log_count": 1
    }
  },
  "stop_with_bad_signal": {
    "status": "blocked",
    "fallback": "hold_position",
    "action_log_count": 0
  },
  "stale_duplicate_packet": {
    "statuses": [
      "success",
      "success"
    ],
    "actions": 2
  },
  "feedback_not_preserved_by_record": {
    "original_memory": "quarantined",
    "replayed_memory": "validated",
    "evidence_hashes_equal": false
  },
  "custom_action_safe_substring_after_revocation": {
    "status": "success",
    "permission": true
  },
  "simplex_decision_packet_mismatch": {
    "controller": "advanced",
    "result": {
      "received_intent": "different_unassessed_action"
    }
  },
  "goal_preservation_flag_with_zero_goal_score": {
    "flag": true,
    "selected_action": "move_left",
    "goal_scores": [
      0.0
    ]
  },
  "freeze_plan_continues_next_step": {
    "outcome": "frozen",
    "steps": [
      "deferred",
      "success"
    ],
    "action_log_count": 1
  },
  "zero_step_session": {
    "repeated_window_detected": true,
    "calls_before_probe_stop": 6
  },
  "text_parser_negation_and_conflict": {
    "do not move left": {
      "status": "success",
      "action": "move_left",
      "confidence": 1.0
    },
    "stop move left": {
      "status": "success",
      "action": "move_left",
      "confidence": 1.0
    }
  },
  "decoder_ignores_channel_names_and_units": {
    "qualified_on_synthetic_fixture": true,
    "analysis_only": false,
    "action": "move_left"
  },
  "random_trial_split_allows_duplicate_overlap": {
    "test_trials": 8,
    "test_trials_identical_to_training": 8,
    "note": "Negative-control fixture, not evidence that an actual external dataset leaked."
  },
  "threshold_campaign_with_faulty_sensors": {
    "total_trials": 2,
    "invariant_passes": 2,
    "invariant_failures": 0,
    "trials": [
      {
        "trial": 1,
        "fault": "nonzero_flatline",
        "quality_score": 0.65,
        "quality_state": "degraded",
        "expected_block": false,
        "blocked": false,
        "invariant_passed": true
      },
      {
        "trial": 2,
        "fault": "pure_60hz",
        "quality_score": 0.908333,
        "quality_state": "good",
        "expected_block": false,
        "blocked": false,
        "invariant_passed": true
      }
    ]
  },
  "chain_without_external_checkpoint": {
    "full_valid": true,
    "truncated_prefix_valid": true,
    "empty_valid": true,
    "note": "A signed original ledger or externally retained head/count is needed to detect removal of a valid suffix."
  },
  "metadata": {
    "python": "3.12.14 (main, Aug 25 2026, 14:00:49) [Clang 22.1.3 ]",
    "numpy": "2.3.5",
    "core_pipeline_sha256": "3782846da09372bffb5400ed990379c3502f5c0bbfa3a903a598d5a55af9d472",
    "scope": "simulated software behavior; no human, hardware or clinical performance"
  }
}
```

## Appendix C. Machine-readable verification summary

```json
{
  "coverage_totals": {
    "covered_lines": 2220,
    "num_statements": 3068,
    "percent_covered": 69.70108695652173,
    "percent_covered_display": "69.7",
    "missing_lines": 848,
    "excluded_lines": 18,
    "percent_statements_covered": 72.35984354628422,
    "percent_statements_covered_display": "72.4",
    "num_branches": 612,
    "num_partial_branches": 119,
    "covered_branches": 345,
    "missing_branches": 267,
    "percent_branches_covered": 56.372549019607845,
    "percent_branches_covered_display": "56.4"
  },
  "pipeline_coverage": {
    "covered_lines": 98,
    "num_statements": 100,
    "percent_covered": 97.22222222222223,
    "percent_covered_display": "97.2",
    "missing_lines": 2,
    "excluded_lines": 0,
    "percent_statements_covered": 98.0,
    "percent_statements_covered_display": "98.0",
    "num_branches": 8,
    "num_partial_branches": 1,
    "covered_branches": 7,
    "missing_branches": 1,
    "percent_branches_covered": 87.5,
    "percent_branches_covered_display": "87.5"
  },
  "release_validator": {
    "schema": "synapdrive.validation.v1",
    "python": "3.12.14",
    "platform": "Linux-6.18.57-x86_64-with-glibc2.41",
    "passed": true,
    "check_count": 24,
    "checks": [
      {
        "check": "governed_declared_command_path",
        "passed": true
      },
      {
        "check": "unmodeled_action_fails_closed",
        "passed": true
      },
      {
        "check": "analysis_only_inference_cannot_actuate",
        "passed": true
      },
      {
        "check": "low_quality_fail_closed",
        "passed": true
      },
      {
        "check": "high_uncertainty_abstains",
        "passed": true
      },
      {
        "check": "decoder_drift_fail_closed",
        "passed": true
      },
      {
        "check": "permission_revoke_preserves_safe_stop",
        "passed": true
      },
      {
        "check": "errp_contradiction_quarantines_memory",
        "passed": true
      },
      {
        "check": "evidence_chain_valid",
        "passed": true
      },
      {
        "check": "evidence_tamper_detected",
        "passed": true
      },
      {
        "check": "ed25519_evidence_signature",
        "passed": true
      },
      {
        "check": "flatline_quality_detection",
        "passed": true
      },
      {
        "check": "multimodal_reliability_weighted_fusion",
        "passed": true
      },
      {
        "check": "counterfactual_shared_autonomy_prefers_lower_risk_candidate",
        "passed": true
      },
      {
        "check": "shadow_policy_has_no_actuation_authority",
        "passed": true
      },
      {
        "check": "guarded_adaptation_requires_held_out_improvement",
        "passed": true
      },
      {
        "check": "deterministic_cycle_evidence_replay",
        "passed": true
      },
      {
        "check": "decoder_benchmark_executes",
        "passed": true
      },
      {
        "check": "locally_qualified_decoder_reaches_governed_runtime",
        "passed": true
      },
      {
        "check": "qualified_decoder_sampling_mismatch_abstains",
        "passed": true
      },
      {
        "check": "qualified_decoder_session_analyzer_bridge",
        "passed": true
      },
      {
        "check": "task_threshold_blocks_before_simulated_actuation",
        "passed": true
      },
      {
        "check": "successful_action_commits_explicit_world_state",
        "passed": true
      },
      {
        "check": "fault_campaign_fail_closed",
        "passed": true
      }
    ]
  },
  "wheel_smoke": {
    "origin": "<isolated-wheel-install>/synapdrive_ai/__init__.py",
    "origin_path_redacted": true,
    "discovered_modules": 95,
    "import_failures": [],
    "pipeline_status": "success",
    "dashboard_home_status": 200
  },
  "audit_dependencies": {
    "numpy": "2.3.5",
    "cryptography": "47.0.0",
    "pytest": "9.2.0",
    "pytest-cov": "7.1.0",
    "coverage": "7.17.0",
    "ruff": "0.17.3",
    "pyright": "1.1.414",
    "build": "1.6.1"
  }
}
```

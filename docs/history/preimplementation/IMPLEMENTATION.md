> Historical pre-implementation design snapshot. Its planned/not-run statements
> describe the earlier package. See [implemented v2 scope](../../V2_IMPLEMENTED.md)
> and [current requirement status](../../REQUIREMENT_STATUS.json) for this release.

# Proposed implementation sequence and code map

The v1 runtime logic is unchanged. Baseline file identities and documentation changes are recorded in `baseline.json`. The following modules are implementation destinations. They have not been created as empty capability placeholders. The only new executable code is specification validation and a bounded admission reference-model checker.

## R0. Design and bounded-model verification

Deliver the researched pain map, normative contracts/requirements, independent acceptance oracles, experiments, profiles and unresolved release decisions. Validate all references and baseline integrity against the recorded publication edits. Explore the bounded protocol and require deliberately broken guards to yield counterexamples. Publish exact scope and machine output.

R0 completion establishes a reviewable design. It does not complete a runtime upgrade.

## R1. Repair and establish enforceable boundaries

| Existing or proposed destination | Concrete change | Required cases |
| --- | --- | --- |
| `contracts/`, `pipeline.py`, `runtime/governed_runtime.py` | Immutable mode-specific records; finite/range checks; reject malformed required evidence before side effects | R-001, R-006 |
| `neuro/signal_quality.py`, acquisition adapters | Per-channel mandatory exclusions, provenance and qualified-subset handling | R-002 to R-005 |
| `intent/intent_parser.py`, `governance/permission.py` | Exact declared grammar, conflicting/negated-command rejection, exact safe capabilities and independent veto path | R-012 |
| `runtime/`, endpoint boundary | Action-bound, expiring single-use permits; current capability/policy/state checks at dispatch | R-013 |
| `pipeline.py`, `assurance/`, `lifecycle/` | Prepare ordinary commits before side effect; failure/unknown outcome and restart recovery | R-014 |
| `neuro/task_planner.py`, `cognition/` | Explicit prerequisites, pause versus defer semantics, dependent permit cancellation | R-015 |
| `neuro/session_analyzer.py` | Finite positive window/step validation and at least one step sample | R-001, baseline F13 |
| `replay/`, `runtime/reality.py`, memory | Feedback/policy/world-state capture and precise outcome states | R-029, R-032, R-033 |
| Compatibility surfaces | Correct or retire broken advertised methods; prevent bypass routes from being described as governed | Baseline audit and public API regression |

Keep the existing test cases, then replace weak smoke-only assertions where the documented behavior requires a specific outcome. Add the actual independent actuator/endpoint spies and error recovery checks from the catalog. A denied decision must be tested for absence of the relevant side effect, not just a status string.

Exit: original functionality is verified; all baseline F01-F14 issues have implemented, tested resolutions or explicitly narrowed compatibility scope; fresh release metadata matches the release artifact. Do not delete a failing scientific/control requirement to obtain green CI.

## R2. Real-data evaluation and qualified inference

Implement dataset/run/trial identity, pinned optional scientific I/O and MOABB adapters. Store source licenses and hashes without repackaging restricted data. Add independent train/calibration/evaluation partitions and overlap/duplicate checks. Preserve task and modality semantics.

Build compatible spatial-filter/linear, covariance and compact neural baselines. Evaluate a limited optional advanced encoder or transformed-ensemble adapter only after baselines. Record resources and artifact identities. Do not download arbitrary weights from a mutable URL into the action process.

Implement supported intent evidence, explicit no-command states and temporal dependence. These are task-specific models. Do not create a nominal `UniversalDecoder` interface whose name implies physiological generalization.

Exit: E01, E02 and E07 produce reproducible, correctly scoped reports with all relevant unresolved parameters fixed before final evaluation. Statistical/claim review remains required in addition to automated numerical checks.

## R3. Useful local interaction and independent control simulation

Add `access/` for selectable targets, draft/correction, cancellation, configurable assistance and input-transition interaction. Use clear operational states and accessible controls. Keep engineering details out of normal task flow. The first endpoint is local/simulated.

Add `simulation/` with independent task/plant state, disturbance generation and observation/outcome truth. Replace registered symbolic risk fixtures as the sole control evidence with a bounded dynamics/recovery model for that environment. Retain symbolic actions as explicit task-level state transitions.

The planner offers bounded candidates and clarification/progress choices. The independent executor consumes permits. Physical fallback is an actual simulated controller with acknowledged outcomes; it is not a printed recommendation.

Exit: E04/E05 and local portions of E03/E09 compare useful progress with direct/fixed/always-abstain controls. No live external endpoint is enabled by this stage alone.

## R4. Adaptation, privacy, isolation and robustness

Extend `adaptation/` to immutable candidate artifacts, shadow evaluation, promotion, expiry and full-set rollback. Track label/feedback lineage. Require a locked audit protocol or appropriate sequential evaluation. Simulate both decoder and user changes without claiming the simulation represents all learning.

Add `workers/` with bounded typed IPC, enforced isolation profiles and separate credentials. A proposal worker never owns the actuator. Add `privacy/` for explicit retention and export decisions, and ensure run capsules declare omissions.

Test LLM/context assistance only as an unprivileged optional proposal path. Preserve machine suggestion, neural evidence and exact approval identity. Use actual model logits for attribution experiments only when supported; otherwise label attribution unavailable.

Exit: E06/E08/E09 and relevant numerical robustness tests pass their specified scopes. Supervised semantic updates, unsupervised alignment, software privacy and adversarial robustness claims remain separate.

## R5. Intended-user co-design and digital pilot

Do not assume published preferences validate this interface. Recruit through an appropriate authorized collaboration and study process. Choose a narrow cohort, meaningful tasks and a comparison with each person's actual existing access method. Include caregivers where appropriate without erasing user preferences.

Resolve accessible stop, starting and recovery methods individually. Evaluate manual, assisted and bounded automation rather than forcing a single level. Measure failed starts, total calibration/correction/support effort and participant-reported control. Publish individual variability and withdrawals.

Digital pilot endpoints require explicit allowlists, scope, consequences, approval identity and recovery behavior. Nothing in this design authorizes sending a message, account operation or purchase through a live account.

Exit: E03 and relevant E10 observations support only the evaluated cohort/tasks, with limitations. A negative usefulness result must be allowed to change the product direction.

## R6. Hardware-specific and sustained use

For any physical integration, supply independent hardware timing, plant/estimator/actuator bounds and a tested baseline path. A suitably qualified hardware engineering and participant program is necessary. The repository alone cannot establish implant longevity, safe motion or clinical benefit.

Longitudinal continuation needs a support owner, compatible asset/version policy, local operation limits, recovery/migration and data access. A promise of indefinite support without infrastructure would be misleading. Record actual continuation and reasons for nonuse.

## Dependency and language decisions

- Keep Python for data, research, orchestration and simulation. Profile the intended platform before extracting a narrow executor/service into Rust or C++.
- Use pinned optional MNE/MOABB/pyRiemann or neural dependencies for the experiments that need them. Keep the small action/evidence core independent of every training stack.
- Use established cryptographic primitives. Design identities, key ownership, freshness and retention explicitly; do not implement a novel signature scheme.
- Third-party code, data and weights have separate licenses/attribution obligations. This package adds no external model weights or borrowed implementation.
- Choose model/checkpoint and framework versions during the actual implementation, record them with results, and test compatibility. Current documentation URLs are research references, not immutable dependency pins.

## Review decisions still required

Application thresholds, hardware budgets, modality availability, accessible interaction choices, sample-size/precision plans and physical envelopes remain explicit unresolved blockers in `profiles.json`. The implementation team must resolve the relevant decisions with evidence. These blockers identify missing scientific or engineering inputs.

Progress is measured by working, reviewable stage deliverables and evidence. A complex architecture should be simplified when experiments show a simpler method serves users better.


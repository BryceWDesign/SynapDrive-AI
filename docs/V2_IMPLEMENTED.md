# Implemented v2.0.0 scope

This is a working software research release. It is not completion of every requirement
in the original design. No original acceptance protocol is silently relabeled passed:
the release has a new scoped behavioral suite and explicit offline-data/simulation results.
The complete 40-row mapping is in `REQUIREMENT_STATUS.json`.

## Baseline audit resolution

| Finding | Implemented response | Scope/limit |
| --- | --- | --- |
| F01 Numeric admission | Finite typed/range checks and strict JSON before actions | Canonical trusted simulation API |
| F02 Act then crash | Required source/input contracts before action; prepared dispatch journal | Arbitrary custom endpoints still need their own valid outcome contracts |
| F03 Distribution mismatch | Exact action/distribution checks; input cannot lower derived uncertainty | Intent semantics remain a scientific question |
| F04 Quality faults pass | Mandatory per-channel exclusion with conservative whole-window rejection | No automatic channel-subset decoder |
| F05 Circular stress oracle | Independent expected-outcome labels and clean controls | No general detector adequacy claim |
| F06 Unenforced provenance | Neural fields required; exact artifact/acquisition identity in v2 decoder | Same-process inputs/configuration remain trusted, not externally authenticated |
| F07 Stop/negation | Exact grammar and independent operator veto/stop API | Physical emergency stop outside scope |
| F08 Safe-name loophole | Exact safe action identifiers | Custom actions cannot gain safe status by substring |
| F09 Lost feedback replay | Supported capsules restore feedback, policy, permissions, guard, world and plant | Custom callbacks and raw-signal reacquisition explicitly unsupported |
| F10 Weak qualification | Disjoint fixed recorded-data split, no post-audit refit, exact model/acquisition checks | Legacy trial-split adapter retained and explicitly narrowed |
| F11 Simplex binding | Reassess current runtime and dispatch with bound permit; actual 1D baseline controller | Not a safety proof for arbitrary plants |
| F12 Freeze continues | Freeze pauses, explicit prerequisites and independent-step defer | Simple sequential dependency model |
| F13 Nonadvancing windows | Finite positive durations and at least one sample per advance | Tested invalid and sub-sample settings |
| F14 Overstated assurance | Unconfirmed memory, delayed retraction, goal-score check and signed completeness checkpoint | User acceptance is not clinical ground truth |

The compatibility classifier method indentation is repaired. LSL observations now retain
acquired timestamps; sensor clock authentication and live hardware tests remain external.

## Executable modules

- `runtime/validation.py`, `runtime/dispatch.py`: finite contracts, permits and journal.
- `decoding.py`, `acquisition.py`, `recorded_eeg.py`: actual train/calibrate/evaluate/infer
  and exact-identity/fresh-window admission.
- `access.py`: local drafts, suggestions, user preferences, input transition,
  sequential confirmation and privacy/export handling.
- `adaptation/decoder_updates.py`, `adaptation/lifecycle.py`: exact model candidate
  evaluation, consumed audits, promotion and feedback-dependent rollback.
- `simulation.py`: independent state integrator, braking and canonical endpoint.
- `cognition/clarification.py`: bounded common progress or clarification proposals.
- `replay/recording.py`, `assurance/checkpoint.py`: contextual replay and externally
  retained signed run commitments.
- `v2.py`, `scripts/validate_release.py`: runnable local demonstration and independent
  software/fault/plant/concurrency validation.

## Remaining gaps that prevent broader claims

The EEG experiment admits three incorrect actions among seven admitted actions.
Most epochs abstain; useful reliable access is unestablished. More data, model and
protocol work are necessary before any claim of dependable neural control.
No intended-user study, physical hardware integration, physiological co-adaptation
validation, automated degraded-channel selection, OS sandbox, or long-term support
service is delivered. Application-level privacy cannot protect against a compromised
account/OS. The local task workspace is not an external communications application.

Historical source audit/design records under `docs/history/preimplementation` remain snapshots of the earlier
package; their old planned statuses and hash expectations do not describe the current
implementation. Current executable tests and reports take precedence for release behavior.

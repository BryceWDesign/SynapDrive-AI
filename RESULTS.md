# Measured results and remaining gaps

This release is executable research software. The entire earlier 40-requirement design
has not been completed. A feature inventory is not evidence of dependable neural access.

## Software verification

- 225 tests passed, zero failures/errors/skips.
- Ruff passed; Pyright reported zero errors and warnings.
- Statement coverage 73.32%; branch coverage 57.04%; combined 70.21%.
- 120 independent fault cases passed, including mandatory clean acceptance controls.
- 933 independently integrated recoverable plant scenarios stopped inside their declared
  envelope. This tests a bounded 1D model with known assumptions, not real machinery.
- 800 cycles across eight threads retained one action and cycle record per successful
  operation. The ledger verified. Timing is machine-dependent and is in the JSON report.
- Source distribution and wheel built. Installed-wheel demo, EEG evaluation, recording,
  rejection-feedback replay and replay-evidence verification passed outside the checkout.

## Recorded scalp EEG

Eight prespecified participants, three fixed runs each, 720 total epochs: 240 training,
240 calibration and 240 evaluation epochs. Mean held-out-run three-class balanced
accuracy was 49.52%, with participant-bootstrap 95% interval 42.92–56.32%.
Two subject models passed the configured local gates. Complete runtime admission
produced 7 actions, 4 correct and 3 incorrect, while abstaining on 233 epochs.
No rest epoch was admitted in this experiment. An always-abstain policy also has zero
false activations, so that fact alone is not evidence of usefulness.

This does not solve general neural decoding, cross-session transfer or useful sustained
access. The local numerical qualification policy is permissive research configuration,
not an assurance of dependable control. Thresholds/model choice were not changed to
conceal the observed failures. Rest annotations do not establish asynchronous idle
behavior in daily use. The source cohort does not validate a disability-specific interface.

## Unfinished scope

Automatic qualified channel-subset operation, OS-enforced experimental-worker isolation,
physiological co-adaptation stability experiments, accessible intended-user/caregiver
studies, live external output endpoints, physical integration and sustained deployment
support remain incomplete. Existing privacy is application-level handling under a trusted
OS/account. Current replay reconstructs supported decisions and the built-in plant,
not original sensor acquisition or arbitrary user callbacks.

`docs/REQUIREMENT_STATUS.json` maps all 40 original requirements to scoped implementation,
partial work or explicit gaps. The original acceptance protocols are not relabeled passed.
Current software verification and neural/control readiness are separate release fields.

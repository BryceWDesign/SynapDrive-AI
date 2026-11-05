# Architecture: executable v2.0.0

The canonical trusted simulation API is `SynapDrivePipeline`. Input records pass
strict finite/type/size validation before optimization, uncertainty computation,
policy, permission, quality, drift and registered-world checks. Admission creates
an action/policy/capability/world-bound single-use permit. The executor journals a
prepared record before calling its endpoint and records the observed outcome.
Unresolved dispatches block future ordinary work until explicitly reconciled.

The default endpoint logs simulated actions. `PlantEndpoint` connects the independent
1D integrator and braking monitor to this same pipeline. Rejected cycles invoke a
configured baseline controller and retain its reported result. Emergency stop uses a
separate trusted operator API; it bypasses ordinary journal availability and latches
future dispatch off. It does not preempt an arbitrary running Python callback or
replace a physical emergency-stop circuit.

The EEG path is `EEGDecoder`: fixed filtering, training-only CSP and shrinkage LDA,
separate temperature calibration, a disjoint held-out evaluation, exact artifact
qualification, and optional fresh-window admission by `StreamDecoder`. Acquisition
identity includes ordered channels, units, reference, preprocessing, epoch length,
sampling rate, modality and source device. The bundled profile identifies the
recorded dataset; applying it to another device fails identity matching. A live
integration needs its own measured acquisition contract and qualification data.

`AccessSession` retains user-selected assistance scope, proposes explicit input
transitions, requires distinct supported windows for sequential confirmation, and
separates decoded evidence, suggestions, drafts and approved local output. Private
mode keeps content in volatile process memory and forbids export. Audited/research
exports require separate explicit consent; content is omitted or encrypted with a
caller-owned Fernet key. This is application-level data handling, not protection
against a compromised OS or arbitrary code in the same process.

`DecoderUpdates` owns evaluation of exact candidate models. `ModelLifecycle` records
parent/feedback lineage, consumes independent audit identities and gates promotion.
Delayed contradictions can retract memory and roll back promoted descendants. This
is supervised software lifecycle control, not a demonstrated solution to biological
co-adaptation.

Replay capsules retain the trusted simulation decision context, feedback and built-in
plant state. Replay compares behavioral summaries and refuses divergence. Custom
fallback callbacks cannot be serialized and are explicitly marked unsupported.
Detached signed checkpoints bind ledger run identity, count and final hash; a retained
checkpoint and trusted public key are necessary to establish completeness. Ledger
integrity does not establish scientific truth.

Python callers, model/configuration loaders and the operating account remain trusted.
No experimental model gets an implicit live endpoint. OS-level process isolation is
not implemented. Direct low-level router/actuator classes are simulation utilities,
not independent governance boundaries.

> Historical pre-implementation design snapshot. Its planned/not-run statements
> describe the earlier package. See [implemented v2 scope](../../V2_IMPLEMENTED.md)
> and [current requirement status](../../REQUIREMENT_STATUS.json) for this release.

# Requirement and implementation traceability

**Every listed runtime requirement is planned. Every linked runtime acceptance case is not run.** The default design check verifies this catalog's structure, not implementation.

## Planned modules

| ID | Responsibility | Planned code destinations | Boundary |
| --- | --- | --- | --- |
| M01 | Validated observation and timing contracts | `synapdrive_ai/contracts/`; `synapdrive_ai/integrations/`; `synapdrive_ai/neuro/eeg_loader.py` | Acquisition truth is not established by metadata or signatures. |
| M02 | Per-channel integrity and usable-input assessment | `synapdrive_ai/neuro/signal_quality.py`; `synapdrive_ai/neuro/drift.py` | Engineering integrity checks are not neurological diagnoses. |
| M03 | Qualified decoding and temporal intent evidence | `synapdrive_ai/benchmarking/`; `synapdrive_ai/intent/belief.py`; `synapdrive_ai/neuro/uncertainty.py` | A supported class is a hypothesis, not proof of true intent. |
| M04 | Accessible interaction and assistance negotiation | `synapdrive_ai/access/`; `synapdrive_ai/cognition/shared_autonomy.py` | No universal interface or preferred assistance level is assumed. |
| M05 | Independent action admission and execution protocol | `synapdrive_ai/governance/`; `synapdrive_ai/runtime/`; `synapdrive_ai/pipeline.py` | Atomic dispatch assumptions and in-flight effects must be explicit. |
| M06 | Bounded task planning and plant-specific recovery | `synapdrive_ai/cognition/`; `synapdrive_ai/simulation/`; `synapdrive_ai/neuro/task_planner.py` | Simulation constraint satisfaction is not physical safety certification. |
| M07 | Qualified adaptation and user-model interaction | `synapdrive_ai/adaptation/`; `synapdrive_ai/runtime/shadow.py` | No promotion from self-generated semantic labels alone. |
| M08 | Privacy, authorship and isolated proposal workers | `synapdrive_ai/privacy/`; `synapdrive_ai/access/communication.py`; `synapdrive_ai/workers/` | Integrity, privacy and intended meaning are separate properties. |
| M09 | Replay capsules and lifecycle recovery | `synapdrive_ai/replay/`; `synapdrive_ai/assurance/`; `synapdrive_ai/lifecycle/` | Private data omitted from a run cannot later be reconstructed for exact replay. |
| M10 | Independent evaluation and failure analysis | `synapdrive_ai/benchmarking/`; `synapdrive_ai/stress/`; `benchmarks/v2/` | Offline, simulated, hardware, human and deployment evidence remain distinct. |

## Requirements

| ID | Requirement | Stage / evidence | Pain points | Planned modules | Acceptance case | Audit findings | Prerequisites |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R-001 | Strict mode-specific input contracts | R1 / software | P04, P12 | M01, M05 | T-001 | F01, F02, F06, F13 | None |
| R-002 | Acquisition and processing identity | R1 / software | P03, P04 | M01, M03 | T-002 | F10 | R-001 |
| R-003 | Timing and observation freshness | R1 / software | P04, P08 | M01, M05 | T-003 | F06 | R-001 |
| R-004 | Per-channel exclusions and usable subsets | R1 / software | P03, P04 | M02, M03 | T-004 | F04 | R-001, R-002 |
| R-005 | Independent fault outcomes | R1 / software | P04, P10 | M02, M10 | T-005 | F05 | R-001, R-004 |
| R-006 | Consistent decoder evidence | R1 / software | P02, P06 | M03, M05 | T-006 | F03 | R-001 |
| R-007 | No-command and engagement states | R2 / offline_data | P01, P02, P11 | M03, M04, M05 | T-007 | New design requirement | R-002, R-004, R-006 |
| R-008 | Grouped immutable qualification | R2 / offline_data | P03, P10 | M03, M10 | T-008 | F10 | R-001, R-002 |
| R-009 | Qualification binds deployed artifact | R1 / software | P03, P14 | M03, M07, M09 | T-009 | F10 | R-001, R-002 |
| R-010 | Calibration and selective risk | R2 / offline_data | P02, P03 | M03, M10 | T-010 | New design requirement | R-008, R-009 |
| R-011 | Decoder family and resource comparison | R2 / offline_data | P01, P13 | M03, M10 | T-011 | New design requirement | R-008, R-010 |
| R-012 | Exact capabilities and independent veto | R1 / software | P02, P06, P08 | M04, M05 | T-012 | F07, F08 | R-001 |
| R-013 | Immutable action permits | R1 / software | P06, P12 | M05 | T-013 | F06, F08, F11 | R-001, R-003, R-009, R-012 |
| R-014 | Pre-dispatch durability and bounded audit failure | R1 / software | P09, P12 | M05, M09 | T-014 | F02, F09 | R-013 |
| R-015 | Task prerequisite enforcement | R1 / software | P06, P08 | M06, M05 | T-015 | F12 | R-013 |
| R-016 | Recoverability before fallback switching | R3 / simulation | P08 | M06, M05 | T-016 | F11 | R-003, R-005, R-013, R-015 |
| R-017 | State-dependent fallback and handover | R3 / simulation | P01, P08 | M06, M04 | T-017 | F07, F11 | R-012, R-016 |
| R-018 | Bounded assistance with original goal retained | R3 / simulation | P01, P06 | M04, M06 | T-018 | F14 | R-013, R-015 |
| R-019 | Clarification and compatible progress hypothesis | R3 / simulation | P01, P02, P06 | M03, M04, M06 | T-019 | New design requirement | R-007, R-010, R-018 |
| R-020 | User-selected automation scope | R5 / human_study | P05, P06, P14 | M04, M05 | T-020 | New design requirement | R-012, R-018, R-037 |
| R-021 | Adaptive input continuity | R3 / simulation | P01, P04, P05 | M01, M03, M04, M09 | T-021 | New design requirement | R-002, R-004, R-009, R-012, R-032 |
| R-022 | Accessible setup and self-recovery | R5 / human_study | P01, P05 | M04, M09 | T-022 | New design requirement | R-021, R-037 |
| R-023 | Transparent communication stages | R3 / simulation | P06, P11 | M04, M08 | T-023 | New design requirement | R-012, R-013, R-024 |
| R-024 | Explicit privacy modes | R1 / software | P11, P14 | M04, M08, M09 | T-024 | New design requirement | R-012, R-013 |
| R-025 | Safe content retention and honest replay limits | R1 / software | P09, P11 | M08, M09 | T-025 | New design requirement | R-024, R-032 |
| R-026 | Isolated proposal workers | R1 / software | P12, P13 | M05, M08 | T-026 | New design requirement | R-001, R-013, R-034 |
| R-027 | Artifact and input threat boundaries | R1 / software | P12, P14 | M01, M07, M08, M09 | T-027 | New design requirement | R-002, R-009, R-013 |
| R-028 | Controlled decoder-update lifecycle | R4 / offline_data | P03, P07 | M03, M07, M09 | T-028 | New design requirement | R-009, R-029, R-031, R-032 |
| R-029 | Label and feedback provenance | R4 / software | P06, P07, P09 | M04, M07, M09 | T-029 | F09, F14 | R-001, R-032 |
| R-030 | Co-adaptation stability experiments | R4 / simulation | P01, P07 | M07, M10 | T-030 | New design requirement | R-028 |
| R-031 | Locked audit data and adaptive-selection control | R4 / offline_data | P07, P10 | M07, M10 | T-031 | New design requirement | R-008, R-010 |
| R-032 | Complete versioned run capsules | R1 / software | P09, P10 | M09 | T-032 | F09 | R-001 |
| R-033 | Independent evidence completeness verification | R1 / software | P09, P12 | M09, M10 | T-033 | F14 | R-032 |
| R-034 | Bounded resources and local continuity | R1 / software | P01, P13 | M03, M05, M08, M09 | T-034 | New design requirement | R-003, R-012 |
| R-035 | Defensive numerical robustness without inflated security claims | R4 / offline_data | P03, P12 | M02, M03, M10 | T-035 | New design requirement | R-004, R-008, R-026, R-027 |
| R-036 | Useful access and denominator integrity | R5 / human_study | P01, P05, P10 | M04, M10 | T-036 | New design requirement | R-007, R-008, R-020, R-022, R-023 |
| R-037 | Versioned user preferences and constrained caregiver roles | R1 / software | P05, P06, P14 | M04, M05, M09 | T-037 | New design requirement | R-009, R-012 |
| R-038 | Evidence classification and honest release status | R1 / software | P10, P15 | M10, M09 | T-038 | New design requirement | R-032, R-033 |
| R-039 | Cross-modality and cohort boundaries | R2 / software | P03, P10, P15 | M01, M03, M10 | T-039 | New design requirement | R-002, R-008 |
| R-040 | Deployment and support continuity | R1 / software | P01, P05, P14 | M09, M04, M10 | T-040 | New design requirement | R-009, R-032, R-034, R-037 |

Normative statements, procedures and independent expected outcomes are in `requirements.json` and `acceptance_tests.json`. The prerequisite graph is acyclic and checked by the design validator. Human, hardware and data evidence cannot be replaced by creating a corresponding test filename.

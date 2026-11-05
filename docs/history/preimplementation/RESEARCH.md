> Historical pre-implementation design snapshot. Its planned/not-run statements
> describe the earlier package. See [implemented v2 scope](../../V2_IMPLEMENTED.md)
> and [current requirement status](../../REQUIREMENT_STATUS.json) for this release.

# Research, critical problems and design decisions

**Research cutoff: 2 November 2026.** This is a targeted review of primary studies and official scientific-tool documentation. It is not an exhaustive systematic review, a prevalence-based ranking, or validation that intended users want this implementation.

## Method and interpretation

The review covered lived-experience preferences and home use; idle-state errors; session/device/processing drift; decoder and user co-adaptation; resource-efficient and foundation-model inference; shared autonomy and authorship; neural privacy and adversarial robustness; timing, metadata and runtime assurance. The baseline source audit is separate software evidence. It grounds repairs but does not establish how common each failure is in deployed systems.

Primary results are used only within their modality, population, task and protocol. Accepted manuscripts and preprints are labeled. Official documentation supports integration choices, not physiological or clinical claims. News coverage and unverified secondary summaries were not used to establish technical capabilities. Review papers helped discover topics but are not the basis of the technical findings catalog.

Current and emerging identifies already observed or plausible growing failure modes associated with adaptation, richer assistance and deployment. It is not a prediction that a specific future product or risk will occur on a particular date. Intracortical inner-speech results are not evidence for unrestricted thought reading or scalp-EEG language decoding.

## Prioritized pain-point map

Priority reflects consequence to useful control, evidence, and software tractability. It is an engineering decision that should be revisited through user participation and experiments.

| ID | Problem and priority | Horizon | Evidence | Proposed response |
| --- | --- | --- | --- | --- |
| P01 | Loss of communication or computer access during ordinary daily use (critical) | current | S01, S02, S04, S05 | Preserve usable access through explicit degradation, recovery and alternative input; measure useful independent task time. |
| P02 | Unintended commands during idle or ambiguous transitions (critical) | current | S03, S09, S15, S23, S27 | Explicit no-command state, engagement, veto and consequence-dependent commit rules. |
| P03 | Session, device, montage or preprocessing shift (critical) | current_and_emerging | S06, S07, S10, S11, S19, S20 | Identity-bound qualification, drift diagnosis, expiry, bounded recalibration and rollback. |
| P04 | Sensor or timestamp faults mistaken for valid intent (critical) | current | S20, S21, S22 | Finite data, channel-specific hard exclusions, timing bounds and decoder-required channel contracts. |
| P05 | Caregiver, setup, correction and support burden (high) | current | S01, S03, S04, S05 | Accessible setup/recovery, versioned profiles, understandable failure states and burden metrics. |
| P06 | Machine assistance overrides or misrepresents the person (critical) | current_and_emerging | S05, S13, S14, S16, S25 | User-selected assistance scope, proposal/approval separation, exact commit identity and correction. |
| P07 | Unstable or contaminated adaptation (critical) | current_and_emerging | S06, S07, S08, S12, S17 | Separate learning and control timescales; shadow, label provenance, locked audit data and rollback. |
| P08 | Fallback selected too late or unsuitable for the plant (critical) | current | S18, S21 | Model recoverability, deadline/uncertainty bounds and an independently supervised baseline controller. |
| P09 | Incomplete replay, asynchronous feedback or crash recovery (critical) | current_and_emerging | S04, S19, S20, S21 | Versioned capsules, pre-dispatch/outcome records, pending feedback and idempotent endpoint recovery. |
| P10 | Evaluation leakage and misleading generalization claims (high) | current | S09, S10, S19, S23, S26 | Group before epoching, lock splits, quantify clustered uncertainty and distinguish evidence levels. |
| P11 | Neural privacy and sensitive content exposure (critical) | current_and_emerging | S01, S04, S15, S16 | Explicit privacy modes, output lock, local processing and content retention controls. |
| P12 | Malicious or compromised model, worker or data path (critical) | current_and_emerging | S17, S18, S20 | Typed bounded IPC, isolated proposal workers, artifact verification, revocation and limited threat claims. |
| P13 | Compute, power or network limits destroy availability (high) | current_and_emerging | S01, S10, S12, S26 | Local compact baseline, bounded queues, cancellation, explicit resource profiles and no required cloud path. |
| P14 | Evidence expiry as abilities, preferences and deployment change (high) | current_and_emerging | S01, S04, S05, S06, S20 | Versioned user profiles and dependency invalidation; continuation/support and export design. |
| P15 | Ambition exceeds what software can establish (high) | current_and_emerging | S02, S04, S15, S18, S23 | Explicit external-evidence gates and cohort/modality/plant limits; do not disguise absence as performance. |

## What changes the update design

**Availability becomes a primary outcome.** Access continuity, failed starts, correction/recalibration and caregiver effort are measured alongside task accuracy. A functional interface, portable preferences and useful recovery are part of the research system. Published preferences motivate co-design; they do not substitute for it.

**Automation is a user choice within supported limits.** Some configurations benefit from substantial automation. The system offers manual, assisted and bounded-task scopes, then measures workload and perceived control rather than equating agency with fewer automated actions.

**Qualification is conditional and expires.** Model confidence cannot detect every montage, clock, action-map, user-profile or policy change. The update tracks these dependencies and invalidates affected authority while preserving genuinely independent usable functions.

**The decoder is only one learner.** Adaptation is tested with changing user strategies, delayed corrections and the consequences of assistance. Unsupervised transformations are not assumed to preserve semantics, and model output is not trusted ground truth.

**Assistance must preserve intended output.** Candidate text, language-prior suggestions, revisions and exact approved output remain distinguishable. A fluent response cannot authorize a message. Computational attribution does not establish mental meaning.

**Privacy is operational.** Lock, processing, recording, training and export are separately scoped. Private-mode data omissions are recorded as replay limitations; encryption and signatures are not described as privacy or sensor-truth guarantees.

**Physical assurance has a model and a clock.** A baseline controller must actually respond before modeled recoverability is lost. Independent environment truth, delays and actuator acknowledgments replace a success flag from a mock actuator as control evidence.

## Falsifiable advanced hypotheses

| Hypothesis | Proposed comparison | Failure that would change the design |
| --- | --- | --- |
| H01: authorized common progress can reduce clarification burden | E04, matched command risk and task complexity | Wrong-goal commitment, oracle intent dependence, or no gain after matching burden |
| H02: dependency-aware expiry preserves more useful access than a global reset | E02 and E10, exact dependency scopes | Invalid authority remains usable or selective invalidation is too complex/unreliable |
| H03: bounded adaptation and slower updates outperform aggressive self-updating over time | E06, chronology and locked audit data | Benefit relies on pseudo-ground-truth, repeated-holdout tuning, or greater unusable time |
| H04: privacy-compatible minimal records support useful accountability | E08/E09, locked/private/audited modes | Forbidden content leaks or records imply exact replay that they cannot provide |

These are proposed integration experiments. The design does not assert that their constituent concepts are novel, that these exact combinations have never been tried, or that the experiments will favor them.

## Problems software cannot solve alone

Implant longevity, biocompatibility, electrode stability, usable signal availability, physical actuator behavior, cost of acquisition hardware, sustained service and clinical benefit require evidence outside this repository. Software can detect some failures, constrain behavior, preserve state and request qualified help; it cannot manufacture a usable neural signal or certify a physical device. These dependencies remain explicit gates rather than being hidden behind a working simulation.

## Source catalog

Source IDs are referenced throughout the architecture and machine-readable requirements. Finding, limitation and design inference are intentionally distinct.

### S01. Patient preferences for implantable BCIs in motor neuron disease

Type: `accepted_manuscript`. Publication: 2026-05-01. Accessed: 2026-11-02.

Source: [Patient preferences for implantable BCIs in motor neuron disease](https://preprints.jmir.org/preprint/82142/accepted)

**Supported finding:** A survey with 39 respondents emphasized useful functions, ease, accuracy, reliability, and support.

**Limit:** 32 completed the survey. Stated preferences do not demonstrate adoption or benefit from this repo.

**Design inference:** Prioritize useful access and sustained support; measure setup, training, and support burden.

### S02. Patient perspectives after high cervical spinal cord injury

Type: `peer_reviewed_primary`. Publication: 2026-06-22. Accessed: 2026-11-02.

Source: [Patient perspectives after high cervical spinal cord injury](https://pubmed.ncbi.nlm.nih.gov/42332942/)

**Supported finding:** A four-person focus group described desired digital independence and practical usability concerns.

**Limit:** Small qualitative cohort; preferences are not population-wide estimates.

**Design inference:** Use communication and computer access as a co-design candidate; preserve individual preferences.

### S03. BCI priorities of potential users with spinal cord injury

Type: `peer_reviewed_primary`. Publication: 2015. Accessed: 2026-11-02.

Source: [BCI priorities of potential users with spinal cord injury](https://pubmed.ncbi.nlm.nih.gov/25721546/)

**Supported finding:** A 40-person survey identified useful functions, emergency communication, and simple setup as priorities.

**Limit:** Older convenience sample; desired performance is not a universal release threshold.

**Design inference:** Measure idle errors, setup and access to a help request; never make the prototype a sole emergency channel.

### S04. Long-term independent intracortical speech and cursor BCI use

Type: `peer_reviewed_primary`. Publication: 2026-06-15. Accessed: 2026-11-02.

Source: [Long-term independent intracortical speech and cursor BCI use](https://pmc.ncbi.nlm.nih.gov/articles/PMC13375540/)

**Supported finding:** One participant used a multimodal implanted system at home for over 3,800 hours with interface and decoder support.

**Limit:** Intracortical single-participant evidence; it does not establish scalp-EEG performance or this repo's capability.

**Design inference:** Treat interface, calibration, corrections, privacy and support as part of the system; distinguish task accuracy from natural use.

### S05. Personalized adaptable speech and cursor BCI interface, CHI 2026

Type: `peer_reviewed_primary`. Publication: 2026-04-13. Accessed: 2026-11-02.

Source: [Personalized adaptable speech and cursor BCI interface, CHI 2026](https://doi.org/10.1145/3772318.3790750)

**Supported finding:** A 22-month co-design deployment with one participant was adapted to a second participant.

**Limit:** Small deployment; may overlap the home-use cohort in S04. Do not count these as independent large cohorts.

**Design inference:** Make interface preferences versioned, exportable and revisable through accessible controls.

### S06. EDAPT continual online adaptation

Type: `peer_reviewed_primary`. Publication: 2026-04-07. Accessed: 2026-11-02.

Source: [EDAPT continual online adaptation](https://doi.org/10.1088/1741-2552/ae5689)

**Supported finding:** Population pretraining and supervised trial-wise updates improved evaluated decoding across several datasets.

**Limit:** Uses revealed labels; offline/open-loop evidence does not establish autonomous closed-loop benefit.

**Design inference:** Evaluate supervised personalization with chronological labels and guarded artifact promotion.

### S07. NoMAD latent-dynamics alignment for BCI stability

Type: `peer_reviewed_primary`. Publication: 2025-05-19. Accessed: 2026-11-02.

Source: [NoMAD latent-dynamics alignment for BCI stability](https://www.nature.com/articles/s41467-025-59652-y)

**Supported finding:** Temporal latent alignment improved stability in the studied intracortical decoding settings.

**Limit:** Representation assumptions and recording modality matter; unsupervised alignment cannot prove semantic label correctness.

**Design inference:** Include alignment as a separately qualified research adapter and monitor loss of correspondence.

### S08. Co-adaptive user and decoder interactions

Type: `peer_reviewed_primary`. Publication: 2026-03-23. Accessed: 2026-11-02.

Source: [Co-adaptive user and decoder interactions](https://doi.org/10.1038/s42256-026-01194-z)

**Supported finding:** Control/game-theoretic analysis was evaluated with 14 people using an adaptive myoelectric interface.

**Limit:** EMG study; learning-rate results cannot be assumed to transfer to EEG or impaired populations.

**Design inference:** Separate control and adaptation timescales and test interacting learner dynamics.

### S09. Cross-session conformal command gating

Type: `peer_reviewed_primary`. Publication: 2026-10-23. Accessed: 2026-11-02.

Source: [Cross-session conformal command gating](https://pubmed.ncbi.nlm.nih.gov/42805221/)

**Supported finding:** Selective gates reduced erroneous decisions at the cost of decisiveness in cross-session motor imagery experiments.

**Limit:** Session shift challenges exchangeability; empirical coverage is not an unconditional safety guarantee.

**Design inference:** Compare gates at matched coverage and risk, with independent calibration and shift monitoring.

### S10. EEG-FM-Compass foundation model benchmark

Type: `peer_reviewed_primary`. Publication: 2026-08-03. Accessed: 2026-11-02.

Source: [EEG-FM-Compass foundation model benchmark](https://doi.org/10.1093/nsr/nwag466)

**Supported finding:** A comparative benchmark found specialists competitive and model scale alone insufficient for universal transfer.

**Limit:** Conclusions depend on protocols, tasks, and training regimes; no blanket verdict on every model.

**Design inference:** Require compact baselines and resource-aware comparisons before promoting a foundation encoder.

### S11. Preprocessing-dependent EEG prediction instability

Type: `preprint`. Publication: 2026-05-08. Accessed: 2026-11-02.

Source: [Preprocessing-dependent EEG prediction instability](https://arxiv.org/abs/2605.07212)

**Supported finding:** The authors investigated how plausible preprocessing changes can alter predictions despite fixed model confidence.

**Limit:** Preprint and studied intervention space; does not validate a universal preprocessing-uncertainty estimator.

**Design inference:** Bind preprocessing identity and run a bounded sensitivity audit before qualification.

### S12. Backpropagation-free transformations for EEG adaptation

Type: `peer_reviewed_primary`. Publication: 2026-08-19. Accessed: 2026-11-02.

Source: [Backpropagation-free transformations for EEG adaptation](https://pubmed.ncbi.nlm.nih.gov/42616624/)

**Supported finding:** Source-trained ranking of transformed trial predictions supports forward-pass-only adaptation experiments.

**Limit:** The evaluated tasks and computational results do not establish platform-wide latency or clinical transfer.

**Design inference:** Test low-compute transformed ensembles as optional alternatives, with bounded inference budgets.

### S13. EEG BCI control with AI copilots

Type: `peer_reviewed_primary`. Publication: 2025-09-01. Accessed: 2026-11-02.

Source: [EEG BCI control with AI copilots](https://pubmed.ncbi.nlm.nih.gov/41221369/)

**Supported finding:** Shared assistance was demonstrated for cursor and robotic tasks using noninvasive EEG.

**Limit:** Published system-specific results are not results or novelty evidence for SynapDrive.

**Design inference:** Benchmark bounded assistance against direct control and fixed assistance.

### S14. Levels of shared autonomy in multimodal brain-robot interaction

Type: `peer_reviewed_primary`. Publication: 2026. Accessed: 2026-11-02.

Source: [Levels of shared autonomy in multimodal brain-robot interaction](https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2025.1718713/full)

**Supported finding:** A configuration-specific study compared assistance levels and reported workload, usability, reliability and agency tradeoffs.

**Limit:** Multimodal lab configuration; patient-level generalization is not established by this design review.

**Design inference:** Permit user-selected automation scope; do not equate agency with compulsory low automation.

### S15. Inner speech and privacy in motor-cortex neuroprostheses

Type: `peer_reviewed_primary`. Publication: 2025. Accessed: 2026-11-02.

Source: [Inner speech and privacy in motor-cortex neuroprostheses](https://pubmed.ncbi.nlm.nih.gov/40816265/)

**Supported finding:** Four implanted participants supported limited inner-speech decoding experiments and strategies against unintended output.

**Limit:** Not unrestricted mind reading and not scalp EEG evidence; privacy defenses are initial explorations.

**Design inference:** Require explicit engagement and privacy lock independent of model confidence; do not implement private-thought inference.

### S16. Measuring language-prior influence in ALS BCI communication

Type: `preprint`. Publication: 2026-08-20. Accessed: 2026-11-02.

Source: [Measuring language-prior influence in ALS BCI communication](https://www.medrxiv.org/content/10.64898/2026.08.20.26360941v1.full)

**Supported finding:** Retrospective P300 re-decoding separates neural evidence and language-prior contributions to output.

**Limit:** A computational attribution measure cannot establish a person's true meaning or authorship; preprint status.

**Design inference:** Preserve neural, assisted and approved output separately and evaluate prior-only controls when logits are available.

### S17. EEG data-alignment adversarial defense benchmark

Type: `peer_reviewed_primary`. Publication: 2025. Accessed: 2026-11-02.

Source: [EEG data-alignment adversarial defense benchmark](https://pubmed.ncbi.nlm.nih.gov/40334321/)

**Supported finding:** Comparative experiments examine neural-decoder sensitivity to adversarial input and defense choices.

**Limit:** Perturbation robustness in a benchmark does not establish secure acquisition, realistic attacker access, or universal defense.

**Design inference:** Separate bounded numerical robustness tests from transport and process-security threat models.

### S18. NASA runtime-assurance verification framework

Type: `primary_technical_paper`. Publication: 2024. Accessed: 2026-11-02.

Source: [NASA runtime-assurance verification framework](https://ntrs.nasa.gov/citations/20240007986)

**Supported finding:** A formal framework relates advanced control, trusted fallback, plant dynamics and monitoring assumptions.

**Limit:** The framework is not a certification of this software or a proof for an unspecified plant.

**Design inference:** State recoverability and timing assumptions explicitly and validate one bounded plant model first.

### S19. MOABB evaluation and dataset API

Type: `official_documentation`. Publication: live official documentation. Accessed: 2026-11-02.

Source: [MOABB evaluation and dataset API](https://moabb.neurotechx.com/docs/api.html)

**Supported finding:** Provides established dataset, paradigm and within/cross-session/subject evaluation abstractions.

**Limit:** Use a pinned version and declared target-data access; benchmark use alone does not prevent every leakage.

**Design inference:** Add grouped protocols, immutable split manifests and explicit target calibration permissions.

### S20. BIDS EEG metadata specification

Type: `official_documentation`. Publication: live official documentation. Accessed: 2026-11-02.

Source: [BIDS EEG metadata specification](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/electroencephalography.html)

**Supported finding:** Defines EEG metadata for acquisition, channels, electrodes, coordinates and related recording context.

**Limit:** Metadata conformance does not prove correct labeling, valid consent, or scientific comparability.

**Design inference:** Preserve acquisition/coordinate/units metadata rather than reducing identity to channel count.

### S21. LSL time synchronization documentation

Type: `official_documentation`. Publication: live official documentation. Accessed: 2026-11-02.

Source: [LSL time synchronization documentation](https://labstreaminglayer.readthedocs.io/info/time_synchronization.html)

**Supported finding:** Explains source timestamps, clock offsets, synchronization options and online/offline timing treatment.

**Limit:** LSL clocks are not interchangeable with wall clocks; bounds still need measurement.

**Design inference:** Retain timestamps, gaps and clock domains; refuse time-critical operation when age cannot be bounded.

### S22. MNE EDF loader documentation

Type: `official_documentation`. Publication: live official documentation. Accessed: 2026-11-02.

Source: [MNE EDF loader documentation](https://mne.tools/stable/generated/mne.io.read_raw_edf.html)

**Supported finding:** Provides a maintained recording reader with explicit channel and format handling options.

**Limit:** Library use does not guarantee correct event interpretation or preprocessing.

**Design inference:** Use tested optional scientific I/O rather than broadening the custom loader by assumption.

### S23. PhysioNet motor movement and imagery dataset

Type: `primary_dataset`. Publication: 2009-09-09. Accessed: 2026-11-02.

Source: [PhysioNet motor movement and imagery dataset](https://physionet.org/content/eegmmidb/1.0.0/)

**Supported finding:** Provides annotated rest and movement/imagery recordings with run-dependent event semantics.

**Limit:** Cued/rest recordings do not represent every natural no-command state; execution and imagery labels differ.

**Design inference:** Build explicit rest/imagery protocols without converting annotations into unrestricted real-world intent claims.

### S24. pyRiemann minimum-distance-to-mean classifier API

Type: `official_documentation`. Publication: live official documentation. Accessed: 2026-11-02.

Source: [pyRiemann minimum-distance-to-mean classifier API](https://pyriemann.readthedocs.io/en/latest/generated/pyriemann.classification.MDM.html)

**Supported finding:** Defines an established covariance-classification baseline for compatible experiments.

**Limit:** A development documentation URL is not a dependency pin; select a released version for implementation.

**Design inference:** Use a specialist baseline and retain exact library/model/preprocessing versions.

### S25. Shared autonomy via hindsight optimization

Type: `peer_reviewed_primary`. Publication: 2015. Accessed: 2026-11-02.

Source: [Shared autonomy via hindsight optimization](https://publications.ri.cmu.edu/shared-autonomy-via-hindsight-optimization)

**Supported finding:** Models uncertainty over goals and assistance choices, with user-control tradeoffs.

**Limit:** POMDP assistance and uncertainty-aware goal selection are existing prior art.

**Design inference:** Evaluate hypothesis-compatible progress as an extension of the cited methods; no new foundational algorithm is claimed.

### S26. ICLR 2026 comparison of EEG foundation and traditional models

Type: `peer_reviewed_primary`. Publication: 2026. Accessed: 2026-11-02.

Source: [ICLR 2026 comparison of EEG foundation and traditional models](https://proceedings.iclr.cc/paper_files/paper/2026/hash/f0f39b7686634fc81ca0112566b2c05f-Abstract-Conference.html)

**Supported finding:** A multi-protocol comparison found foundation-model advantages dependent on data and evaluation regime.

**Limit:** No model family is a guaranteed winner; exact supported artifacts require separate checks.

**Design inference:** Promote by demonstrated risk/coverage/resource benefit rather than architecture size.

### S27. Periodic and aperiodic features for asynchronous BCI

Type: `accepted_manuscript` (in-press journal article). Online publication: September 2026; retained date precision: year. Accessed: 2026-11-02.

Source: [Periodic and aperiodic features for asynchronous BCI](https://www.engineering.org.cn/engi/EN/10.1016/j.eng.2026.08.025)

**Supported finding:** In-press experiments distinguish control from non-control using periodic/aperiodic evidence in a supported SSVER setting.

**Limit:** Paradigm-specific EEG/OPM-MEG and online task results do not establish a universal idle detector. Online listings give different September dates; year precision is retained.

**Design inference:** Evaluate complementary state evidence only in a separately supported asynchronous paradigm, with false-activation exposure and latency.

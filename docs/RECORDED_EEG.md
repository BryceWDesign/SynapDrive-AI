# Recorded EEG protocol and attribution

Source: Gerwin Schalk (2009), EEG Motor Movement/Imagery Dataset v1.0.0,
PhysioNet, DOI https://doi.org/10.13026/C28G6P .
https://physionet.org/content/eegmmidb/1.0.0/

Contains information from the EEG Motor Movement/Imagery Dataset, made available
under the Open Data Commons Attribution License v1.0:
https://physionet.org/content/eegmmidb/view-license/1.0.0/

Additional references requested by the dataset:
Schalk G, McFarland DJ, Hinterberger T, Birbaumer N, Wolpaw JR. BCI2000:
A General-Purpose Brain-Computer Interface (BCI) System. IEEE Transactions on
Biomedical Engineering 51(6):1034–1043, 2004.
Goldberger AL et al. PhysioBank, PhysioToolkit, and PhysioNet: Components of a New
Research Resource for Complex Physiologic Signals. Circulation 101(23):e215–e220, 2000.

`assets/recorded_eeg.npz` is a transformed subset, not the full original dataset.
It contains subjects S001–S008, runs 04, 08 and 12, nine named channels, one
0.5–3.5 second raw-data epoch for each eligible annotation, float32 samples in volts,
and explicit subject/run/parent-trial identity. No overlapping subwindows are used.
The original recorded EEG labels are task annotations, not proof of a participant's
private intended meaning or of intent in an asynchronous everyday setting.

The fixed protocol uses R04 for training, R08 only for temperature calibration,
and R12 for evaluation. Training-only one-vs-rest CSP spatial filters and shrinkage
LDA are applied to a fixed 8–30 Hz fourth-order filter. Common-average referencing
is over the selected channels. Complete three-second windows are filtered with
`sosfiltfilt`; a live system would therefore wait for the full epoch before inference.

All eight prespecified subjects are reported. There is no model or threshold selection
against the audit labels. The audit does gate qualification of the evaluated exact
artifact; no full-data refit follows it. Permuting training labels is a negative control,
not a p-value. The 95% interval resamples eight participants, so it is imprecise and
is not a clinical confidence guarantee. The dataset is too small for broad claims.

Reproduce without downloading recordings:

```text
python -m synapdrive_ai.v2 eeg --out results/eeg-reproduced
```

Recreate the processed subset from the source EDF+ files (network and MNE required):

```text
python -m scripts.evaluate_recorded_eeg --download --cache ../eeg-cache --dataset synapdrive_ai/assets/recorded_eeg.npz --out results/eeg-recreated
```

`results/EEG_SOURCES.json` lists file URLs, sizes, downloaded hashes and matching official
hashes. The processed dataset hash is in the experiment report. Repeated reproduction
of these known audit labels does not create fresh independent evaluation evidence.

Implementation references: MNE `read_raw_edf`, SciPy `butter`/`sosfiltfilt`/`eigh`,
and scikit-learn `LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")`.
Portable fitted artifacts store numeric arrays and JSON, with no pickle. A checksum
must come from trusted configuration before a loaded artifact retains action qualification.

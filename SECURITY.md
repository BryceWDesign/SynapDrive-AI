# Security Policy

## Scope

SynapDrive-AI is research software with simulated actuation. The repository does not claim cybersecurity certification or safe deployment on physical systems.

Security-relevant surfaces include evidence signing, evidence-chain verification, input parsing, optional BrainFlow/LSL acquisition, the local WSGI dashboard, and any downstream decoder or hardware integration added by a user.

## Reporting

Do not publish secrets, private keys, participant data, or device credentials in an issue. Report a vulnerability privately through the repository owner's preferred private contact channel when one is available.

A useful report includes the affected version, reproducible steps, expected security property, observed behavior, and whether the issue requires optional dependencies or hardware.

## Key handling

`synapdrive-evidence keygen` can create an Ed25519 private key. Keep private keys outside source control. The repository `.gitignore` cannot protect a key that is explicitly force-added.

## Hardware boundary

The built-in actuator is simulated. Connecting SynapDrive-AI to physical machinery requires an independently engineered hardware safety architecture, emergency-stop path, authorization model, threat model, and validation program appropriate to that system. Do not treat the bundled policy thresholds as hardware safety limits.

# Safety Model (Simulation-First)

## Safety stance
This repo defaults to a conservative policy:
- Unknown or low-confidence intents are **blocked**
- The pipeline always returns a stable response shape (no crashing on drift)
- Telemetry is treated as a contract because UIs/tests depend on it

## SafetyGuard policy (current)
- Confidence threshold gating (blocks below a threshold)
- Suspicious intent keyword blocks (if present)

## Threat model (practical)
- Accidental actuation due to noisy input
- Misrouting due to schema drift
- “Demo inflation” where the README claims behaviors that do not exist

## What we do about it
- Contract tests enforce output shapes and telemetry keys
- CI runs lint + type check + tests + coverage
- Replay artifacts allow reviewers to reproduce behavior without hardware

## Non-goals (explicit)
- Clinical diagnosis
- Medical device claims
- Safety certification for real-world actuation

# Local operation and support boundaries

The 2.0.0 research release is tested locally on Python 3.12/Linux. CI is configured for
3.11–3.13; Windows and remote matrix outcomes remain unverified until those jobs run.
The local demo and bundled EEG evaluation work without network access after dependencies
are installed. BrainFlow, LSL and new source downloads are optional and fail explicitly
when unavailable. No cloud inference service or external account is required.

Archive model/configuration/data identities and the matching source release when reproducing
results. Expired models abstain. Do not extend qualification by editing a timestamp or
passing changed acquisition metadata. Reproducing an old offline experiment is not fresh
independent evidence for a new device/session. Keep keys separate from exported ledgers.

There is no promised long-term service owner, clinical support or indefinite compatibility
commitment. Migration is documented in `MIGRATION_V2.md`. Preserve the original run
capsule/keys/checkpoints when exporting a run; private exports intentionally omit content.

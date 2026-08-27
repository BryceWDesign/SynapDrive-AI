# Evidence, Replay, and Signing

## Two different records

SynapDrive has two related but distinct recording mechanisms.

`--record` stores replay inputs and a compact output summary. Replay is intended to reproduce the software decision path from the stored input intent packet.

`--evidence-out` exports the v1 cycle evidence chain. Each entry includes the previous entry hash and its own SHA-256 digest.

## Create evidence

```text
python -m synapdrive_ai --text "move left" --no-delay --evidence-out run.evidence.jsonl
```

Verify the chain:

```text
synapdrive-evidence verify-chain run.evidence.jsonl
```

## Detached Ed25519 signature

Generate a keypair:

```text
synapdrive-evidence keygen --private evidence-private.pem --public evidence-public.pem
```

Keep the private key out of source control.

Sign an exported evidence ledger:

```text
synapdrive-evidence sign run.evidence.jsonl --private evidence-private.pem --out run.signature.json
```

Verify:

```text
synapdrive-evidence verify-signature run.evidence.jsonl --public evidence-public.pem --signature run.signature.json
```

The signature authenticates the bytes against possession of the private key. It does not validate the truth of sensor measurements or scientific claims.

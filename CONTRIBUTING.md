# Contributing to SynapDrive-AI

SynapDrive-AI is simulation-first research software. Contributions are expected to preserve the repository's claim boundaries and fail-closed behavior.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the local quality surface:

```bash
python -m compileall -q synapdrive_ai core scripts
python -m pytest -q
python -m scripts.run_v1_validation
ruff check .
pyright
```

## Pull request requirements

- Tests cover every behavioral change, including a negative control when a failure mode matters.
- Unknown, malformed, unqualified, or analysis-only inputs fail closed.
- New decoders do not receive authority merely because they produce a class label.
- Synthetic fixtures are labeled as synthetic and are never described as participant performance.
- Hardware acquisition paths do not invent intent when no decoder is configured.
- Documentation states what is executed and what remains unvalidated.
- No private keys, participant data, device credentials, or generated build artifacts are committed.

## Scientific and safety claims

Do not submit claims of clinical validity, medical-device safety, participant generalization, safe physical actuation, or real-world BCI performance unless the corresponding external evidence actually exists and is cited separately from repository tests.

Software tests establish software behavior only.

## Reporting a defect

Include the operating system, Python version, exact command, traceback or logs, expected behavior, actual behavior, and the smallest reproducible input that can be shared safely.

For security-sensitive reports, follow `SECURITY.md` rather than opening a public issue with exploit details.

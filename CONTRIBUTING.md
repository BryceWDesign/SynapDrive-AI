# Contributing to SynapDrive-AI

Thanks for your interest.

## Project stance
SynapDrive-AI is **simulation-first**. We accept contributions that improve:
- reproducibility (install/run/test)
- safety gating behavior
- telemetry/logging consistency
- modular adapters (optional integrations that do not break the core demo)
- documentation accuracy

We do **not** accept medical/clinical claims.

## Development setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
pre-commit install
pytest -q

Pull Request checklist

 Tests pass locally (pytest -q)

 Lint passes (ruff check .)

 Type check passes (pyright)

 README/docs updated if behavior changes

 No new hard dependencies without discussion

Reporting issues

Please include:

OS + Python version

exact command you ran

traceback/logs

expected vs actual behavior


---

## 2) `CODE_OF_CONDUCT.md` (NEW)
```markdown
# Code of Conduct

We are committed to providing a welcoming, professional environment.

## Expected behavior
- Be respectful and constructive
- Assume good intent
- Focus on technical issues, not people
- Keep discussions on-topic

## Unacceptable behavior
- Harassment, insults, or personal attacks
- Discrimination or hate speech
- Doxxing or sharing private information
- Sustained disruption of discussions

## Enforcement
Project maintainers may remove content, lock threads, or restrict participation
when behavior violates this policy.

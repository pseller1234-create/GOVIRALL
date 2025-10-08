# Codex Operating Standard

## Standard Commands
- **Setup**: `./scripts/setup.sh`
- **Install dependencies**: `pip install -r requirements.txt`
- **Run application**: `python main.py`
- **Tests**: `pytest`
- **Lint**: `ruff check .`
- **Format**: `ruff format .`
- **Type check**: `pyright`
- **Security scan**: `pip-audit`

## Style Rules
- Python code follows [PEP 8] defaults enforced via Ruff.
- Type hints are required for all new or modified functions.
- Avoid wildcard imports and unused variables.
- Use f-strings for string formatting.
- Keep modules focused; prefer small, composable functions.

## Git Workflow
- Branch naming: `feature/<slug>`, `bugfix/<slug>`, or `chore/<slug>`.
- Commit messages follow Conventional Commits (e.g., `feat: add scoring worker`).
- Rebase onto latest `main` before raising a PR.
- Every PR must receive at least one human approval; no auto-merge.

## Review Gates
1. `pytest`
2. `ruff check .`
3. `ruff format --check .`
4. `pyright`
5. `pip-audit`
6. Manual QA notes in PR description

All gates must be green before requesting human review.

## Test Data & Redaction Policy
- Synthetic data only; never commit production data or PII.
- Scrub secrets, tokens, and keys from logs and fixtures.
- Replace sensitive strings with `<redacted>` placeholders in examples.

## Prompt & Completion Guidance
- Use concise, technical prompts with explicit inputs/outputs.
- Include environment assumptions and command history where relevant.
- Responses should be deterministic, cite file paths or command output when referencing sources, and omit filler language.
- Never expose or request secrets; rely on environment variables at runtime.

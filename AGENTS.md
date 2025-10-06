# Codex Operating Standard — GOVIRALL

## Standard Commands
- **Install dependencies:** `pip install -r requirements.txt`
- **Run dev server:** `uvicorn main:app --host 0.0.0.0 --port 8000`
- **Lint:** `ruff check .`
- **Format:** `ruff format .`
- **Type check:** `mypy .`
- **Tests:** `pytest`
- **Security scan:** `bandit -r .`

## Style Rules
- Python follows PEP 8 with `ruff` defaults; prefer type hints on new functions.
- Keep FastAPI routes lean; delegate logic to helper functions when they exceed ~40 lines.
- JSON contracts documented in comments must remain synchronized with implementation.

## Commit Conventions
- Use conventional commit prefixes (e.g., `feat:`, `fix:`, `docs:`, `chore:`).
- Reference tickets in the footer if applicable (e.g., `Refs: GOV-123`).

## Branching & Reviews
- Branch naming: `<type>/<short-description>` (e.g., `feat/gamification-docs`).
- Open PRs against `main`.
- Run lint, format, tests, type check, and security scan before requesting review.
- Mention `@codex review` on every PR to trigger automated analysis; human review required before merge.

## Test Data & Redaction
- Do not commit real user data or API keys; use synthetic or anonymized fixtures.
- Remove or redact any PII before logging or storing artifacts.

## Prompt Patterns
- Provide explicit system/user prompts when documenting workflows.
- Constrain completions with JSON schemas or structured bullet lists when possible.

## Completion Constraints
- Avoid speculative dependencies; document any non-determinism introduced by external services.
- Ensure instructions emphasize transparency, reproducibility, and absence of dark patterns in engagement mechanics.
